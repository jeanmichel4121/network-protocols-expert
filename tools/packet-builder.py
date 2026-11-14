#!/usr/bin/env python3
"""Build sample protocol packets for the protocol pages.

Rule (CLAUDE.md): never hand-write values or hex in a page. Every sample packet is
built here, so lengths, checksums, padding and flags are always correct.

Usage:
    python3 tools/packet-builder.py --self-test      # run in CI
    python3 tools/packet-builder.py ospf-hello       # print a sample packet as JSON
"""

import argparse
import html
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

    def mac_hdr(self, dst, src, tree="eth", *, prefix="", layer="header"):
        for fid, name, addr, wsl in (
            ("dst", "Destination Address", dst, "Destination"),
            ("src", "Source Address", src, "Source"),
        ):
            b0 = mac(addr)[0]
            lg, ig = (b0 >> 1) & 1, b0 & 1
            self.add(
                prefix + fid,
                name,
                layer,
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


# ----------------------------------------------------------------------------- IPv4
# RFC 791 §3.1 (header, options), RFC 2474 §3 and RFC 3168 §5 (DS field), RFC 6864 (ID),
# RFC 2113 (Router Alert), RFC 792 (ICMP Echo), RFC 768 (UDP), RFC 2236 (IGMPv2).
# Documentation values only: RFC 5737 addresses, RFC 6676 group 233.252.0.1, RFC 9542 MACs.
# Tree labels: Wireshark epan/dissectors/packet-ip.c, with the IPv4 preferences "Validate the
# IPv4 checksum if possible" on and "Reassemble fragmented IPv4 datagrams" off (the defaults
# are the opposite: the page says so).
IP_HOST, IP_R1, IP_R2, IP_DST = "192.0.2.10", "198.51.100.1", "203.0.113.1", "198.51.100.20"
IP_GROUP = "233.252.0.1"  # RFC 6676 MCAST-TEST-NET
MAC_HOST, MAC_GW = "00:00:5e:00:53:0a", "00:00:5e:00:53:01"
MAC_GROUP = "01:00:5e:7c:00:01"  # RFC 1112 §6.4: 01-00-5E + the low 23 bits of 233.252.0.1
ICMP_DATA = bytes((0x20 + i) % 256 for i in range(56))
PROTO_NAMES = {1: "ICMP", 2: "IGMP", 6: "TCP", 17: "UDP"}
DSCP_NAMES = {0: ("CS0", "Default"), 46: ("EF", "Expedited Forwarding"), 48: ("CS6", "Class Selector 6")}
ECN_NAMES = {
    0: ("Not-ECT", "Not ECN-Capable Transport"),
    2: ("ECT(0)", "ECN-Capable Transport codepoint '10'"),
    3: ("CE", "Congestion Experienced"),
}
OPT_CLASS = {0: "Control", 2: "Debugging and measurement"}
OPT_NUMBER = {
    0: "End of Option List (EOL)",
    1: "No-Operation (NOP)",
    3: "Loose source route",
    4: "Time stamp",
    7: "Record route",
    20: "Router Alert",
}
OPT_TITLE = {
    0: "End of Options List (EOL)",
    1: "No-Operation (NOP)",
    7: "Record Route",
    68: "Time Stamp",
    131: "Loose Source Route",
    148: "Router Alert",
}
IP_REF = "RFC 791 §3.1"


def wsbits(value: int, width: int, start: int, total: int) -> str:
    """Wireshark bit mask: wsbits(4, 4, 0, 8) == '0100 ....'."""
    s = ["."] * total
    for k, ch in enumerate(format(value, f"0{width}b")):
        s[start + k] = ch
    return " ".join("".join(s[k : k + 4]) for k in range(0, total, 4))


def ipv4_packet(
    src, dst, proto, payload, *, dscp=0, ecn=0, ident=0, df=0, mf=0, offset=0, ttl=64, options=b""
):
    """RFC 791 §3.1 header + payload; options padded with zeros to 32 bits; IHL, Total Length
    and Header Checksum computed."""
    options += bytes(-len(options) % 4)
    ihl = 5 + len(options) // 4
    hdr = struct.pack(
        "!BBHHHBBH4s4s",
        0x40 | ihl,
        dscp << 2 | ecn,
        ihl * 4 + len(payload),
        ident,
        df << 14 | mf << 13 | offset,
        ttl,
        proto,
        0,
        ip4(src),
        ip4(dst),
    )
    hdr += options
    return hdr[:10] + struct.pack("!H", inet_checksum(hdr)) + hdr[12:] + payload


def ipv4_fragments(datagram: bytes, mtu: int) -> list:
    """RFC 791 §3.2: every fragment but the last carries a multiple of 8 data bytes (no option)."""
    ihl = (datagram[0] & 0x0F) * 4
    src, dst = (str(ipaddress.IPv4Address(datagram[k : k + 4])) for k in (12, 16))
    proto, ident, ttl = datagram[9], struct.unpack("!H", datagram[4:6])[0], datagram[8]
    data, room, out = datagram[ihl:], (mtu - 20) // 8 * 8, []
    for pos in range(0, len(data), room):
        chunk = data[pos : pos + room]
        more = int(pos + len(chunk) < len(data))
        out.append(ipv4_packet(src, dst, proto, chunk, ident=ident, mf=more, offset=pos // 8, ttl=ttl))
    return out


def icmp_echo(ident: int, seq: int, data: bytes) -> bytes:
    """RFC 792 Echo request (type 8, code 0)."""
    msg = struct.pack("!BBHHH", 8, 0, 0, ident, seq) + data
    return msg[:2] + struct.pack("!H", inet_checksum(msg)) + msg[4:]


def igmpv2_report(group: str) -> bytes:
    """RFC 2236 §2 Version 2 Membership Report (type 0x16), Max Resp Time 0."""
    msg = struct.pack("!BBH4s", 0x16, 0, 0, ip4(group))
    return msg[:2] + struct.pack("!H", inet_checksum(msg)) + msg[4:]


def udp_datagram(src: str, dst: str, sport: int, dport: int, data: bytes) -> bytes:
    """RFC 768: checksum over the pseudo-header; a computed 0 is sent as 0xFFFF."""
    length = 8 + len(data)
    pseudo = ip4(src) + ip4(dst) + struct.pack("!BBH", 0, 17, length)
    hdr = struct.pack("!HHHH", sport, dport, length, 0)
    csum = inet_checksum(pseudo + hdr + data) or 0xFFFF
    return hdr[:6] + struct.pack("!H", csum) + data


def opt_route(otype: int, addrs: list, ptr: int, slots: int) -> bytes:
    """Record Route (7), Loose (131) or Strict (137) Source Route: type, length, pointer, slots."""
    route = b"".join(ip4(a) for a in addrs) + bytes(4 * (slots - len(addrs)))
    return struct.pack("!BBB", otype, 3 + 4 * slots, ptr) + route


def opt_timestamp_addr(entries: list, slots: int) -> bytes:
    """Internet Timestamp (68) with flag 1: address + timestamp pairs (RFC 791 §3.1)."""
    body = b"".join(ip4(a) + struct.pack("!I", ts) for a, ts in entries) + bytes(8 * (slots - len(entries)))
    return struct.pack("!BBBB", 68, 4 + 8 * slots, 5 + 8 * len(entries), 1) + body


class IPv4Frame(EthFrame):
    """Ethernet II + IPv4 (+ options) + upper layer, in the page format, with Wireshark groups."""

    def __init__(self):
        super().__init__()
        self.groups, self.count = {}, {}

    def group(self, gid, label, ws="", parent=None):
        self.groups[gid] = {
            "label": label,
            **({"ws": ws} if ws else {}),
            **({"parent": parent} if parent else {}),
        }
        return gid

    def nid(self, kind):
        self.count[kind] = self.count.get(kind, 0) + 1
        return f"{kind}{self.count[kind]}"

    def bitfield(self, fid, name, layer, bits, value, ws, ws_label, ref, **extra):  # noqa: PLR0917 (as add)
        """A field inside bytes already appended (raw added by the caller)."""
        return self.add(fid, name, layer, b"", value, ws, ws_label, ref, bits=bits, **extra)

    def eth(self, dst_mac):
        self.mac_hdr(dst_mac, MAC_HOST, prefix="eth", layer="encap")
        self.ethertype("ethtype", 0x0800, "IPv4", layer="encap")

    def ip_header(self, pkt: bytes):
        ver_ihl, tos, total, ident, frag, ttl, proto, csum = struct.unpack("!BBHHHBBH", pkt[:12])
        ihl, dscp, ecn = ver_ihl & 0x0F, tos >> 2, tos & 3
        df, mf, off = frag >> 14 & 1, frag >> 13 & 1, frag & 0x1FFF
        src, dst = (str(ipaddress.IPv4Address(pkt[k : k + 4])) for k in (12, 16))
        t = "ip"
        self.data += pkt[:2]
        self.bitfield(
            "ver",
            "Version",
            "header",
            4,
            "4",
            "ip.version",
            "Version",
            IP_REF,
            tree=t,
            ws_bits=wsbits(4, 4, 0, 8),
        )
        self.bitfield(
            "ihl",
            "IHL",
            "header",
            4,
            str(ihl),
            "ip.hdr_len",
            "Header Length",
            IP_REF,
            tree=t,
            ws_bits=wsbits(ihl, 4, 4, 8),
            ws_value=f"{ihl * 4} bytes ({ihl})",
        )
        short = f"DSCP: {DSCP_NAMES[dscp][0]}, ECN: {ECN_NAMES[ecn][0]}"
        ds = self.group("ds", f"Differentiated Services Field: 0x{tos:02x} ({short})", "ip.dsfield")
        self.bitfield(
            "dscp",
            "DSCP",
            "header",
            6,
            f"{dscp} ({DSCP_NAMES[dscp][0]})",
            "ip.dsfield.dscp",
            "Differentiated Services Codepoint",
            "RFC 2474 §3",
            tree=t,
            ws_group=ds,
            ws_bits=wsbits(dscp, 6, 0, 8),
            ws_value=f"{DSCP_NAMES[dscp][1]} ({dscp})",
        )
        self.bitfield(
            "ecn",
            "ECN",
            "header",
            2,
            f"{ecn} ({ECN_NAMES[ecn][0]})",
            "ip.dsfield.ecn",
            "Explicit Congestion Notification",
            "RFC 3168 §5",
            tree=t,
            ws_group=ds,
            ws_bits=wsbits(ecn, 2, 6, 8),
            ws_value=f"{ECN_NAMES[ecn][1]} ({ecn})",
        )
        self.add(
            "tlen", "Total Length", "header", pkt[2:4], str(total), "ip.len", "Total Length", IP_REF, tree=t
        )
        self.add(
            "id",
            "Identification",
            "header",
            pkt[4:6],
            f"0x{ident:04x}",
            "ip.id",
            "Identification",
            "RFC 791 §3.1, RFC 6864 §4",
            tree=t,
            ws_value=f"0x{ident:04x} ({ident})",
        )
        names = [n for n, b in (("Don't fragment", df), ("More fragments", mf)) if b]
        flags = df << 1 | mf
        fl = self.group(
            "flags",
            f"{wsbits(flags, 3, 0, 8)} = Flags: 0x{flags:x}" + "".join(", " + n for n in names),
            "ip.flags",
        )
        self.data += pkt[6:8]
        for fid, name, label, bit, val in (
            ("rb", "R", "Reserved bit", 0, 0),
            ("df", "DF", "Don't fragment", 1, df),
            ("mf", "MF", "More fragments", 2, mf),
        ):
            self.bitfield(
                fid,
                name,
                "header",
                1,
                str(val),
                f"ip.flags.{fid}",
                label,
                IP_REF,
                tree=t,
                ws_group=fl,
                ws_bits=wsbits(val, 1, bit, 8),
                ws_value="Set" if val else "Not set",
            )
        self.bitfield(
            "foff",
            "Fragment Offset",
            "header",
            13,
            str(off),
            "ip.frag_offset",
            "Fragment Offset",
            "RFC 791 §3.1, §3.2",
            tree=t,
            ws_bits=wsbits(off, 13, 3, 16),
            ws_value=str(off * 8),
        )
        self.add(
            "ttl", "Time to Live", "header", pkt[8:9], str(ttl), "ip.ttl", "Time to Live", IP_REF, tree=t
        )
        self.add(
            "proto",
            "Protocol",
            "header",
            pkt[9:10],
            f"{proto} ({PROTO_NAMES[proto]})",
            "ip.proto",
            "Protocol",
            "RFC 791 §3.1, IANA Protocol Numbers",
            tree=t,
            ws_value=f"{PROTO_NAMES[proto]} ({proto})",
        )
        ok = inet_checksum(pkt[: ihl * 4]) == 0
        self.add(
            "csum",
            "Header Checksum",
            "header",
            pkt[10:12],
            f"0x{csum:04x}",
            "ip.checksum",
            "Header Checksum",
            "RFC 791 §3.1, RFC 1071",
            tree=t,
            ws_value=f"0x{csum:04x} [{'correct' if ok else 'incorrect'}]",
            ws_more=[
                {"label": f"[Header checksum status: {'Good' if ok else 'Bad'}]", "ws": "ip.checksum.status"},
                {"label": f"[Calculated Checksum: 0x{csum:04x}]", "ws": "ip.checksum_calculated"},
            ],
        )
        self.add(
            "src", "Source Address", "header", pkt[12:16], src, "ip.src", "Source Address", IP_REF, tree=t
        )
        self.add(
            "dst",
            "Destination Address",
            "header",
            pkt[16:20],
            dst,
            "ip.dst",
            "Destination Address",
            IP_REF,
            tree=t,
        )
        if ihl > 5:
            self.ip_options(pkt[20 : ihl * 4])
        return pkt[ihl * 4 :]

    def opt_type(self, otype, parent):
        """Option type octet: copied flag (1 bit), class (2 bits), number (5 bits), RFC 791 §3.1."""
        g = self.group(self.nid("gt"), f"Type: {otype}", "ip.opt.type", parent)
        copy, cls, num = otype >> 7, otype >> 5 & 3, otype & 0x1F
        self.data += bytes([otype])
        for kind, name, bits, val, ws, label, shown, start in (
            (
                "optcopy",
                "C",
                1,
                copy,
                "ip.opt.type.copy",
                "Copy on fragmentation",
                "Yes" if copy else "No",
                0,
            ),
            ("optclass", "Class", 2, cls, "ip.opt.type.class", "Class", f"{OPT_CLASS[cls]} ({cls})", 1),
            ("optnum", "Number", 5, num, "ip.opt.type.number", "Number", f"{OPT_NUMBER[num]} ({num})", 3),
        ):
            self.bitfield(
                self.nid(kind),
                name,
                "tlv",
                bits,
                str(val),
                ws,
                label,
                IP_REF,
                tree="ip",
                ws_group=g,
                ws_bits=wsbits(val, bits, start, 8),
                ws_value=shown,
            )

    def ip_options(self, opts: bytes):
        names, k, parts = [], 0, []
        while k < len(opts):
            otype = opts[k]
            parts.append((k, otype))
            if otype in (0, 1):
                names.append(OPT_TITLE[otype])
                k += 1
                if otype == 0:
                    break
                continue
            names.append(OPT_TITLE[otype])
            k += opts[k + 1]
        top = self.group("opts", f"Options: ({len(opts)} bytes), " + ", ".join(names))
        for k, otype in parts:
            if otype in (0, 1):
                g = self.group(self.nid("go"), f"IP Option - {OPT_TITLE[otype]}", parent=top)
                self.opt_type(otype, g)
                if otype == 0 and k + 1 < len(opts):
                    pad = opts[k + 1 :]
                    self.add(
                        "padding",
                        "Padding",
                        "tlv",
                        pad,
                        f"{len(pad)} bytes",
                        "ip.opt.padding",
                        "Padding",
                        IP_REF,
                        tree="ip",
                        ws_group=top,
                        ws_value=pad.hex(),
                    )
                continue
            length = opts[k + 1]
            label = f"IP Option - {OPT_TITLE[otype]} ({length} bytes)"
            if otype == 148:
                label += ": Router shall examine packet (0)"
            g = self.group(self.nid("go"), label, parent=top)
            self.opt_type(otype, g)
            self.add(
                self.nid("optlen"),
                "Length",
                "tlv",
                opts[k + 1 : k + 2],
                str(length),
                "ip.opt.len",
                "Length",
                IP_REF,
                tree="ip",
                ws_group=g,
            )
            body = opts[k + 2 : k + length]
            if otype in (7, 131):
                self.route(otype, body, length, g)
            elif otype == 68:
                self.timestamps(body, length, g)
            elif otype == 148:
                self.add(
                    self.nid("raval"),
                    "Value",
                    "tlv",
                    body,
                    "0",
                    "ip.opt.ra",
                    "Router Alert",
                    "RFC 2113 §2.1",
                    tree="ip",
                    ws_group=g,
                    ws_value="Router shall examine packet (0)",
                )

    def route(self, otype, body, length, g):
        ptr = body[0]
        self.add(
            self.nid("optptr"),
            "Pointer",
            "tlv",
            body[:1],
            str(ptr),
            "ip.opt.ptr",
            "Pointer",
            IP_REF,
            tree="ip",
            ws_group=g,
        )
        for off in range(3, length, 4):
            addr = str(ipaddress.IPv4Address(body[off - 2 : off + 2]))
            nxt = " <- (next)" if off + 1 == ptr else ""
            if otype == 7:
                kind, ws, label = (
                    ("rrrec", "ip.rec_rt", "Recorded Route")
                    if off + 1 < ptr
                    else ("rrempty", "ip.empty_rt", "Empty Route")
                )
            elif off == length - 4:
                kind, ws, label = "srdst", "ip.dst", "Destination Address"
            else:
                kind, ws, label = (
                    ("srrec", "ip.rec_rt", "Recorded Route")
                    if off + 1 < ptr
                    else ("srnext", "ip.src_rt", "Source Route")
                )
            self.add(
                self.nid(kind),
                label,
                "tlv",
                body[off - 2 : off + 2],
                addr,
                ws,
                label,
                IP_REF,
                tree="ip",
                ws_group=g,
                ws_value=addr + nxt,
            )

    def timestamps(self, body, length, g):
        ptr, of = body[0], body[1]
        self.add(
            self.nid("optptr"),
            "Pointer",
            "tlv",
            body[:1],
            str(ptr),
            "ip.opt.ptr",
            "Pointer",
            IP_REF,
            tree="ip",
            ws_group=g,
        )
        self.data += body[1:2]
        self.bitfield(
            self.nid("tsoflw"),
            "Overflow",
            "tlv",
            4,
            str(of >> 4),
            "ip.opt.overflow",
            "Overflow",
            IP_REF,
            tree="ip",
            ws_group=g,
            ws_bits=wsbits(of >> 4, 4, 0, 8),
        )
        self.bitfield(
            self.nid("tsflag"),
            "Flag",
            "tlv",
            4,
            str(of & 0xF),
            "ip.opt.flag",
            "Flag",
            IP_REF,
            tree="ip",
            ws_group=g,
            ws_bits=wsbits(of & 0xF, 4, 4, 8),
            ws_value=f"Time stamp and address (0x{of & 0xF})",
        )
        for off in range(2, length - 2, 8):
            addr = str(ipaddress.IPv4Address(body[off : off + 4]))
            (ts,) = struct.unpack("!I", body[off + 4 : off + 8])
            self.add(
                self.nid("tsaddr"),
                "Address",
                "tlv",
                body[off : off + 4],
                addr,
                "ip.opt.time_stamp_addr",
                "Address",
                IP_REF,
                tree="ip",
                ws_group=g,
                ws_value=addr if addr != "0.0.0.0" else "-",
            )
            self.add(
                self.nid("tsts"),
                "Timestamp",
                "tlv",
                body[off + 4 : off + 8],
                str(ts),
                "ip.opt.time_stamp",
                "Time stamp",
                IP_REF,
                tree="ip",
                ws_group=g,
            )

    def data_field(self, raw, tree, group=None):
        hexs = raw.hex()
        self.add(
            "data",
            "Data",
            "body",
            raw,
            f"{len(raw)} bytes",
            "data.data",
            "Data",
            "RFC 791 §3.1",
            tree=tree,
            rows=2,
            ws_value=hexs[:24] + ("…" if len(hexs) > 24 else ""),
            ws_more=[{"label": f"[Length: {len(raw)}]", "ws": "data.len"}],
            **({"ws_group": group} if group else {}),
        )

    def icmp(self, msg):
        ident, seq = struct.unpack("!HH", msg[4:8])
        t, ok = "icmp", inet_checksum(msg) == 0
        self.add(
            "icmptype",
            "Type",
            "body",
            msg[:1],
            "8",
            "icmp.type",
            "Type",
            "RFC 792",
            tree=t,
            ws_value="8 (Echo (ping) request)",
        )
        self.add("icmpcode", "Code", "body", msg[1:2], "0", "icmp.code", "Code", "RFC 792", tree=t)
        csum = struct.unpack("!H", msg[2:4])[0]
        self.add(
            "icmpcsum",
            "Checksum",
            "body",
            msg[2:4],
            f"0x{csum:04x}",
            "icmp.checksum",
            "Checksum",
            "RFC 792",
            tree=t,
            ws_value=f"0x{csum:04x} [{'correct' if ok else 'incorrect'}]",
            ws_more=[
                {"label": f"[Checksum Status: {'Good' if ok else 'Bad'}]", "ws": "icmp.checksum.status"}
            ],
        )
        swap = lambda v: struct.unpack("<H", struct.pack(">H", v))[0]  # noqa: E731
        self.add(
            "icmpid",
            "Identifier",
            "body",
            msg[4:6],
            str(ident),
            "icmp.ident",
            "Identifier (BE)",
            "RFC 792",
            tree=t,
            ws_value=f"{ident} (0x{ident:04x})",
            ws_more=[
                {"label": f"Identifier (LE): {swap(ident)} (0x{swap(ident):04x})", "ws": "icmp.ident_le"}
            ],
        )
        self.add(
            "icmpseq",
            "Sequence Number",
            "body",
            msg[6:8],
            str(seq),
            "icmp.seq",
            "Sequence Number (BE)",
            "RFC 792",
            tree=t,
            ws_value=f"{seq} (0x{seq:04x})",
            ws_more=[
                {"label": f"Sequence Number (LE): {swap(seq)} (0x{swap(seq):04x})", "ws": "icmp.seq_le"}
            ],
        )
        self.data_field(msg[8:], t, self.group("icmpdata", f"Data ({len(msg) - 8} bytes)"))

    def udp(self, msg, total_len=None):
        sport, dport, length, csum = struct.unpack("!HHHH", msg[:8])
        t = "udp"
        self.add(
            "sport",
            "Source Port",
            "body",
            msg[:2],
            str(sport),
            "udp.srcport",
            "Source Port",
            "RFC 768",
            tree=t,
        )
        self.add(
            "dport",
            "Destination Port",
            "body",
            msg[2:4],
            str(dport),
            "udp.dstport",
            "Destination Port",
            "RFC 768",
            tree=t,
        )
        self.add("ulen", "Length", "body", msg[4:6], str(length), "udp.length", "Length", "RFC 768", tree=t)
        self.add(
            "ucsum",
            "Checksum",
            "body",
            msg[6:8],
            f"0x{csum:04x}",
            "udp.checksum",
            "Checksum",
            "RFC 768",
            tree=t,
            ws_value=f"0x{csum:04x} [unverified]",
            ws_more=[{"label": "[Checksum Status: Unverified]", "ws": "udp.checksum.status"}],
        )
        self.data_field(msg[8:], "data")

    def igmp(self, msg):
        t, ok, csum = "igmp", inet_checksum(msg) == 0, struct.unpack("!H", msg[2:4])[0]
        self.add(
            "igmptype",
            "Type",
            "body",
            msg[:1],
            "0x16",
            "igmp.type",
            "Type",
            "RFC 2236 §2",
            tree=t,
            ws_value="Membership Report (0x16)",
            ws_pre=[{"label": "[IGMP Version: 2]", "ws": "igmp.version"}],
        )
        self.add(
            "igmpmrt",
            "Max Resp Time",
            "body",
            msg[1:2],
            "0",
            "igmp.max_resp",
            "Max Resp Time",
            "RFC 2236 §2",
            tree=t,
            ws_value="0.0 sec (0x00)",
        )
        self.add(
            "igmpcsum",
            "Checksum",
            "body",
            msg[2:4],
            f"0x{csum:04x}",
            "igmp.checksum",
            "Checksum",
            "RFC 2236 §2",
            tree=t,
            ws_value=f"0x{csum:04x} [{'correct' if ok else 'incorrect'}]",
            ws_more=[
                {"label": f"[Checksum Status: {'Good' if ok else 'Bad'}]", "ws": "igmp.checksum.status"}
            ],
        )
        self.add(
            "igmpgroup",
            "Group Address",
            "body",
            msg[4:8],
            IP_GROUP,
            "igmp.maddr",
            "Multicast Address",
            "RFC 2236 §2",
            tree=t,
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
            "rows",
            "value",
            "hex",
            "ws",
            "ws_group",
            "ws_bits",
            "ws_label",
            "ws_value",
            "ws_pre",
            "ws_more",
            "ref",
            "flag_bits",
            "flags",
        )
        return {
            "id": sid,
            "protocol": "IPv4",
            "message": message,
            "encapsulation": encapsulation,
            "ws_layers": layers,
            "ws_groups": self.groups,
            "grid_from": 112,  # bit diagram from the IPv4 header (RFC 791 rows), after 14 bytes of Ethernet
            "length": len(self.data),
            "hex": self.data.hex(" "),
            "fields": [{k: f[k] for k in order if k in f} for f in self.fields],
        }


def ipv4_sample(sid, message, pkt, *, dst_mac=MAC_GW, upper=None):
    """One Ethernet II frame carrying `pkt`; upper(fr, payload) adds the payload's fields."""
    fr = IPv4Frame()
    fr.eth(dst_mac)
    payload = fr.ip_header(pkt)
    src, dst = (str(ipaddress.IPv4Address(pkt[k : k + 4])) for k in (12, 16))
    layers = {
        "eth": f"Ethernet II, Src: {MAC_HOST}, Dst: {dst_mac}",
        "ip": f"Internet Protocol Version 4, Src: {src}, Dst: {dst}",
    }
    upper(fr, payload, layers)
    return fr.out(sid, message, "Ethernet II, EtherType 0x0800", layers)


def _icmp(fr, payload, layers):
    layers["icmp"] = "Internet Control Message Protocol"
    fr.icmp(payload)


def _udp(fr, payload, layers):
    layers["udp"] = "User Datagram Protocol, Src Port: {}, Dst Port: {}".format(
        *struct.unpack("!HH", payload[:4])
    )
    layers["data"] = f"Data ({len(payload) - 8} bytes)"
    fr.udp(payload)


def _data(fr, payload, layers):
    layers["data"] = f"Data ({len(payload)} bytes)"
    fr.data_field(payload, "data")


def _igmp(fr, payload, layers):
    layers["igmp"] = "Internet Group Management Protocol"
    fr.igmp(payload)


def ipv4_big_datagram() -> bytes:
    """A 4000-byte UDP datagram (DF=0) that a 1500-byte MTU splits into three fragments."""
    data = bytes((k * 7) % 256 for k in range(4000 - 20 - 8))
    return ipv4_packet(IP_HOST, IP_DST, 17, udp_datagram(IP_HOST, IP_DST, 49152, 5001, data), ident=0x7A3C)


def ipv4_base() -> dict:
    pkt = ipv4_packet(IP_HOST, IP_DST, 1, icmp_echo(0x0B1E, 1, ICMP_DATA), ident=0x4D2A, df=1)
    return ipv4_sample("ipv4-base", "Atomic (DF=1)", pkt, upper=_icmp)


def ipv4_frag(n: int) -> dict:
    pkt = ipv4_fragments(ipv4_big_datagram(), 1500)[n - 1]
    upper = _udp if n == 1 else _data
    return ipv4_sample(f"ipv4-frag{n}", f"Fragment {n}/3", pkt, upper=upper)


def ipv4_ra() -> dict:
    pkt = ipv4_packet(
        IP_HOST,
        IP_GROUP,
        2,
        igmpv2_report(IP_GROUP),
        dscp=48,
        df=1,
        ttl=1,
        options=struct.pack("!BBH", 148, 4, 0),
    )
    return ipv4_sample("ipv4-ra", "Router Alert", pkt, dst_mac=MAC_GROUP, upper=_igmp)


def ipv4_rr() -> dict:
    """Record Route seen after two routers: 9 slots, 2 filled, pointer 12, then EOOL."""
    opts = opt_route(7, [IP_R1, IP_R2], ptr=12, slots=9) + b"\x00"
    pkt = ipv4_packet(IP_HOST, IP_DST, 1, icmp_echo(0x0B1E, 2, ICMP_DATA), ident=0x4D2B, ttl=62, options=opts)
    return ipv4_sample("ipv4-rr", "Record Route", pkt, upper=_icmp)


def ipv4_ts() -> dict:
    """Timestamp flag 1: four slots, one filled by R1 at 10:00:00.000 UT (36,000,000 ms)."""
    opts = opt_timestamp_addr([(IP_R1, 36_000_000)], slots=4)
    pkt = ipv4_packet(IP_HOST, IP_DST, 1, icmp_echo(0x0B1E, 3, ICMP_DATA), ident=0x4D2C, ttl=63, options=opts)
    return ipv4_sample("ipv4-ts", "Timestamp", pkt, upper=_icmp)


def ipv4_lsrr() -> dict:
    """Loose Source Route as sent: Destination = first hop R1, route = R2 then the real target."""
    opts = b"\x01" + opt_route(131, [IP_R2, IP_DST], ptr=4, slots=2)
    pkt = ipv4_packet(IP_HOST, IP_R1, 1, icmp_echo(0x0B1E, 4, ICMP_DATA), ident=0x4D2D, options=opts)
    return ipv4_sample("ipv4-lsrr", "NOP + LSRR", pkt, upper=_icmp)


def ipv4_voice(ecn: int, ttl: int) -> bytes:
    voice = udp_datagram(IP_HOST, IP_DST, 16384, 16386, bytes(160))
    return ipv4_packet(IP_HOST, IP_DST, 17, voice, dscp=46, ecn=ecn, ident=0x1C46, df=1, ttl=ttl)


def ipv4_ect() -> dict:
    return ipv4_sample("ipv4-ect", "EF + ECT(0)", ipv4_voice(2, 64), upper=_udp)


def ipv4_ce() -> dict:
    return ipv4_sample("ipv4-ce", "EF + CE", ipv4_voice(3, 63), upper=_udp)


IPV4_SAMPLES = {
    "ipv4-base": ipv4_base,
    "ipv4-frag1": lambda: ipv4_frag(1),
    "ipv4-frag2": lambda: ipv4_frag(2),
    "ipv4-frag3": lambda: ipv4_frag(3),
    "ipv4-ra": ipv4_ra,
    "ipv4-rr": ipv4_rr,
    "ipv4-ts": ipv4_ts,
    "ipv4-lsrr": ipv4_lsrr,
    "ipv4-ect": ipv4_ect,
    "ipv4-ce": ipv4_ce,
}

# ----------------------------------------------------------------------------- OSI and TCP/IP models
# One frame per transport: the same bytes read layer by layer. RFC 9293 §3.1 (TCP header, MSS
# option §3.7.1), RFC 9768 (AE flag), RFC 768 (UDP), RFC 1035 §4.1 (DNS message). Tree labels:
# Wireshark packet-tcp.c and packet-dns.c. Documentation values only (RFC 5737, RFC 2606, RFC 9542).
IP_DNS, IP_WEB = "198.51.100.53", "203.0.113.80"
DNS_NAME = "example.com"
TCP_REF, DNS_REF = "RFC 9293 §3.1", "RFC 1035 §4.1.1"
# RFC 1035 has a 3-bit Z field; DNSSEC took two of its bits (RFC 2535 §6.1, now RFC 4035).
DNSSEC_REF = {"AD": "RFC 4035 §3.2.3", "CD": "RFC 4035 §3.2.2"}
TCP_FLAGS = (
    ("cwr", "CWR", "Congestion Window Reduced"),
    ("ece", "ECE", "ECN-Echo"),
    ("urg", "URG", "Urgent"),
    ("ack", "ACK", "Acknowledgment"),
    ("push", "PSH", "Push"),
    ("reset", "RST", "Reset"),
    ("syn", "SYN", "Syn"),
    ("fin", "FIN", "Fin"),
)


def tcp_segment(src, dst, sport, dport, seq, ack, flags, window, options=b"", data=b""):  # noqa: PLR0917 (header fields in wire order)
    """RFC 9293 §3.1: Data Offset and the checksum over the pseudo-header are computed."""
    options += bytes(-len(options) % 4)
    offset = 5 + len(options) // 4
    hdr = struct.pack("!HHIIHHHH", sport, dport, seq, ack, offset << 12 | flags, window, 0, 0) + options
    pseudo = ip4(src) + ip4(dst) + struct.pack("!BBH", 0, 6, len(hdr) + len(data))
    csum = inet_checksum(pseudo + hdr + data)
    return hdr[:16] + struct.pack("!H", csum) + hdr[18:] + data


def dns_query(ident: int, name: str, qtype: int = 1) -> bytes:
    """RFC 1035 §4.1: header with RD set, one question (QCLASS IN), no compression."""
    qname = b"".join(bytes([len(part)]) + part.encode("ascii") for part in name.split(".")) + b"\x00"
    return struct.pack("!HHHHHH", ident, 0x0100, 1, 0, 0, 0) + qname + struct.pack("!HH", qtype, 1)


class LayerFrame(IPv4Frame):
    """A whole frame drawn from its first bit, one colour per layer of the stack."""

    LAYER = {"eth": "encap", "ip": "header", "udp": "tlv", "tcp": "tlv", "dns": "body", "http": "body"}
    # Protocol name, OSI layer number, id of the field that names the next layer (drawn as the
    # layer strip above the bit diagram).
    STACK = {
        "eth": ("Ethernet II", 2, "ethtype"),
        "ip": ("IPv4", 3, "proto"),
        "udp": ("UDP", 4, "dport"),
        "tcp": ("TCP", 4, "tdport"),
        "dns": ("DNS", 7, None),
        "http": ("HTTP", 7, None),
    }

    def udp_header(self, msg):
        sport, dport, length, csum = struct.unpack("!HHHH", msg[:8])
        t = "udp"
        self.add(
            "sport",
            "Source Port",
            "tlv",
            msg[:2],
            str(sport),
            "udp.srcport",
            "Source Port",
            "RFC 768",
            tree=t,
        )
        self.add(
            "dport",
            "Destination Port",
            "tlv",
            msg[2:4],
            str(dport),
            "udp.dstport",
            "Destination Port",
            "RFC 768",
            tree=t,
        )
        self.add("ulen", "Length", "tlv", msg[4:6], str(length), "udp.length", "Length", "RFC 768", tree=t)
        self.add(
            "ucsum",
            "Checksum",
            "tlv",
            msg[6:8],
            f"0x{csum:04x}",
            "udp.checksum",
            "Checksum",
            "RFC 768",
            tree=t,
            ws_value=f"0x{csum:04x} [unverified]",
            ws_more=[{"label": "[Checksum Status: Unverified]", "ws": "udp.checksum.status"}],
        )
        return msg[8:]

    def tcp(self, msg, rel=(0, 0)):
        """rel: the relative sequence and acknowledgment numbers Wireshark prints."""
        sport, dport, seq, ack, off_flags, window, csum, urg = struct.unpack("!HHIIHHHH", msg[:20])
        offset, flags = off_flags >> 12, off_flags & 0x0FFF
        t = "tcp"
        self.add(
            "tsport", "Source Port", "tlv", msg[:2], str(sport), "tcp.srcport", "Source Port", TCP_REF, tree=t
        )
        self.add(
            "tdport",
            "Destination Port",
            "tlv",
            msg[2:4],
            str(dport),
            "tcp.dstport",
            "Destination Port",
            TCP_REF,
            tree=t,
        )
        self.add(
            "tseq",
            "Sequence Number",
            "tlv",
            msg[4:8],
            str(seq),
            "tcp.seq_raw",
            "Sequence Number (raw)",
            TCP_REF,
            tree=t,
            ws_pre=[{"label": f"Sequence Number: {rel[0]}    (relative sequence number)", "ws": "tcp.seq"}],
        )
        self.add(
            "tack",
            "Acknowledgment Number",
            "tlv",
            msg[8:12],
            str(ack),
            "tcp.ack_raw",
            "Acknowledgment number (raw)",
            TCP_REF,
            tree=t,
            ws_pre=[
                {
                    "label": f"Acknowledgment Number: {rel[1]}"
                    + ("    (relative ack number)" if rel[1] else ""),
                    "ws": "tcp.ack",
                }
            ],
        )
        self.data += msg[12:14]
        self.bitfield(
            "toff",
            "Data Offset",
            "tlv",
            4,
            str(offset),
            "tcp.hdr_len",
            "Header Length",
            TCP_REF,
            tree=t,
            ws_bits=wsbits(offset, 4, 0, 8),
            ws_value=f"{offset * 4} bytes ({offset})",
        )
        names = [n for (_, n, _), k in zip(TCP_FLAGS, range(7, -1, -1), strict=True) if flags >> k & 1]
        # Wireshark lists the set flags from the low bit up: (PSH, ACK), (SYN, ACK).
        fl = self.group("tflags", f"Flags: 0x{flags:03x} ({', '.join(reversed(names))})", "tcp.flags")
        self.bitfield(
            "tres",
            "Rsrvd",
            "tlv",
            3,
            str(flags >> 9),
            "tcp.flags.res",
            "Reserved",
            "RFC 9293 §3.1, RFC 9768 §3.1",
            tree=t,
            ws_group=fl,
            ws_bits=wsbits(flags >> 9, 3, 0, 12),
            ws_value="Not set",
        )
        self.bitfield(
            "tae",
            "AE",
            "tlv",
            1,
            str(flags >> 8 & 1),
            "tcp.flags.ae",
            "Accurate ECN",
            "RFC 9768 §3.1",
            tree=t,
            ws_group=fl,
            ws_bits=wsbits(flags >> 8 & 1, 1, 3, 12),
            ws_value="Not set",
        )
        for k, (fid, name, label) in enumerate(TCP_FLAGS):
            val = flags >> (7 - k) & 1
            self.bitfield(
                "tf" + fid,
                name,
                "tlv",
                1,
                str(val),
                f"tcp.flags.{fid}",
                label,
                TCP_REF,
                tree=t,
                ws_group=fl,
                ws_bits=wsbits(val, 1, 4 + k, 12),
                ws_value="Set" if val else "Not set",
            )
        self.add(
            "twin",
            "Window",
            "tlv",
            msg[14:16],
            str(window),
            "tcp.window_size_value",
            "Window",
            TCP_REF,
            tree=t,
        )
        self.add(
            "tcsum",
            "Checksum",
            "tlv",
            msg[16:18],
            f"0x{csum:04x}",
            "tcp.checksum",
            "Checksum",
            TCP_REF,
            tree=t,
            ws_value=f"0x{csum:04x} [unverified]",
            ws_more=[{"label": "[Checksum Status: Unverified]", "ws": "tcp.checksum.status"}],
        )
        self.add(
            "turg",
            "Urgent Pointer",
            "tlv",
            msg[18:20],
            str(urg),
            "tcp.urgent_pointer",
            "Urgent Pointer",
            TCP_REF,
            tree=t,
        )
        if offset == 5:
            return msg[20:]
        kind, length, mss = struct.unpack("!BBH", msg[20:24])
        ref = "RFC 9293 §3.7.1"
        go = self.group("topts", f"Options: ({offset * 4 - 20} bytes), Maximum segment size", "tcp.options")
        gm = self.group("tmss", f"TCP Option - Maximum segment size: {mss} bytes", "tcp.options.mss", go)
        self.add(
            "tokind",
            "Kind",
            "tlv",
            msg[20:21],
            str(kind),
            "tcp.option_kind",
            "Kind",
            ref,
            tree=t,
            ws_group=gm,
            ws_value=f"Maximum Segment Size ({kind})",
        )
        self.add(
            "tolen",
            "Length",
            "tlv",
            msg[21:22],
            str(length),
            "tcp.option_len",
            "Length",
            ref,
            tree=t,
            ws_group=gm,
        )
        self.add(
            "tomss",
            "MSS Value",
            "tlv",
            msg[22:24],
            str(mss),
            "tcp.options.mss_val",
            "MSS Value",
            ref,
            tree=t,
            ws_group=gm,
        )
        return msg[offset * 4 :]

    def http(self, msg):
        """An HTTP/1.1 request (RFC 9112 §2.1): request line, header lines, empty line. Each field
        takes its separator (SP or CRLF) so the map tiles the message. osi: the OSI layer whose
        role the line plays (5 session, 6 presentation, 7 application)."""
        t = "http"
        lines = msg.split(b"\r\n")
        method, uri, version = lines[0].split(b" ")
        g = self.group("hline", lines[0].decode("ascii") + "\\r\\n")
        req = (
            (
                "hmethod",
                "Request Method",
                method + b" ",
                "http.request.method",
                "RFC 9112 §3.1, RFC 9110 §9.3.1",
            ),
            ("huri", "Request URI", uri + b" ", "http.request.uri", "RFC 9112 §3.2"),
            ("hver", "Request Version", version + b"\r\n", "http.request.version", "RFC 9112 §2.3"),
        )
        for fid, name, raw, ws, ref in req:
            self.add(
                fid, name, "body", raw, raw.strip().decode("ascii"), ws, name, ref, tree=t, ws_group=g, osi=7
            )
        # header name: field id, Wireshark filter, OSI role, reference
        known = {
            "Host": ("hhost", "http.host", 7, "RFC 9110 §7.2"),
            "Accept-Encoding": ("haccenc", "http.accept_encoding", 6, "RFC 9110 §12.5.3"),
            "Connection": ("hconn", "http.connection", 5, "RFC 9110 §7.6.1, RFC 9112 §9.3"),
        }
        for line in lines[1:-2]:
            name, value = (x.decode("ascii") for x in line.split(b": ", 1))
            fid, ws, osi, ref = known[name]
            self.add(fid, name, "body", line + b"\r\n", value, ws, name, ref, tree=t, osi=osi)
        self.add("hend", "CRLF", "body", b"\r\n", "\\r\\n", "http", "\\r\\n", "RFC 9112 §2.1", tree=t, osi=7)

    def dns(self, msg):
        ident, flags, qd, an, ns, ar = struct.unpack("!HHHHHH", msg[:12])
        t = "dns"
        self.add(
            "did",
            "ID",
            "body",
            msg[:2],
            f"0x{ident:04x}",
            "dns.id",
            "Transaction ID",
            DNS_REF,
            tree=t,
        )
        fl = self.group("dflags", f"Flags: 0x{flags:04x} Standard query", "dns.flags")
        self.data += msg[2:4]
        # name, width, Wireshark filter, label, what Wireshark prints for the value of this query
        bits = (
            ("QR", 1, "dns.flags.response", "Response", "Message is a query"),
            ("Opcode", 4, "dns.flags.opcode", "Opcode", "Standard query (0)"),
            ("AA", 1, "dns.flags.authoritative", "Authoritative", "Not set"),
            ("TC", 1, "dns.flags.truncated", "Truncated", "Message is not truncated"),
            ("RD", 1, "dns.flags.recdesired", "Recursion desired", "Do query recursively"),
            ("RA", 1, "dns.flags.recavail", "Recursion available", "Not set"),
            ("Z", 1, "dns.flags.z", "Z", "reserved (0)"),
            ("AD", 1, "dns.flags.authenticated", "Answer authenticated", "Not set"),
            ("CD", 1, "dns.flags.checkdisable", "Non-authenticated data", "Unacceptable"),
            ("RCODE", 4, "dns.flags.rcode", "Reply code", "No error (0)"),
        )
        pos = 0
        for name, width, ws, label, text in bits:
            val = flags >> (16 - pos - width) & ((1 << width) - 1)
            self.bitfield(
                "d" + name.lower(),
                name,
                "body",
                width,
                str(val),
                ws,
                label,
                DNSSEC_REF.get(name, DNS_REF),
                tree=t,
                ws_group=fl,
                ws_bits=wsbits(val, width, pos, 16),
                ws_value=text,
            )
            pos += width
        for k, (fid, name, ws, label, val) in enumerate(
            (
                ("dqd", "QDCOUNT", "dns.count.queries", "Questions", qd),
                ("dan", "ANCOUNT", "dns.count.answers", "Answer RRs", an),
                ("dns", "NSCOUNT", "dns.count.auth_rr", "Authority RRs", ns),
                ("dar", "ARCOUNT", "dns.count.add_rr", "Additional RRs", ar),
            )
        ):
            self.add(fid, name, "body", msg[4 + 2 * k : 6 + 2 * k], str(val), ws, label, DNS_REF, tree=t)
        qname, (qtype, qclass) = msg[12:-4], struct.unpack("!HH", msg[-4:])
        ref = "RFC 1035 §4.1.2"
        gq = self.group("dqueries", "Queries")
        g1 = self.group("dquery", f"{DNS_NAME}: type A, class IN", "", gq)
        self.add(
            "dqname",
            "QNAME",
            "body",
            qname,
            DNS_NAME,
            "dns.qry.name",
            "Name",
            ref,
            tree=t,
            ws_group=g1,
            ws_more=[
                {"label": f"[Name Length: {len(DNS_NAME)}]", "ws": "dns.qry.name.len"},
                {"label": f"[Label Count: {DNS_NAME.count('.') + 1}]", "ws": "dns.count.labels"},
            ],
        )
        self.add(
            "dqtype",
            "QTYPE",
            "body",
            msg[-4:-2],
            str(qtype),
            "dns.qry.type",
            "Type",
            ref,
            tree=t,
            ws_group=g1,
            ws_value=f"A ({qtype}) (Host Address)",
        )
        self.add(
            "dqclass",
            "QCLASS",
            "body",
            msg[-2:],
            str(qclass),
            "dns.qry.class",
            "Class",
            ref,
            tree=t,
            ws_group=g1,
            ws_value=f"IN (0x{qclass:04x})",
        )

    def out(self, sid, message, encapsulation, layers):
        d = super().out(sid, message, encapsulation, layers)
        size = {}
        for f, src in zip(d["fields"], self.fields, strict=True):
            f["layer"] = self.LAYER[f["tree"]]
            size[f["tree"]] = size.get(f["tree"], 0) + f["bits"]
            # OSI layer of the field: its protocol's layer, or its own (an HTTP header line that
            # does the work of the session or presentation layer).
            f["osi"] = src.get("osi", self.STACK[f["tree"]][1])
        d["protocol"] = "OSI and TCP/IP models"
        d["grid_from"] = 0
        # One entry per protocol of the frame, in wire order: its size and the field that names
        # the protocol above it. NPE.packet draws them as the layer strip.
        d["stack"] = [
            {
                "key": k,
                "name": self.STACK[k][0],
                "osi": self.STACK[k][1],
                "layer": self.LAYER[k],
                "bytes": bits // 8,
            }
            | ({"next": self.STACK[k][2]} if self.STACK[k][2] else {})
            for k, bits in size.items()
        ]
        return d


def layer_sample(sid, message, pkt, upper):
    fr = LayerFrame()
    fr.eth(MAC_GW)
    payload = fr.ip_header(pkt)
    src, dst = (str(ipaddress.IPv4Address(pkt[k : k + 4])) for k in (12, 16))
    layers = {
        "eth": f"Ethernet II, Src: {MAC_HOST}, Dst: {MAC_GW}",
        "ip": f"Internet Protocol Version 4, Src: {src}, Dst: {dst}",
    }
    upper(fr, payload, layers)
    return fr.out(sid, message, "Ethernet II, IPv4", layers)


def osi_dns() -> dict:
    """A DNS query: Ethernet II, IPv4, UDP and DNS headers in one 71-byte frame."""
    query = dns_query(0x1A2B, DNS_NAME)
    pkt = ipv4_packet(
        IP_HOST, IP_DNS, 17, udp_datagram(IP_HOST, IP_DNS, 53124, 53, query), ident=0x3C4D, df=1
    )

    def upper(fr, payload, layers):
        layers["udp"] = "User Datagram Protocol, Src Port: 53124, Dst Port: 53"
        layers["dns"] = "Domain Name System (query)"
        fr.dns(fr.udp_header(payload))

    return layer_sample("osi-dns", "DNS query (UDP)", pkt, upper)


def osi_syn() -> dict:
    """A TCP SYN with an MSS option: Ethernet II, IPv4 and TCP, no application data yet."""
    seg = tcp_segment(
        IP_HOST, IP_WEB, 49152, 443, 0x2F5A1C00, 0, 0x002, 64240, struct.pack("!BBH", 2, 4, 1460)
    )
    pkt = ipv4_packet(IP_HOST, IP_WEB, 6, seg, ident=0x3C4E, df=1)

    def upper(fr, payload, layers):
        layers["tcp"] = "Transmission Control Protocol, Src Port: 49152, Dst Port: 443, Seq: 0, Len: 0"
        fr.tcp(payload)

    return layer_sample("osi-syn", "TCP SYN", pkt, upper)


HTTP_REQUEST = (
    b"GET / HTTP/1.1\r\nHost: " + DNS_NAME.encode("ascii") + b"\r\n"
    b"Accept-Encoding: gzip\r\nConnection: keep-alive\r\n\r\n"
)


def osi_http() -> dict:
    """An HTTP/1.1 GET on an open TCP connection: the first data segment (PSH, ACK), whose
    payload carries the roles of OSI layers 5 to 7 in its own lines."""
    isn, peer = 0x2F5A1C00, 0x7A1B3C00  # this segment follows the handshake: both numbers are ISN + 1
    seg = tcp_segment(IP_HOST, IP_WEB, 49152, 80, isn + 1, peer + 1, 0x018, 64240, data=HTTP_REQUEST)
    pkt = ipv4_packet(IP_HOST, IP_WEB, 6, seg, ident=0x3C50, df=1)

    def upper(fr, payload, layers):
        layers["tcp"] = (
            "Transmission Control Protocol, Src Port: 49152, Dst Port: 80, "
            f"Seq: 1, Ack: 1, Len: {len(HTTP_REQUEST)}"
        )
        layers["http"] = "Hypertext Transfer Protocol"
        fr.http(fr.tcp(payload, rel=(1, 1)))

    return layer_sample("osi-http", "HTTP GET (TCP)", pkt, upper)


OSI_SAMPLES = {"osi-dns": osi_dns, "osi-http": osi_http, "osi-syn": osi_syn}


# ----------------------------------------------------------------------------- ARP
# RFC 826 (packet format: ar$hrd, ar$pro, ar$hln, ar$pln, ar$op, ar$sha, ar$spa, ar$tha, ar$tpa),
# RFC 5227 §1.1 (ARP Probe: sender IP 0.0.0.0; ARP Announcement: sender IP = target IP, request),
# RFC 5944 §4.6 (gratuitous ARP in reply form: target hardware address = sender hardware address),
# IANA ARP parameters (hardware type 1, opcodes 1 and 2), EtherType 0x0806. IEEE 802.3 §3.2.8:
# the 28-byte ARP packet is padded to 46 bytes of MAC client data (42 behind a VLAN tag).
# Tree labels: Wireshark epan/dissectors/packet-arp.c. Documentation values only (RFC 5737, RFC 9542).
MAC_BCAST, MAC_ZERO = "ff:ff:ff:ff:ff:ff", "00:00:00:00:00:00"
IP_GW, IP_SRV, MAC_SRV = "192.0.2.1", "192.0.2.20", "00:00:5e:00:53:14"
IP_NEW, MAC_NEW = "192.0.2.30", "00:00:5e:00:53:1e"
IP_VIP, MAC_LB = "192.0.2.100", "00:00:5e:00:53:65"
ARP_OPS = {1: "request", 2: "reply"}  # IANA ARP parameters, Operation Codes
ARP_REF = "RFC 826 (Definitions)"


class ArpFrame(EthFrame):
    """Ethernet II (optionally 802.1Q tagged) + ARP for IPv4 over Ethernet + padding + FCS."""

    def eth(self, dst, src, vid=None):
        self.mac_hdr(dst, src, prefix="eth", layer="encap")
        if vid is None:
            self.ethertype("ethtype", 0x0806, "ARP", layer="encap")
        else:
            self.tag("", 0x8100, 0, 0, vid, "vlan", "eth", "eth.type", "802.1Q Virtual LAN")
            self.ethertype("ethtype", 0x0806, "ARP", tree="vlan", ws="vlan.etype", layer="encap")

    def arp(self, op, sha, spa, tha, tpa):
        """The nine fields of RFC 826, hardware type 1 (Ethernet), protocol type 0x0800 (IPv4).
        Returns Wireshark's name for the packet (packet-arp.c: gratuitous, probe, announcement)."""
        gratuitous = spa == tpa
        announcement = gratuitous and op == 1 and tha == MAC_ZERO
        probe = not gratuitous and op == 1 and spa == "0.0.0.0"
        marks = [
            {"label": f"[{label}: True]", "ws": ws}
            for on, label, ws in (
                (gratuitous, "Is gratuitous", "arp.isgratuitous"),
                (probe, "Is probe", "arp.isprobe"),
                (announcement, "Is announcement", "arp.isannouncement"),
            )
            if on
        ]
        t = "arp"
        self.add(
            "hrd",
            "Hardware Type",
            "header",
            struct.pack("!H", 1),
            "Ethernet (1)",
            "arp.hw.type",
            "Hardware type",
            ARP_REF,
            tree=t,
        )
        self.add(
            "pro",
            "Protocol Type",
            "header",
            struct.pack("!H", 0x0800),
            "IPv4 (0x0800)",
            "arp.proto.type",
            "Protocol type",
            ARP_REF,
            tree=t,
        )
        self.add("hln", "HLEN", "header", bytes([6]), "6", "arp.hw.size", "Hardware size", ARP_REF, tree=t)
        self.add("pln", "PLEN", "header", bytes([4]), "4", "arp.proto.size", "Protocol size", ARP_REF, tree=t)
        self.add(
            "op",
            "Operation",
            "header",
            struct.pack("!H", op),
            f"{ARP_OPS[op]} ({op})",
            "arp.opcode",
            "Opcode",
            "RFC 826 (Definitions), IANA ARP parameters",
            tree=t,
            **({"ws_more": marks} if marks else {}),
        )
        self.add(
            "sha",
            "Sender Hardware Address",
            "body",
            mac(sha),
            sha,
            "arp.src.hw_mac",
            "Sender MAC address",
            ARP_REF,
            tree=t,
        )
        self.add(
            "spa",
            "Sender Protocol Address",
            "body",
            ip4(spa),
            spa,
            "arp.src.proto_ipv4",
            "Sender IP address",
            ARP_REF,
            tree=t,
        )
        self.add(
            "tha",
            "Target Hardware Address",
            "body",
            mac(tha),
            tha,
            "arp.dst.hw_mac",
            "Target MAC address",
            ARP_REF,
            tree=t,
        )
        self.add(
            "tpa",
            "Target Protocol Address",
            "body",
            ip4(tpa),
            tpa,
            "arp.dst.proto_ipv4",
            "Target IP address",
            ARP_REF,
            tree=t,
        )
        if announcement:
            return "ARP Announcement"
        if probe:
            return "ARP Probe"
        return f"{ARP_OPS[op]}/gratuitous ARP" if gratuitous else ARP_OPS[op]

    def finish(self, tree="eth"):
        super().finish(tree)
        for f in self.fields:
            if f["id"] in {"pad", "fcs"}:
                f["layer"] = "encap"

    def out(self, sid, message, encapsulation, layers):
        d = super().out(sid, message, encapsulation, layers)
        for f, src in zip(d["fields"], self.fields, strict=True):
            if "ws_more" in src:
                f["ws_more"] = src["ws_more"]
        d["protocol"] = "ARP"
        # The bit diagram starts at the ARP packet (28 bytes, seven 32-bit rows); a tagged frame
        # is drawn from its first bit, so the tag shows in the diagram too.
        d["grid_from"] = 0 if "vlan" in layers else 112
        return d


def arp_sample(sid, message, encapsulation, dst, src, op, spa, tha, tpa, *, vid=None):  # noqa: PLR0917 (ARP fields in wire order)
    fr = ArpFrame()
    fr.eth(dst, src, vid)
    kind = fr.arp(op, src, spa, tha, tpa)
    fr.finish()
    layers = {"eth": f"Ethernet II, Src: {src}, Dst: {dst}"}
    if vid is not None:
        layers["vlan"] = f"802.1Q Virtual LAN, PRI: 0, DEI: 0, ID: {vid}"
    layers["arp"] = f"Address Resolution Protocol ({kind})"
    return fr.out(sid, message, encapsulation, layers)


def arp_request() -> dict:
    """PC-A (192.0.2.10) asks in broadcast who has 192.0.2.20: target hardware address all zero."""
    return arp_sample(
        "arp-request",
        "ARP Request",
        "Ethernet II, EtherType 0x0806, broadcast",
        MAC_BCAST,
        MAC_HOST,
        1,
        IP_HOST,
        MAC_ZERO,
        IP_SRV,
    )


def arp_reply() -> dict:
    """SRV-B (192.0.2.20) answers PC-A in unicast: the request's sender becomes the target."""
    return arp_sample(
        "arp-reply",
        "ARP Reply",
        "Ethernet II, EtherType 0x0806, unicast",
        MAC_HOST,
        MAC_SRV,
        2,
        IP_SRV,
        MAC_HOST,
        IP_HOST,
    )


def arp_probe() -> dict:
    """RFC 5227 §2.1.1: PC-C probes 192.0.2.30 before using it, sender IP address 0.0.0.0."""
    return arp_sample(
        "arp-probe",
        "ARP Probe",
        "Ethernet II, EtherType 0x0806, broadcast",
        MAC_BCAST,
        MAC_NEW,
        1,
        "0.0.0.0",
        MAC_ZERO,
        IP_NEW,
    )


def arp_announce() -> dict:
    """RFC 5227 §2.3: PC-C announces 192.0.2.30 (gratuitous ARP in request form)."""
    return arp_sample(
        "arp-announce",
        "ARP Announcement",
        "Ethernet II, EtherType 0x0806, broadcast",
        MAC_BCAST,
        MAC_NEW,
        1,
        IP_NEW,
        MAC_ZERO,
        IP_NEW,
    )


def arp_garp_reply() -> dict:
    """Gratuitous ARP in reply form (RFC 5944 §4.6): LB-01 takes over the virtual address 192.0.2.100."""
    return arp_sample(
        "arp-garp-reply",
        "Gratuitous ARP (Reply)",
        "Ethernet II, EtherType 0x0806, broadcast",
        MAC_BCAST,
        MAC_LB,
        2,
        IP_VIP,
        MAC_LB,
        IP_VIP,
    )


def arp_dot1q() -> dict:
    """An ARP Request for the gateway 192.0.2.1 on a trunk: 802.1Q tag, VID 100, 14 bytes of padding."""
    return arp_sample(
        "arp-dot1q",
        "ARP Request (802.1Q)",
        "Ethernet II, TPID 0x8100, inner EtherType 0x0806, broadcast",
        MAC_BCAST,
        MAC_HOST,
        1,
        IP_HOST,
        MAC_ZERO,
        IP_GW,
        vid=100,
    )


ARP_SAMPLES = {
    "arp-request": arp_request,
    "arp-reply": arp_reply,
    "arp-probe": arp_probe,
    "arp-announce": arp_announce,
    "arp-garp-reply": arp_garp_reply,
    "arp-dot1q": arp_dot1q,
}


def arp_self_test() -> int:
    """Every ARP frame is 64 bytes with a valid FCS; the ARP packet is 28 bytes of hardware type 1,
    protocol type 0x0800, lengths 6 and 4; the sender hardware address is the frame's source; the
    probe has a zero sender IP address; announcement and gratuitous reply have sender = target IP."""
    errors = 0
    for name, build in ARP_SAMPLES.items():
        raw = bytes.fromhex(build()["hex"].replace(" ", ""))
        tagged = raw[12:14] == b"\x81\x00"
        a = raw[18:46] if tagged else raw[14:42]
        hrd, pro, hln, pln, op = struct.unpack("!HHBBH", a[:8])
        ok = len(raw) == ETH_MIN and zlib.crc32(raw) & 0xFFFFFFFF == 0x2144DF1C
        ok = (
            ok
            and raw[16 if tagged else 12 :][:2] == b"\x08\x06"
            and (hrd, pro, hln, pln) == (1, 0x0800, 6, 4)
        )
        ok = ok and a[8:14] == raw[6:12] and not any(raw[(46 if tagged else 42) : -4])
        ok = ok and (raw[:6] == b"\xff" * 6 or (op == 2 and a[18:24] == raw[:6]))
        if name == "arp-probe":
            ok = ok and a[14:18] == bytes(4) and op == 1
        if name in {"arp-announce", "arp-garp-reply"}:
            ok = ok and a[14:18] == a[24:28]
        if not ok:
            print(f"FAIL {name} ARP frame")
            errors += 1
    return errors


# ----------------------------------------------------------------------------- ICMP (IPv4)
# RFC 792 (formats), RFC 1191 §4 (Next-Hop MTU), RFC 4884 §4 and §7 (length attribute, extension
# structure), RFC 4950 §2 (MPLS Label Stack object). Tree labels: Wireshark packet-icmp.c.
# Every frame is seen on host A's link: A 192.0.2.10 behind R1 192.0.2.1; R1 to R2 203.0.113.2;
# B 198.51.100.20 behind R2; R3 192.0.2.2 is a second router on A's LAN, towards 203.0.113.200.
# Documentation values only (RFC 5737, RFC 9542).
ICMP_R1, ICMP_R2, ICMP_R3, ICMP_SRV = "192.0.2.1", "203.0.113.2", "192.0.2.2", "203.0.113.200"
MAC_R3 = "00:00:5e:00:53:03"
ICMP_TYPES = {
    0: "Echo (ping) reply",
    3: "Destination unreachable",
    5: "Redirect",
    8: "Echo (ping) request",
    11: "Time-to-live exceeded",
    13: "Timestamp request",
}
ICMP_CODES = {
    (3, 3): "Port unreachable",
    (3, 4): "Fragmentation needed",
    (5, 1): "Redirect for host",
    (11, 0): "Time to live exceeded in transit",
}
ICMP_RESP_MS = "0.412"  # capture metadata of the Echo pair: frames 1 and 2, 0.412 ms apart


def icmp_message(mtype: int, code: int, rest: bytes, body: bytes) -> bytes:
    """RFC 792: type, code, checksum over the whole message, 4 bytes that depend on the type, body."""
    msg = struct.pack("!BBH", mtype, code, 0) + rest + body
    return msg[:2] + struct.pack("!H", inet_checksum(msg)) + msg[4:]


def icmp_ext_mpls(label: int, exp: int, s: int, ttl: int) -> bytes:
    """RFC 4884 §7 extension header (version 2) + RFC 4950 §2 MPLS Label Stack object (class 1,
    C-Type 1) holding one label stack entry; the checksum covers the whole structure."""
    obj = struct.pack("!HBBI", 8, 1, 1, label << 12 | exp << 9 | s << 8 | ttl)
    ext = struct.pack("!HH", 2 << 12, 0) + obj
    return ext[:2] + struct.pack("!H", inet_checksum(ext)) + ext[4:]


class ICMPFrame(IPv4Frame):
    """Ethernet II + IPv4 (grey, in the tree and the hex dump) + one ICMP message drawn from its
    first bit: header in blue, data or quoted datagram in teal, extension structure in purple."""

    def encap(self, src_mac, dst_mac, pkt):
        self.mac_hdr(dst_mac, src_mac, prefix="eth", layer="encap")
        self.ethertype("ethtype", 0x0800, "IPv4", layer="encap")
        return self.ip_fields(pkt, "encap", "", "ip", None)

    def ip_fields(self, pkt, layer, prefix, tree, parent):
        """The IPv4 header of pkt, dissected as on the IPv4 page, with its own ids and groups."""
        tmp = IPv4Frame()
        rest = tmp.ip_header(pkt)
        base = self.pos
        for gid, g in tmp.groups.items():
            self.groups[prefix + gid] = {**g, **({"parent": parent} if parent else {})}
        for src in tmp.fields:
            f = dict(src, id=prefix + src["id"], layer=layer, tree=tree, offset=base + src["offset"])
            if "ws_group" in f:
                f["ws_group"] = prefix + f["ws_group"]
            elif parent:
                f["ws_group"] = parent
            self.fields.append(f)
        self.data += tmp.data
        self.pos += tmp.pos
        return rest

    def head(self, msg):
        """Type, Code and Checksum, common to every ICMP message (RFC 792)."""
        mtype, code, csum = struct.unpack("!BBH", msg[:4])
        t, ok = "icmp", inet_checksum(msg) == 0
        self.add(
            "icmptype",
            "Type",
            "header",
            msg[:1],
            str(mtype),
            "icmp.type",
            "Type",
            "RFC 792",
            tree=t,
            ws_value=f"{mtype} ({ICMP_TYPES[mtype]})",
        )
        name = ICMP_CODES.get((mtype, code))
        self.add(
            "icmpcode",
            "Code",
            "header",
            msg[1:2],
            str(code),
            "icmp.code",
            "Code",
            "RFC 792",
            tree=t,
            **({"ws_value": f"{code} ({name})"} if name else {}),
        )
        self.add(
            "icmpcsum",
            "Checksum",
            "header",
            msg[2:4],
            f"0x{csum:04x}",
            "icmp.checksum",
            "Checksum",
            "RFC 792, RFC 1071",
            tree=t,
            ws_value=f"0x{csum:04x} [{'correct' if ok else 'incorrect'}]",
            ws_more=[
                {"label": f"[Checksum Status: {'Good' if ok else 'Bad'}]", "ws": "icmp.checksum.status"}
            ],
        )

    def ident_seq(self, msg, more, layer="header", prefix="", group=None):
        ident, seq = struct.unpack("!HH", msg[4:8])
        swap = lambda v: struct.unpack("<H", struct.pack(">H", v))[0]  # noqa: E731
        g = {"ws_group": group} if group else {}
        self.add(
            prefix + "icmpid",
            "Identifier",
            layer,
            msg[4:6],
            f"0x{ident:04x}",
            "icmp.ident",
            "Identifier (BE)",
            "RFC 792",
            tree="icmp",
            ws_value=f"{ident} (0x{ident:04x})",
            ws_more=[
                {"label": f"Identifier (LE): {swap(ident)} (0x{swap(ident):04x})", "ws": "icmp.ident_le"}
            ],
            **g,
        )
        self.add(
            prefix + "icmpseq",
            "Sequence Number",
            layer,
            msg[6:8],
            str(seq),
            "icmp.seq",
            "Sequence Number (BE)",
            "RFC 792",
            tree="icmp",
            ws_value=f"{seq} (0x{seq:04x})",
            ws_more=[
                {"label": f"Sequence Number (LE): {swap(seq)} (0x{swap(seq):04x})", "ws": "icmp.seq_le"},
                *more,
            ],
            **g,
        )

    def unused(self, raw, fid="icmpunused"):
        self.add(
            fid,
            "unused",
            "header",
            raw,
            "0",
            "icmp.unused",
            "Unused",
            "RFC 792",
            tree="icmp",
            ws_value=raw.hex(),
        )

    def echo(self, msg, more):
        self.head(msg)
        self.ident_seq(msg, more)
        self.data_field(msg[8:], "icmp", self.group("icmpdata", f"Data ({len(msg) - 8} bytes)"))
        self.fields[-1]["ref"] = "RFC 792"

    def timestamp(self, msg):
        self.head(msg)
        self.ident_seq(msg, [])
        for k, (fid, name, ws) in enumerate(
            (
                ("icmpots", "Originate Timestamp", "icmp.originate_timestamp"),
                ("icmprts", "Receive Timestamp", "icmp.receive_timestamp"),
                ("icmptts", "Transmit Timestamp", "icmp.transmit_timestamp"),
            )
        ):
            raw = msg[8 + 4 * k : 12 + 4 * k]
            ms = struct.unpack("!I", raw)[0]
            h, m, s = ms // 3_600_000, ms // 60_000 % 60, ms // 1000 % 60
            parts = [
                f"{v} {u}{'' if v == 1 else 's'}" for v, u in ((h, "hour"), (m, "minute"), (s, "second")) if v
            ]
            shown = ", ".join(parts) or "0 seconds"
            self.add(
                fid,
                name,
                "body",
                raw,
                str(ms),
                ws,
                name,
                "RFC 792",
                tree="icmp",
                ws_value=f"{ms} ({shown} after midnight UTC)",
            )

    def quoted(self, orig: bytes, l4: str):
        """The quoted datagram of an error message: its IPv4 header, then what follows of it."""
        src, dst = (str(ipaddress.IPv4Address(orig[k : k + 4])) for k in (12, 16))
        qip = self.group("qip", f"Internet Protocol Version 4, Src: {src}, Dst: {dst}")
        rest = self.ip_fields(orig, "body", "q", "icmp", qip)
        t = "icmp"
        if l4 == "udp":
            sport, dport, length, csum = struct.unpack("!HHHH", rest[:8])
            g = self.group("qudp", f"User Datagram Protocol, Src Port: {sport}, Dst Port: {dport}")
            for fid, name, raw, val, ws in (
                ("qsport", "Source Port", rest[:2], str(sport), "udp.srcport"),
                ("qdport", "Destination Port", rest[2:4], str(dport), "udp.dstport"),
                ("qulen", "Length", rest[4:6], str(length), "udp.length"),
            ):
                self.add(fid, name, "body", raw, val, ws, name, "RFC 768", tree=t, ws_group=g)
            self.add(
                "qucsum",
                "Checksum",
                "body",
                rest[6:8],
                f"0x{csum:04x}",
                "udp.checksum",
                "Checksum",
                "RFC 768",
                tree=t,
                ws_group=g,
                ws_value=f"0x{csum:04x} [unverified]",
                ws_more=[{"label": "[Checksum Status: Unverified]", "ws": "udp.checksum.status"}],
            )
            if len(rest) > 8:
                self.data_field(rest[8:], t, self.group("qdata", f"Data ({len(rest) - 8} bytes)"))
                self.fields[-1].update(id="qdata", ref="RFC 1812 §4.3.2.3")
        elif l4 == "tcp":
            sport, dport, seq = struct.unpack("!HHI", rest[:8])
            g = self.group("qtcp", f"Transmission Control Protocol, Src Port: {sport}, Dst Port: {dport}")
            self.add(
                "qtsport",
                "Source Port",
                "body",
                rest[:2],
                str(sport),
                "tcp.srcport",
                "Source Port",
                TCP_REF,
                tree=t,
                ws_group=g,
            )
            self.add(
                "qtdport",
                "Destination Port",
                "body",
                rest[2:4],
                str(dport),
                "tcp.dstport",
                "Destination Port",
                TCP_REF,
                tree=t,
                ws_group=g,
            )
            self.add(
                "qtseq",
                "Sequence Number",
                "body",
                rest[4:8],
                str(seq),
                "tcp.seq_raw",
                "Sequence Number (raw)",
                TCP_REF,
                tree=t,
                ws_group=g,
            )
        else:  # the first 8 bytes of an ICMP Echo
            mtype, code, csum = struct.unpack("!BBH", rest[:4])
            g = self.group("qicmp", "Internet Control Message Protocol")
            self.add(
                "qicmptype",
                "Type",
                "body",
                rest[:1],
                str(mtype),
                "icmp.type",
                "Type",
                "RFC 792",
                tree=t,
                ws_group=g,
                ws_value=f"{mtype} ({ICMP_TYPES[mtype]})",
            )
            self.add(
                "qicmpcode",
                "Code",
                "body",
                rest[1:2],
                str(code),
                "icmp.code",
                "Code",
                "RFC 792",
                tree=t,
                ws_group=g,
            )
            self.add(
                "qicmpcsum",
                "Checksum",
                "body",
                rest[2:4],
                f"0x{csum:04x}",
                "icmp.checksum",
                "Checksum",
                "RFC 792",
                tree=t,
                ws_group=g,
                ws_value=f"0x{csum:04x} [unverified] [in ICMP error packet]",
                ws_more=[{"label": "[Checksum Status: Unverified]", "ws": "icmp.checksum.status"}],
            )
            self.ident_seq(rest, [], "body", "q", g)

    def extension(self, ext: bytes):
        """RFC 4884 §7 header and one RFC 4950 MPLS Label Stack object with one entry."""
        t = "icmp"
        word, csum = struct.unpack("!HH", ext[:4])
        length, cls, ctype, entry = struct.unpack("!HBBI", ext[4:12])
        label, exp, s, ttl = entry >> 12, entry >> 9 & 7, entry >> 8 & 1, entry & 0xFF
        ok = inet_checksum(ext) == 0
        top = self.group("ext", "ICMP Multi-Part Extensions", "icmp.ext")
        self.data += ext[:2]
        self.bitfield(
            "extver",
            "Version",
            "tlv",
            4,
            str(word >> 12),
            "icmp.ext.version",
            "Version",
            "RFC 4884 §7",
            tree=t,
            ws_group=top,
        )
        self.bitfield(
            "extres",
            "Reserved",
            "tlv",
            12,
            "0",
            "icmp.ext.res",
            "Reserved",
            "RFC 4884 §7",
            tree=t,
            ws_group=top,
            ws_bits=wsbits(word & 0xFFF, 12, 4, 16),
            ws_value=f"0x{word & 0xFFF:03x}",
        )
        self.add(
            "extcsum",
            "Checksum",
            "tlv",
            ext[2:4],
            f"0x{csum:04x}",
            "icmp.ext.checksum",
            "Checksum",
            "RFC 4884 §7",
            tree=t,
            ws_group=top,
            ws_value=f"0x{csum:04x} [{'correct' if ok else 'incorrect'}]",
            ws_more=[
                {"label": f"[Checksum Status: {'Good' if ok else 'Bad'}]", "ws": "icmp.ext.checksum.status"}
            ],
        )
        obj = self.group("extobj", "MPLS Stack Entry", parent=top)
        self.add(
            "extlen",
            "Length",
            "tlv",
            ext[4:6],
            str(length),
            "icmp.ext.length",
            "Length",
            "RFC 4884 §8",
            tree=t,
            ws_group=obj,
        )
        self.add(
            "extclass",
            "Class-Num",
            "tlv",
            ext[6:7],
            str(cls),
            "icmp.ext.class",
            "Class",
            "RFC 4950 §2",
            tree=t,
            ws_group=obj,
            ws_value=f"MPLS Label Stack Class ({cls})",
        )
        self.add(
            "extctype",
            "C-Type",
            "tlv",
            ext[7:8],
            str(ctype),
            "icmp.ext.ctype",
            "C-Type",
            "RFC 4950 §2",
            tree=t,
            ws_group=obj,
        )
        lse = self.group("extlse", f"Label: {label}, Exp: {exp}, S: {s}, TTL: {ttl}", parent=obj)
        self.data += ext[8:11]
        ref = "RFC 4950 §2, RFC 3032 §2.1"
        self.bitfield(
            "mplslabel",
            "Label",
            "tlv",
            20,
            str(label),
            "icmp.mpls.label",
            "Label",
            ref,
            tree=t,
            ws_group=lse,
            ws_bits=wsbits(label, 20, 0, 24),
        )
        self.bitfield(
            "mplsexp",
            "TC",
            "tlv",
            3,
            str(exp),
            "icmp.mpls.exp",
            "Experimental",
            ref + ", RFC 5462",
            tree=t,
            ws_group=lse,
            ws_bits=wsbits(exp, 3, 20, 24),
        )
        self.bitfield(
            "mplss",
            "S",
            "tlv",
            1,
            str(s),
            "icmp.mpls.s",
            "Stack bit",
            ref,
            tree=t,
            ws_group=lse,
            ws_bits=wsbits(s, 1, 23, 24),
            ws_value="Set" if s else "Not set",
        )
        self.add(
            "mplsttl",
            "TTL",
            "tlv",
            ext[11:12],
            str(ttl),
            "icmp.mpls.ttl",
            "Time to live",
            ref,
            tree=t,
            ws_group=lse,
        )

    def out(self, sid, message, encapsulation, layers):
        s = super().out(sid, message, encapsulation, layers)
        s["protocol"] = "ICMP"
        s["grid_from"] = 272  # the bit diagram starts at the ICMP message: 14 bytes of Ethernet + 20 of IPv4
        return s


def icmp_sample(sid, message, pkt, body, *, src_mac=MAC_GW, dst_mac=MAC_HOST):
    """One Ethernet II frame on A's link carrying the ICMP message pkt; body(fr, msg) maps it."""
    fr = ICMPFrame()
    msg = fr.encap(src_mac, dst_mac, pkt)
    src, dst = (str(ipaddress.IPv4Address(pkt[k : k + 4])) for k in (12, 16))
    body(fr, msg)
    layers = {
        "eth": f"Ethernet II, Src: {src_mac}, Dst: {dst_mac}",
        "ip": f"Internet Protocol Version 4, Src: {src}, Dst: {dst}",
        "icmp": "Internet Control Message Protocol",
    }
    return fr.out(sid, message, "IPv4, protocol 1", layers)


def icmp_probe(ttl: int, dport: int, ident: int, size: int = 60) -> bytes:
    """A UDP traceroute probe from A to B: `size` bytes of IP datagram, ports as traceroute picks them."""
    data = bytes(0x40 + k % 32 for k in range(size - 28))
    return ipv4_packet(
        IP_HOST, IP_DST, 17, udp_datagram(IP_HOST, IP_DST, 49153, dport, data), ident=ident, ttl=ttl
    )


def icmp_echo_req() -> dict:
    """The Echo of the IPv4 page (ipv4-base), read here from the ICMP header."""
    pkt = ipv4_packet(IP_HOST, IP_DST, 1, icmp_echo(0x0B1E, 1, ICMP_DATA), ident=0x4D2A, df=1)
    more = [{"label": "[Response frame: 2]", "ws": "icmp.resp_in"}]
    return icmp_sample(
        "icmp-echo-req", "Echo Request", pkt, lambda fr, m: fr.echo(m, more), src_mac=MAC_HOST, dst_mac=MAC_GW
    )


def icmp_echo_rep() -> dict:
    """B's answer after two routers: same Identifier, Sequence Number and data, type 0."""
    msg = icmp_message(0, 0, struct.pack("!HH", 0x0B1E, 1), ICMP_DATA)
    pkt = ipv4_packet(IP_DST, IP_HOST, 1, msg, ident=0x8F13, ttl=62)
    more = [
        {"label": "[Request frame: 1]", "ws": "icmp.resp_to"},
        {"label": f"[Response time: {ICMP_RESP_MS} ms]", "ws": "icmp.resptime"},
    ]
    return icmp_sample("icmp-echo-rep", "Echo Reply", pkt, lambda fr, m: fr.echo(m, more))


def icmp_error(sid, message, src, mtype, code, rest, orig, l4, *, ttl=255, dscp=0, ident=0, ext=b""):  # noqa: PLR0917 (the message in wire order)
    msg = icmp_message(mtype, code, rest, orig + ext)
    pkt = ipv4_packet(src, IP_HOST, 1, msg, ident=ident, ttl=ttl, dscp=dscp)

    def body(fr, m):
        fr.head(m)
        if mtype == 5:
            fr.add(
                "icmpgw",
                "Gateway Internet Address",
                "header",
                m[4:8],
                str(ipaddress.IPv4Address(m[4:8])),
                "icmp.redir_gw",
                "Gateway Address",
                "RFC 792",
                tree="icmp",
            )
        elif m[5]:
            fr.unused(m[4:5])
            fr.add(
                "icmplen",
                "Length",
                "header",
                m[5:6],
                str(m[5]),
                "icmp.length",
                "Length",
                "RFC 4884 §4.2",
                tree="icmp",
                ws_more=[
                    {
                        "label": f"[Length of original datagram: {m[5] * 4}]",
                        "ws": "icmp.length.original_datagram",
                    }
                ],
            )
            fr.unused(m[6:8], "icmpunusedb")
        elif (mtype, code) == (3, 4):
            fr.unused(m[4:6])
            mtu = struct.unpack("!H", m[6:8])[0]
            fr.add(
                "icmpmtu",
                "Next-Hop MTU",
                "header",
                m[6:8],
                str(mtu),
                "icmp.mtu",
                "MTU of next hop",
                "RFC 1191 §4",
                tree="icmp",
            )
        else:
            fr.unused(m[4:8])
        fr.quoted(m[8 : 8 + len(orig)], l4)
        if ext:
            fr.extension(m[8 + len(orig) :])

    return icmp_sample(sid, message, pkt, body)


def icmp_big_segment() -> bytes:
    """A full-size TCP segment from A to B: Total Length 1500, DF set (as on the IPv4 page, animation C)."""
    seg = tcp_segment(IP_HOST, IP_DST, 49152, 443, 0x2F5A1C01, 0x6B3D9A11, 0x010, 64240, data=bytes(1460))
    return ipv4_packet(IP_HOST, IP_DST, 6, seg, ident=0x4D2E, df=1)


def icmp_frag_needed() -> dict:
    """R1 cannot forward 1500 bytes into its 1400-byte tunnel: type 3 code 4, header + 8 bytes quoted."""
    return icmp_error(
        "icmp-frag-needed",
        "Fragmentation Needed",
        ICMP_R1,
        3,
        4,
        struct.pack("!HH", 0, 1400),
        icmp_big_segment()[:28],
        "tcp",
        ident=0x0A31,
    )


def icmp_port_unreach() -> dict:
    """B has no listener on UDP 33440 (first probe with TTL 3, seen with TTL 1): type 3 code 3.
    B quotes the whole 60-byte probe and marks the error CS6, as RFC 1812 recommends."""
    return icmp_error(
        "icmp-port-unreach",
        "Port Unreachable",
        IP_DST,
        3,
        3,
        bytes(4),
        icmp_probe(1, 33440, 0x5C17),
        "udp",
        ttl=62,
        dscp=48,
        ident=0xC2A4,
    )


def icmp_time_exceeded() -> dict:
    """R1 drops the first probe (TTL 1, UDP 33434): type 11 code 0, header + 8 bytes quoted."""
    return icmp_error(
        "icmp-time-exceeded",
        "Time Exceeded",
        ICMP_R1,
        11,
        0,
        bytes(4),
        icmp_probe(1, 33434, 0x5C11)[:28],
        "udp",
        ident=0x0A2F,
    )


def icmp_redirect() -> dict:
    """R1 forwards A's Echo for 203.0.113.200 back out of the same LAN to R3: type 5 code 1."""
    echo = ipv4_packet(IP_HOST, ICMP_SRV, 1, icmp_echo(0x0B1F, 1, ICMP_DATA), ident=0x4D30, df=1)
    return icmp_error(
        "icmp-redirect", "Redirect", ICMP_R1, 5, 1, ip4(ICMP_R3), echo[:28], "icmp", ident=0x0A33
    )


def icmp_ts_req() -> dict:
    """Timestamp request sent by A at 10:00:00.000 UT (36,000,000 ms after midnight)."""
    body = struct.pack("!III", 36_000_000, 0, 0)
    pkt = ipv4_packet(
        IP_HOST, IP_DST, 1, icmp_message(13, 0, struct.pack("!HH", 0x0B20, 1), body), ident=0x4D31
    )
    return icmp_sample(
        "icmp-ts-req",
        "Timestamp Request",
        pkt,
        lambda fr, m: fr.timestamp(m),
        src_mac=MAC_HOST,
        dst_mac=MAC_GW,
    )


def icmp_te_mpls() -> dict:
    """R2 as a label switching router: Time Exceeded for a 128-byte probe that arrived with label
    24001 and MPLS TTL 1. Length = 32 words (128 bytes quoted), then the RFC 4950 extension."""
    probe = icmp_probe(1, 33437, 0x5C14, size=128)
    return icmp_error(
        "icmp-te-mpls",
        "Time Exceeded + MPLS",
        ICMP_R2,
        11,
        0,
        struct.pack("!BBH", 0, len(probe) // 4, 0),
        probe,
        "udp",
        ttl=254,
        ident=0x1B52,
        ext=icmp_ext_mpls(24001, 0, 1, 1),
    )


ICMP_SAMPLES = {
    "icmp-echo-req": icmp_echo_req,
    "icmp-echo-rep": icmp_echo_rep,
    "icmp-frag-needed": icmp_frag_needed,
    "icmp-port-unreach": icmp_port_unreach,
    "icmp-time-exceeded": icmp_time_exceeded,
    "icmp-redirect": icmp_redirect,
    "icmp-ts-req": icmp_ts_req,
    "icmp-te-mpls": icmp_te_mpls,
}


def icmp_self_test() -> int:
    """Outer IPv4 and ICMP checksums verify; every quoted IPv4 header verifies too; the reply
    echoes the request's Identifier, Sequence Number and data; the extension checksum verifies
    and the RFC 4884 length attribute counts the quoted bytes in 32-bit words."""
    errors, raw = 0, {}
    for name, build in ICMP_SAMPLES.items():
        ip = raw[name] = bytes.fromhex(build()["hex"].replace(" ", ""))[14:]
        msg = ip[20:]
        bad = inet_checksum(ip[:20]) or inet_checksum(msg) or struct.unpack("!H", ip[2:4])[0] != len(ip)
        if msg[0] in (3, 5, 11) and inet_checksum(msg[8:28]):
            bad = True
        if bad:
            print(f"FAIL {name} IPv4 or ICMP checksum")
            errors += 1
    req, rep = raw["icmp-echo-req"][20:], raw["icmp-echo-rep"][20:]
    if (req[0], rep[0]) != (8, 0) or req[4:] != rep[4:]:
        print("FAIL icmp echo reply does not echo the request")
        errors += 1
    te = raw["icmp-te-mpls"][20:]
    if te[5] * 4 != 128 or inet_checksum(te[8 + 128 :]) or len(te) != 8 + 128 + 12:
        print("FAIL icmp-te-mpls length attribute or extension checksum")
        errors += 1
    return errors


SAMPLES = {
    "ospf-hello": ospf_hello,
    **ETH_SAMPLES,
    **IPV4_SAMPLES,
    **OSI_SAMPLES,
    **ARP_SAMPLES,
    **ICMP_SAMPLES,
}


def ipv4_self_test() -> int:
    """Every header checksum verifies and Total Length matches; the three fragments carry the
    datagram's data at offsets 0, 185 and 370 (x 8 bytes); the CE packet's checksum equals the
    RFC 1624 incremental update of the ECT(0) packet's (TTL and ECN changed)."""
    errors = 0
    for name in IPV4_SAMPLES:
        ip = bytes.fromhex(SAMPLES[name]()["hex"].replace(" ", ""))[14:]
        if inet_checksum(ip[: (ip[0] & 0x0F) * 4]) or struct.unpack("!H", ip[2:4])[0] != len(ip):
            print(f"FAIL {name} header checksum or Total Length")
            errors += 1
    big = ipv4_big_datagram()
    frags = ipv4_fragments(big, 1500)
    if b"".join(f[20:] for f in frags) != big[20:] or [struct.unpack("!H", f[6:8])[0] for f in frags] != [
        0x2000,
        0x2000 | 185,
        370,
    ]:
        print("FAIL ipv4 fragments do not rebuild the datagram")
        errors += 1
    ect, ce = (bytes.fromhex(SAMPLES[n]()["hex"].replace(" ", ""))[14:34] for n in ("ipv4-ect", "ipv4-ce"))
    acc = ~struct.unpack("!H", ect[10:12])[0] & 0xFFFF
    for k in range(0, 20, 2):
        if k != 10 and ect[k : k + 2] != ce[k : k + 2]:
            acc += (~struct.unpack("!H", ect[k : k + 2])[0] & 0xFFFF) + struct.unpack("!H", ce[k : k + 2])[0]
    while acc >> 16:
        acc = (acc & 0xFFFF) + (acc >> 16)
    if ~acc & 0xFFFF != struct.unpack("!H", ce[10:12])[0]:
        print("FAIL ipv4 RFC 1624 incremental update")
        errors += 1
    return errors


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
    errors += ipv4_self_test()
    # OSI samples: IPv4, UDP and TCP checksums verify (the last two over the pseudo-header).
    for name, proto in (("osi-dns", 17), ("osi-http", 6), ("osi-syn", 6)):
        ip = bytes.fromhex(SAMPLES[name]()["hex"].replace(" ", ""))[14:]
        l4 = ip[20:]
        pseudo = ip[12:20] + struct.pack("!BBH", 0, proto, len(l4))
        if inet_checksum(ip[:20]) != 0 or ip[9] != proto or inet_checksum(pseudo + l4) != 0:
            print(f"FAIL {name} IPv4 or transport checksum")
            errors += 1
    errors += arp_self_test()
    errors += icmp_self_test()
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
        help="rewrite the data-packet JSON blocks, chips lines and packet tab lists of a page",
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
# Markup of templates/protocol-template.html: a packet article (with what precedes it), its chips
# line, a packet set and the set's tab list.
PACKET_ARTICLE = re.compile(
    r"(?:\s|<!--.*?-->)*"
    r'<article class="packet"(?: id="([^"]+)")? data-packet="([a-z0-9-]+)"[^>]*>.*?</article>',
    re.S,
)
CHIPS = re.compile(r'(<ul class="packet-meta"(?: data-ref="([^"]*)")?>).*?(</ul>)', re.S)
PACKET_SET = re.compile(r'<div class="pkt-set" id="[a-z0-9-]+">')
SET_TABS = re.compile(r'\s*<div role="tablist" data-aria="packets"[^>]*>.*?</div>', re.S)
GRID = re.compile(r'<div class="bitgrid"(?: style="--rows:\d+")?')
PANEL = re.compile(r'(?:<div class="tour">.*?</div>\s*)?(<div class="fpanel")', re.S)
TOUR = (
    '<div class="tour"><span class="tour-t">'
    '<span data-l="fr">Visite guidée</span><span data-l="en">Guided tour</span>'
    '<span data-l="nl">Rondleiding</span><span data-l="de">Geführte Tour</span></span>'
    '<button type="button" data-tour="prev" disabled>'
    '<span data-l="fr">Champ précédent</span><span data-l="en">Previous field</span>'
    '<span data-l="nl">Vorig veld</span><span data-l="de">Vorheriges Feld</span></button>'
    '<button type="button" data-tour="next">'
    '<span data-l="fr">Champ suivant</span><span data-l="en">Next field</span>'
    '<span data-l="nl">Volgend veld</span><span data-l="de">Nächstes Feld</span></button>'
    '<p class="tour-now"></p></div>\n          '
)
BYTES = (("fr", "octets"), ("en", "bytes"), ("nl", "bytes"), ("de", "Byte"))  # the template's "bytes"


def update(path: str) -> int:
    """Inject the builder's output into a page, so sample values are never hand-written."""
    page = pathlib.Path(path)
    text = page.read_text(encoding="utf-8")
    unknown = [m.group(2) for m in PACKET_BLOCK.finditer(text) if m.group(2) not in SAMPLES]
    if unknown:
        print(f"unknown sample(s) in {path}: {', '.join(unknown)}")
        return 1
    page.write_text(rewrite(text), encoding="utf-8")
    print(f"{path}: {len(PACKET_BLOCK.findall(text))} packet block(s), chips lines and tab lists updated")
    return 0


def rewrite(text: str) -> str:
    """The page with every value taken from the samples written in: the data-packet JSON blocks,
    each packet's chips line and each packet set's tab list. Written in the markup rather than
    by the page script, they are there from the first paint: a page that renders progressively
    (slow link, busy CPU) does not shift. Unknown samples are left as they are."""
    text = PACKET_BLOCK.sub(
        lambda m: m.group(1) + embed(m.group(2)) + m.group(4) if m.group(2) in SAMPLES else m.group(0), text
    )
    text = PACKET_ARTICLE.sub(with_chips, text)
    out, pos = [], 0
    for m in PACKET_SET.finditer(text):
        tabs = SET_TABS.match(text, m.end())
        arts, end = [], tabs.end() if tabs else m.end()
        while a := PACKET_ARTICLE.match(text, end):
            arts.append(a)
            end = a.end()
        body = "".join(a.group(0) if a.group(1) else with_id(a.group(0), a.group(2)) for a in arts)
        out += [text[pos : m.end()], tablist(arts) if len(arts) > 1 else "", body]
        pos = end
    return "".join(out) + text[pos:]


def with_chips(m: re.Match) -> str:
    """A packet article with its chips line: length, encapsulation and the page's reference."""
    sample = m.group(2)
    if sample not in SAMPLES:
        return m.group(0)
    s = SAMPLES[sample]()
    unit = "".join(f'<span data-l="{lang}">{word}</span>' for lang, word in BYTES)

    def line(c: re.Match) -> str:
        items = [f"{s['length']} {unit}", html.escape(s["encapsulation"], quote=False), c.group(2) or ""]
        return c.group(1) + "".join(f"<li>{item}</li>" for item in items if item) + c.group(3)

    article = CHIPS.sub(line, m.group(0), count=1)
    article = GRID.sub(f'<div class="bitgrid" style="--rows:{grid_rows(s)}"', article, count=1)
    # data-view="layers": the frame is read layer by layer (bit diagram, layer strip and detail
    # panel only), so it gets no field-by-field tour.
    tag = re.match(r"<article\b[^>]*>", m.group(0).lstrip()) or re.search(r"<article\b[^>]*>", m.group(0))
    tour = "" if 'data-view="layers"' in tag.group(0) else TOUR
    return PANEL.sub(lambda p: tour + p.group(1), article, count=1)


def grid_rows(sample: dict) -> int:
    """Rows the page script draws in the bit diagram (same walk as NPE.packet in the template):
    the page reserves that height, so the diagram does not push the content below it when the
    script fills it in after the first paint."""
    origin, rows, shift, prev = sample.get("grid_from", 0), set(), 0, None
    for f in sample["fields"]:
        if f["offset"] < origin:
            continue
        start, left, first, row = f["offset"] - origin + shift, f["bits"], True, 1
        # Layers view: each protocol header starts on a new row.
        if sample.get("stack") and prev and f["layer"] != prev and start % 32:
            shift += 32 - start % 32
            start += 32 - start % 32
        prev = f["layer"]
        while left > 0:
            col = start % 32
            take = min(left, 32 - col)
            more = left // 32 if not first and not f.get("rows") and col == 0 else 0
            rows.add(start // 32)
            if more > 1:
                start, left = start + more * 32, left - more * 32
                continue
            if f.get("rows") and row == f["rows"] and left > take:
                break
            start, left, first, row = start + take, left - take, False, row + 1
    return len(rows)


def with_id(article: str, sample: str) -> str:
    """The id NPE.pktset gives a packet of a set (aria-controls of its tab)."""
    old = '<article class="packet" data-packet='
    return article.replace(old, f'<article class="packet" id="pkt-{sample}" data-packet=', 1)


def tablist(arts: list) -> str:
    """Tab list of a packet set, adopted by NPE.pktset. Label: data-tab on the article, else the
    sample's message; the first tab is selected, the others leave the tab order (roving tabindex)."""
    tabs = []
    for k, a in enumerate(arts):
        sample = a.group(2)
        tag = re.search(r"<article\b[^>]*>", a.group(0)).group(0)
        own = re.search(r'\sdata-tab="([^"]*)"', tag)
        label = own.group(1) if own else html.escape(SAMPLES[sample]()["message"], quote=False)
        state = 'aria-selected="true"' if k == 0 else 'aria-selected="false" tabindex="-1"'
        tabs.append(
            f'<button type="button" role="tab" id="tab-{sample}" data-pkt="{sample}" '
            f'aria-controls="{a.group(1) or "pkt-" + sample}" {state}>{label}</button>'
        )
    return '<div role="tablist" data-aria="packets" aria-label="Sample packets">' + "".join(tabs) + "</div>"


def embed(sample: str) -> str:
    """Canonical one-line JSON embedded in pages; scripts/check_pages.py compares against it."""
    return json.dumps(SAMPLES[sample](), separators=(",", ":"), ensure_ascii=False)


if __name__ == "__main__":
    sys.exit(main())
