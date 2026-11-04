#!/usr/bin/env python3
"""Build sample protocol packets for the protocol pages.

Rule (CLAUDE.md): never hand-write values or hex in a page. Every sample packet is
built here, so lengths, checksums, padding and flags are always correct.

Usage:
    python3 tools/packet-builder.py --self-test      # run in CI
    python3 tools/packet-builder.py ospf-hello       # print a sample packet as JSON
"""

import argparse
import ipaddress
import json
import pathlib
import re
import struct
import sys
import zlib


def inet_checksum(data: bytes) -> int:
    """RFC 1071 one's-complement checksum of 16-bit words."""
    if len(data) % 2:
        data += b"\x00"
    total = sum(struct.unpack(f"!{len(data) // 2}H", data))
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def ip4(addr: str) -> bytes:
    return ipaddress.IPv4Address(addr).packed


def ospf_hello(
    *,
    router_id="198.51.100.1",
    area="0.0.0.0",
    mask="255.255.255.0",
    hello=10,
    options=0x02,
    priority=1,
    dead=40,
    dr="192.0.2.2",
    bdr="192.0.2.1",
    neighbors=("198.51.100.2",),
) -> dict:
    """OSPFv2 Hello, RFC 2328 §A.3.1 (header) and §A.3.2 (Hello), AuType 0."""
    body = (
        ip4(mask)
        + struct.pack("!HBBI", hello, options, priority, dead)
        + ip4(dr)
        + ip4(bdr)
        + b"".join(ip4(n) for n in neighbors)
    )
    length = 24 + len(body)
    header = struct.pack("!BBH4s4sHH8s", 2, 1, length, ip4(router_id), ip4(area), 0, 0, bytes(8))
    # Checksum covers the whole packet except the 64-bit Authentication field (§D.4.1)
    csum = inet_checksum(header[:16] + body)
    header = header[:12] + struct.pack("!H", csum) + header[14:]
    pkt = header + body
    opt_bits = [
        # (mask, Wireshark label, Wireshark filter, reference), from IANA "OSPFv2 Options"
        # registry; labels and filters from the Wireshark display filter reference (ospf).
        (0x80, "DN", "ospf.v2.options.dn", "RFC 4576"),
        (0x40, "(O) Opaque", "ospf.v2.options.o", "RFC 5250"),
        (0x20, "(DC) Demand Circuits", "ospf.v2.options.dc", "RFC 1793"),
        (0x10, "(L) LLS Data block", "ospf.v2.options.l", "RFC 5613"),
        (0x08, "(N) NSSA", "ospf.v2.options.n", "RFC 3101"),
        (0x04, "(MC) Multicast", "ospf.v2.options.mc", "RFC 5110"),
        (0x02, "(E) External Routing", "ospf.v2.options.e", "RFC 2328 §A.2"),
        (0x01, "(MT) Multi-Topology Routing", "ospf.v2.options.mt", "RFC 4915"),
    ]
    ws_labels = {
        "version": "Version",
        "type": "Message Type",
        "length": "Packet Length",
        "router_id": "Source OSPF Router",
        "area_id": "Area ID",
        "checksum": "Checksum",
        "autype": "Auth Type",
        "auth": "Auth Data (none)",
        "mask": "Network Mask",
        "hello": "Hello Interval [sec]",
        "options": "Options",
        "priority": "Router Priority",
        "dead": "Router Dead Interval [sec]",
        "dr": "Designated Router",
        "bdr": "Backup Designated Router",
        "neighbor": "Active Neighbor",
    }
    fields = [
        # (id, RFC name, layer, bits, display value, Wireshark filter, RFC section)
        ("version", "Version #", "header", 8, "2", "ospf.version", "RFC 2328 §A.3.1"),
        ("type", "Type", "header", 8, "1 (Hello)", "ospf.msg", "RFC 2328 §A.3.1"),
        ("length", "Packet length", "header", 16, str(length), "ospf.packet_length", "RFC 2328 §A.3.1"),
        ("router_id", "Router ID", "header", 32, router_id, "ospf.srcrouter", "RFC 2328 §A.3.1"),
        ("area_id", "Area ID", "header", 32, area, "ospf.area_id", "RFC 2328 §A.3.1"),
        ("checksum", "Checksum", "header", 16, f"0x{csum:04x}", "ospf.checksum", "RFC 2328 §A.3.1, §D.4.1"),
        ("autype", "AuType", "header", 16, "0 (Null)", "ospf.auth.type", "RFC 2328 §A.3.1, §D.4"),
        (
            "auth",
            "Authentication",
            "header",
            64,
            "00 00 00 00 00 00 00 00",
            "ospf.auth.none",
            "RFC 2328 §D.4",
        ),
        ("mask", "Network Mask", "body", 32, mask, "ospf.hello.network_mask", "RFC 2328 §A.3.2"),
        ("hello", "HelloInterval", "body", 16, f"{hello} s", "ospf.hello.hello_interval", "RFC 2328 §A.3.2"),
        ("options", "Options", "body", 8, f"0x{options:02x}", "ospf.v2.options", "RFC 2328 §A.2"),
        ("priority", "Rtr Pri", "body", 8, str(priority), "ospf.hello.router_priority", "RFC 2328 §A.3.2"),
        (
            "dead",
            "RouterDeadInterval",
            "body",
            32,
            f"{dead} s",
            "ospf.hello.router_dead_interval",
            "RFC 2328 §A.3.2",
        ),
        ("dr", "Designated Router", "body", 32, dr, "ospf.hello.designated_router", "RFC 2328 §A.3.2"),
        (
            "bdr",
            "Backup Designated Router",
            "body",
            32,
            bdr,
            "ospf.hello.backup_designated_router",
            "RFC 2328 §A.3.2",
        ),
    ] + [
        (f"neighbor{i}", "Neighbor", "body", 32, n, "ospf.hello.active_neighbor", "RFC 2328 §A.3.2")
        for i, n in enumerate(neighbors, 1)
    ]
    out, offset = [], 0
    for fid, name, layer, bits, value, ws, ref in fields:
        f = {
            "id": fid,
            "name": name,
            "layer": layer,
            "offset": offset,
            "bits": bits,
            "value": value,
            "hex": pkt[offset // 8 : (offset + bits) // 8].hex(" "),
            "ws": ws,
            "ws_label": ws_labels[fid.rstrip("0123456789")],
            "ref": ref,
        }
        if fid == "options":
            f["flags"] = [
                {"label": n, "mask": m, "set": bool(options & m), "ws": w, "ref": r}
                for m, n, w, r in opt_bits
            ]
        if fid.startswith("neighbor"):
            f["repeat"] = True
        out.append(f)
        offset += bits
    return {
        "id": "ospf-hello",
        "protocol": "OSPFv2",
        "message": "Hello",
        "encapsulation": "IPv4, protocol 89, destination 224.0.0.5 (AllSPFRouters)",
        "ws_root": "Open Shortest Path First",
        "ws_layers": {"header": "OSPF Header", "body": "OSPF Hello Packet"},
        "length": length,
        "checksum": f"0x{csum:04x}",
        "hex": pkt.hex(" "),
        "fields": out,
    }


# ----------------------------------------------------------------- Ethernet
# IEEE 802.3-2022 clause 3, IEEE 802.1Q-2022 clause 9, ISO/IEC 8802-2, IEEE 802 §9.
# Documentation MAC addresses only (RFC 9542 §2.1.4: 00-00-5E-00-53-00 to -FF).
MAC_A, MAC_B = "00:00:5e:00:53:01", "00:00:5e:00:53:02"
MAC_STP = "01:80:c2:00:00:00"  # IEEE 802.1Q Table 8-1, Nearest Customer Bridge group address
MAC_CTRL = "01:80:c2:00:00:01"  # IEEE 802.3 Annex 31B, MAC Control (PAUSE, PFC)
ETH_MIN = 64  # IEEE 802.3 §4.4.2 minFrameSize, FCS included


def mac(addr: str) -> bytes:
    return bytes.fromhex(addr.replace(":", ""))


def fcs32(frame: bytes) -> bytes:
    """IEEE 802.3 §3.2.9 CRC-32 (0x04C11DB7, reflected): zlib.crc32, sent least significant byte first."""
    return struct.pack("<I", zlib.crc32(frame) & 0xFFFFFFFF)


class EthFrame:
    """Accumulates bytes and fields (bit offsets) in the page format of ospf_hello()."""

    def __init__(self):
        self.data, self.fields, self.pos = bytearray(), [], 0

    def add(self, fid, name, layer, raw, value, ws, ws_label, ref, *, bits=None, tree=None, **extra):  # noqa: PLR0917 (one column per field attribute, as in ospf_hello)
        """A field of `bits` bits (default: all of raw); raw is appended once the bits fill bytes."""
        bits = len(raw) * 8 if bits is None else bits
        self.data += raw
        f = {
            "id": fid,
            "name": name,
            "layer": layer,
            "offset": self.pos,
            "bits": bits,
            "value": value,
            "ws": ws,
            "ws_label": ws_label,
            "ref": ref,
        }
        if tree:
            f["tree"] = tree
        f.update(extra)
        self.fields.append(f)
        self.pos += bits
        return f

    def mac_hdr(self, dst, src, tree="eth"):
        for fid, name, addr, wsl in (
            ("dst", "Destination Address", dst, "Destination"),
            ("src", "Source Address", src, "Source"),
        ):
            b0 = mac(addr)[0]
            lg, ig = (b0 >> 1) & 1, b0 & 1
            self.add(
                fid,
                name,
                "header",
                mac(addr),
                addr,
                f"eth.{fid}",
                wsl,
                "IEEE 802.3 §3.2.3, RFC 9542 §2.1",
                tree=tree,
                flag_bits=24,
                flags=[
                    {
                        "label": "LG bit",
                        "mask": 0x020000,
                        "set": bool(lg),
                        "ws": f"eth.{fid}.lg",
                        "ref": "RFC 9542 §2.1.1",
                        "text": "Locally administered address"
                        if lg
                        else "Globally unique address (factory default)",
                    },
                    {
                        "label": "IG bit",
                        "mask": 0x010000,
                        "set": bool(ig),
                        "ws": f"eth.{fid}.ig",
                        "ref": "IEEE 802.3 §3.2.3.1",
                        "text": "Group address (multicast/broadcast)"
                        if ig
                        else "Individual address (unicast)",
                    },
                ],
            )

    def ethertype(self, fid, value, label, *, tree="eth", ws="eth.type", layer="header", name="Type"):
        self.add(
            fid,
            name,
            layer,
            struct.pack("!H", value),
            f"{label} (0x{value:04x})",
            ws,
            "Type",
            "IEEE 802.3 §3.2.6, RFC 9542 §3",
            tree=tree,
        )

    def tag(self, prefix, tpid, pcp, dei, vid, tree, tpid_tree, tpid_ws, tpid_label, ws_ns="vlan"):  # noqa: PLR0917 (TPID and TCI values in wire order)
        """IEEE 802.1Q §9.5 TPID + §9.6 TCI (PCP 3 bits, DEI 1 bit, VID 12 bits).

        Wireshark dissects a C-TAG (0x8100) with "vlan" (named priorities, DEI as text) and an
        S-TAG (0x88A8) with "ieee8021ad" (plain numbers), see epan/dissectors/packet-ieee8021ah.c."""
        self.add(
            f"{prefix}tpid",
            "TPID",
            "tlv",
            struct.pack("!H", tpid),
            f"{tpid_label} (0x{tpid:04x})",
            tpid_ws,
            "Type",
            "IEEE 802.1Q §9.5",
            tree=tpid_tree,
        )
        tci = struct.pack("!H", (pcp << 13) | (dei << 12) | vid)
        pcp_name = {0: "Best Effort (default)", 5: "Voice, < 10ms latency and jitter"}[pcp]

        def mask(shift, width, val):
            bits = "".join(str(val >> (width - 1 - k) & 1) for k in range(width))
            line = "." * (16 - shift - width) + bits + "." * shift
            return " ".join(line[k : k + 4] for k in range(0, 16, 4))

        self.data += tci
        named = ws_ns == "vlan"
        for fid, name, width, shift, val, ws, wsl, shown in (
            (
                "pcp",
                "PCP",
                3,
                13,
                pcp,
                f"{ws_ns}.priority",
                "Priority",
                f"{pcp_name} ({pcp})" if named else str(pcp),
            ),
            (
                "dei",
                "DEI",
                1,
                12,
                dei,
                f"{ws_ns}.dei",
                "DEI",
                ("Eligible" if dei else "Ineligible") if named else str(dei),
            ),
            ("vid", "VID", 12, 0, vid, f"{ws_ns}.id", "ID", str(vid)),
        ):
            f = {
                "id": f"{prefix}{fid}",
                "name": name,
                "layer": "tlv",
                "offset": self.pos,
                "bits": width,
                "value": shown,
                "ws": ws,
                "ws_label": wsl,
                "ref": "IEEE 802.1Q §9.6",
                "tree": tree,
                "ws_bits": mask(shift, width, val),
            }
            self.fields.append(f)
            self.pos += width

    def payload_ipv4(self, src="192.0.2.1", dst="192.0.2.2", tree="ip"):
        icmp = struct.pack("!BBHHH", 8, 0, 0, 1, 1)
        icmp = icmp[:2] + struct.pack("!H", inet_checksum(icmp)) + icmp[4:]
        hdr = struct.pack(
            "!BBHHHBBH4s4s", 0x45, 0, 20 + len(icmp), 0x1C46, 0x4000, 64, 1, 0, ip4(src), ip4(dst)
        )
        hdr = hdr[:10] + struct.pack("!H", inet_checksum(hdr)) + hdr[12:]
        pkt = hdr + icmp
        self.add(
            "ipv4",
            "MAC client data (IPv4)",
            "body",
            pkt,
            f"ICMP Echo request, Total Length {len(pkt)}",
            "ip",
            "Internet Protocol Version 4",
            "IEEE 802.3 §3.2.7, RFC 894",
            tree=tree,
        )

    def finish(self, tree="eth"):
        """Pad to 60 bytes (IEEE 802.3 §3.2.8), then the FCS (§3.2.9): 64 bytes minimum."""
        short = ETH_MIN - 4 - len(self.data)
        if short > 0:
            self.add(
                "pad",
                "Pad",
                "header",
                bytes(short),
                f"{short} bytes of 0x00",
                "eth.padding",
                "Padding",
                "IEEE 802.3 §3.2.8",
                tree=tree,
            )
        crc = fcs32(bytes(self.data))
        self.add(
            "fcs",
            "Frame Check Sequence",
            "header",
            crc,
            f"0x{crc.hex()} [correct]",
            "eth.fcs",
            "Frame check sequence",
            "IEEE 802.3 §3.2.9",
            tree=tree,
        )

    def out(self, sid, message, encapsulation, layers):
        for f in self.fields:
            lo, hi = f["offset"] // 8, -(-(f["offset"] + f["bits"]) // 8)
            f["hex"] = self.data[lo:hi].hex(" ")
        order = (
            "id",
            "name",
            "layer",
            "tree",
            "offset",
            "bits",
            "value",
            "hex",
            "ws",
            "ws_bits",
            "ws_label",
            "ref",
            "flag_bits",
            "flags",
        )
        fields = [{k: f[k] for k in order if k in f} for f in self.fields]
        return {
            "id": sid,
            "protocol": "Ethernet",
            "message": message,
            "encapsulation": encapsulation,
            "ws_layers": layers,
            "length": len(self.data),
            "hex": self.data.hex(" "),
            "fields": fields,
        }


ETH_II = f"Ethernet II, Src: {MAC_A}, Dst: {MAC_B}"
IP_TREE = "Internet Protocol Version 4, Src: 192.0.2.1, Dst: 192.0.2.2"


def eth_ii() -> dict:
    """Ethernet II (RFC 894) carrying an ICMP Echo request: 28 bytes of data, 18 bytes of padding."""
    fr = EthFrame()
    fr.mac_hdr(MAC_B, MAC_A)
    fr.ethertype("type", 0x0800, "IPv4")
    fr.payload_ipv4()
    fr.finish()
    return fr.out(
        "eth-ii",
        "Ethernet II",
        "Physical medium (IEEE 802.3 PHY), EtherType 0x0800",
        {"eth": ETH_II, "ip": IP_TREE},
    )


def eth_phy() -> dict:
    """The same frame as eth-ii as the PHY sends it: preamble and SFD in front (IEEE 802.3 §3.2.1, §3.2.2)."""
    frame = bytes.fromhex(eth_ii()["hex"].replace(" ", ""))
    fr = EthFrame()
    fr.add(
        "preamble",
        "Preamble",
        "encap",
        b"\x55" * 7,
        "7 x 0x55 (10101010 on the wire)",
        "(not captured)",
        "Preamble",
        "IEEE 802.3 §3.2.1",
        tree="phy",
    )
    fr.add(
        "sfd",
        "SFD",
        "encap",
        b"\xd5",
        "0xd5 (10101011 on the wire)",
        "(not captured)",
        "Start Frame Delimiter",
        "IEEE 802.3 §3.2.2",
        tree="phy",
    )
    fr.add(
        "frame",
        "MAC frame (DA to FCS)",
        "header",
        frame,
        f"{len(frame)} bytes, see Ethernet II",
        "eth",
        "MAC frame",
        "IEEE 802.3 §3.1.1",
        tree="phy",
    )
    return fr.out(
        "eth-phy",
        "Preamble + SFD",
        "Physical layer (Reconciliation Sublayer and PHY)",
        {"phy": "Physical layer: removed by the PHY, never seen by Wireshark"},
    )


def _llc(fr, sap, sap_label):
    for fid, name, ws, wsl, sub, sub_ws, sub_label, sub_text in (
        ("dsap", "DSAP", "llc.dsap", "DSAP", 0x01, "llc.dsap.ig", "IG Bit", "Individual"),
        ("ssap", "SSAP", "llc.ssap", "SSAP", 0x01, "llc.ssap.cr", "CR Bit", "Command"),
    ):
        fr.add(
            fid,
            name,
            "tlv",
            bytes([sap]),
            f"{sap_label} (0x{sap:02x})",
            ws,
            wsl,
            "ISO/IEC 8802-2 §5.2",
            tree="llc",
            flags=[
                {
                    "label": sub_label,
                    "mask": sub,
                    "set": False,
                    "ws": sub_ws,
                    "ref": "ISO/IEC 8802-2 §5.2",
                    "text": sub_text,
                }
            ],
        )
    fr.add(
        "ctrl",
        "Control",
        "tlv",
        b"\x03",
        "U, func=UI (0x03)",
        "llc.control",
        "Control field",
        "ISO/IEC 8802-2 §5.4",
        tree="llc",
    )


def _ieee_hdr(fr, dst, length):
    fr.mac_hdr(dst, MAC_A)
    fr.add(
        "len",
        "Length",
        "header",
        struct.pack("!H", length),
        str(length),
        "eth.len",
        "Length",
        "IEEE 802.3 §3.2.6",
        tree="eth",
    )


def eth_llc() -> dict:
    """IEEE 802.3 + LLC carrying an STP Configuration BPDU (IEEE 802.1Q clause 14), root 32769."""
    bridge = struct.pack("!H", 0x8001) + mac(MAC_A)
    bpdu = (
        struct.pack("!HBBB", 0, 0, 0, 0) + bridge + struct.pack("!I", 0) + bridge + struct.pack("!H", 0x8001)
    )
    bpdu += struct.pack("!HHHH", 0, 20 * 256, 2 * 256, 15 * 256)
    fr = EthFrame()
    _ieee_hdr(fr, MAC_STP, 3 + len(bpdu))
    _llc(fr, 0x42, "Spanning Tree BPDU")
    fr.add(
        "bpdu",
        "MAC client data (STP BPDU)",
        "body",
        bpdu,
        f"Configuration BPDU, root 32769/{MAC_A}, {len(bpdu)} bytes",
        "stp",
        "Spanning Tree Protocol",
        "IEEE 802.1Q §14",
        tree="stp",
    )
    fr.finish()
    return fr.out(
        "eth-llc",
        "802.3 + LLC",
        "Physical medium, Length field (no EtherType), DSAP/SSAP 0x42",
        {"eth": "IEEE 802.3 Ethernet", "llc": "Logical-Link Control", "stp": "Spanning Tree Protocol"},
    )


def eth_snap() -> dict:
    """IEEE 802.3 + LLC + SNAP carrying IPv4 (RFC 1042)."""
    fr = EthFrame()
    _ieee_hdr(fr, MAC_B, 3 + 5 + 28)
    _llc(fr, 0xAA, "SNAP")
    fr.add(
        "oui",
        "OUI",
        "tlv",
        b"\x00\x00\x00",
        "00:00:00 (Encapsulated Ethernet)",
        "llc.oui",
        "Organization Code",
        "IEEE 802 §9.3, RFC 1042",
        tree="llc",
    )
    fr.add(
        "pid",
        "Protocol ID",
        "tlv",
        struct.pack("!H", 0x0800),
        "IPv4 (0x0800)",
        "llc.type",
        "Type",
        "IEEE 802 §9.3, RFC 1042",
        tree="llc",
    )
    fr.payload_ipv4()
    fr.finish()
    return fr.out(
        "eth-snap",
        "802.3 + LLC + SNAP",
        "Physical medium, Length field, DSAP/SSAP 0xAA, OUI 00-00-00",
        {"eth": "IEEE 802.3 Ethernet", "llc": "Logical-Link Control", "ip": IP_TREE},
    )


def eth_dot1q() -> dict:
    """IEEE 802.1Q C-TAG: PCP 5, DEI 0, VID 100."""
    fr = EthFrame()
    fr.mac_hdr(MAC_B, MAC_A)
    fr.tag("", 0x8100, 5, 0, 100, "vlan", "eth", "eth.type", "802.1Q Virtual LAN")
    fr.ethertype("type", 0x0800, "IPv4", tree="vlan", ws="vlan.etype")
    fr.payload_ipv4()
    fr.finish()
    return fr.out(
        "eth-dot1q",
        "802.1Q",
        "Physical medium, TPID 0x8100, inner EtherType 0x0800",
        {"eth": ETH_II, "vlan": "802.1Q Virtual LAN, PRI: 5, DEI: 0, ID: 100", "ip": IP_TREE},
    )


def eth_qinq() -> dict:
    """IEEE 802.1Q S-TAG (0x88A8, VID 200) + C-TAG (0x8100, PCP 5, VID 100): Q-in-Q (ex 802.1ad)."""
    fr = EthFrame()
    fr.mac_hdr(MAC_B, MAC_A)
    fr.tag(
        "s",
        0x88A8,
        0,
        0,
        200,
        "stag",
        "eth",
        "eth.type",
        "802.1ad Provider Bridge (Q-in-Q)",
        ws_ns="ieee8021ad",
    )
    fr.tag("c", 0x8100, 5, 0, 100, "ctag", "stag", "ieee8021ah.etype", "802.1Q Virtual LAN")
    fr.ethertype("type", 0x0800, "IPv4", tree="ctag", ws="vlan.etype")
    fr.payload_ipv4()
    fr.finish()
    return fr.out(
        "eth-qinq",
        "Q-in-Q",
        "Physical medium, TPID 0x88A8 then 0x8100",
        {
            "eth": ETH_II,
            "stag": "IEEE 802.1ad, ID: 200",
            "ctag": "802.1Q Virtual LAN, PRI: 5, DEI: 0, ID: 100",
            "ip": IP_TREE,
        },
    )


def _macc_hdr(fr, opcode, label):
    fr.mac_hdr(MAC_CTRL, MAC_A)
    fr.ethertype("type", 0x8808, "MAC Control")
    fr.add(
        "opcode",
        "Opcode",
        "body",
        struct.pack("!H", opcode),
        f"{label} (0x{opcode:04x})",
        "macc.opcode",
        "Opcode",
        "IEEE 802.3 Annex 31A",
        tree="macc",
    )


def eth_pause() -> dict:
    """MAC Control PAUSE (IEEE 802.3 Annex 31B), pause_time 65535 quanta."""
    fr = EthFrame()
    _macc_hdr(fr, 0x0001, "Pause")
    fr.add(
        "quanta",
        "pause_time",
        "body",
        struct.pack("!H", 0xFFFF),
        "65535 quanta (x 512 bit times)",
        "macc.pause_time",
        "pause_time",
        "IEEE 802.3 Annex 31B.2",
        tree="macc",
    )
    fr.finish()
    return fr.out(
        "eth-pause",
        "PAUSE",
        "Physical medium, EtherType 0x8808, to 01-80-C2-00-00-01",
        {"eth": f"Ethernet II, Src: {MAC_A}, Dst: {MAC_CTRL}", "macc": "MAC Control"},
    )


def eth_pfc() -> dict:
    """Priority-based Flow Control (IEEE 802.3 Annex 31D, IEEE 802.1Q clause 36): priority 3 paused."""
    fr = EthFrame()
    _macc_hdr(fr, 0x0101, "Class Based Flow Control [CBFC] Pause")
    vec = 1 << 3
    fr.add(
        "enbv",
        "Priority-enable vector",
        "body",
        struct.pack("!H", vec),
        f"0x{vec:04x}",
        "macc.cbfc.enbv",
        "CBFC Class Enable Vector",
        "IEEE 802.3 Annex 31D",
        tree="macc",
        flags=[
            {
                "label": f"C{p}",
                "mask": 1 << p,
                "set": bool(vec >> p & 1),
                "ws": f"macc.cbfc.enbv.c{p}",
                "ref": "IEEE 802.3 Annex 31D",
                "text": "True" if vec >> p & 1 else "False",
            }
            for p in range(7, -1, -1)
        ],
    )
    for p in range(8):
        q = 0xFFFF if vec >> p & 1 else 0
        fr.add(
            f"time{p}",
            f"Time({p})",
            "body",
            struct.pack("!H", q),
            f"{q} quanta",
            f"macc.cbfc.pause_time.c{p}",
            f"C{p}",
            "IEEE 802.3 Annex 31D",
            tree="macc",
            repeat=True,
        )
    fr.finish()
    return fr.out(
        "eth-pfc",
        "PFC",
        "Physical medium, EtherType 0x8808, opcode 0x0101",
        {"eth": f"Ethernet II, Src: {MAC_A}, Dst: {MAC_CTRL}", "macc": "MAC Control"},
    )


ETH_SAMPLES = {
    "eth-phy": eth_phy,
    "eth-ii": eth_ii,
    "eth-llc": eth_llc,
    "eth-snap": eth_snap,
    "eth-dot1q": eth_dot1q,
    "eth-qinq": eth_qinq,
    "eth-pause": eth_pause,
    "eth-pfc": eth_pfc,
}


SAMPLES = {"ospf-hello": ospf_hello, **ETH_SAMPLES}


def self_test() -> int:
    errors = 0
    # RFC 1071 example: words 0001 f203 f4f5 f6f7 -> checksum 0x220d
    if inet_checksum(bytes.fromhex("0001f203f4f5f6f7")) != 0x220D:
        print("FAIL inet_checksum RFC 1071 example")
        errors += 1
    pkt = bytes.fromhex(ospf_hello()["hex"].replace(" ", ""))
    if len(pkt) != struct.unpack("!H", pkt[2:4])[0]:
        print("FAIL ospf-hello length field")
        errors += 1
    if inet_checksum(pkt[:16] + pkt[24:]) != 0:
        print("FAIL ospf-hello checksum does not verify")
        errors += 1
    # Ethernet: every MAC frame is at least 64 bytes and its FCS verifies (CRC-32 residue,
    # IEEE 802.3 §3.2.9: the CRC over frame + FCS is the constant 0x2144DF1C).
    for name in ETH_SAMPLES:
        raw = bytes.fromhex(SAMPLES[name]()["hex"].replace(" ", ""))
        frame = raw[8:] if name == "eth-phy" else raw
        if len(frame) < ETH_MIN or zlib.crc32(frame) & 0xFFFFFFFF != 0x2144DF1C:
            print(f"FAIL {name} size or FCS")
            errors += 1
    # The field map must tile the packet exactly: contiguous, no gap, no overlap. A field
    # narrower than a byte (802.1Q PCP, DEI, VID) carries the hex of the bytes it sits in.
    for name, build in SAMPLES.items():
        s = build()
        raw = bytes.fromhex(s["hex"].replace(" ", ""))
        pos = 0
        for f in s["fields"]:
            if f["offset"] != pos or f["hex"] != raw[pos // 8 : -(-(pos + f["bits"]) // 8)].hex(" "):
                print(f"FAIL {name} field map at {f['id']}")
                errors += 1
            pos += f["bits"]
        if pos != len(raw) * 8:
            print(f"FAIL {name} field map covers {pos} of {len(raw) * 8} bits")
            errors += 1
    print("self-test OK" if not errors else f"self-test FAILED ({errors})")
    return 1 if errors else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("sample", nargs="?", choices=sorted(SAMPLES))
    p.add_argument("--self-test", action="store_true")
    p.add_argument(
        "--update",
        metavar="HTML",
        help="rewrite the data-packet JSON blocks of a page with the current samples",
    )
    p.add_argument(
        "--embed",
        action="store_true",
        help="print the one-line JSON to paste in a page's <script type=application/json data-packet=...>",
    )
    a = p.parse_args()
    if a.self_test:
        return self_test()
    if a.update:
        return update(a.update)
    if not a.sample:
        p.print_help()
        return 2
    if a.embed:
        print(embed(a.sample))
    else:
        print(json.dumps(SAMPLES[a.sample](), indent=2))
    return 0


PACKET_BLOCK = re.compile(
    r'(<script type="application/json" data-packet="([a-z0-9-]+)">)(.*?)(</script>)', re.S
)


def update(path: str) -> int:
    """Inject the builder's output into a page, so sample values are never hand-written."""
    page = pathlib.Path(path)
    text = page.read_text(encoding="utf-8")
    unknown = [m.group(2) for m in PACKET_BLOCK.finditer(text) if m.group(2) not in SAMPLES]
    if unknown:
        print(f"unknown sample(s) in {path}: {', '.join(unknown)}")
        return 1
    new, n = PACKET_BLOCK.subn(lambda m: m.group(1) + embed(m.group(2)) + m.group(4), text)
    page.write_text(new, encoding="utf-8")
    print(f"{path}: {n} packet block(s) updated")
    return 0


def embed(sample: str) -> str:
    """Canonical one-line JSON embedded in pages; scripts/check_pages.py compares against it."""
    return json.dumps(SAMPLES[sample](), separators=(",", ":"), ensure_ascii=False)


if __name__ == "__main__":
    sys.exit(main())
