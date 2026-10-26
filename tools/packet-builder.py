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


SAMPLES = {"ospf-hello": ospf_hello}


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
    # The field map must tile the packet exactly: contiguous, byte-aligned, no gap.
    for name, build in SAMPLES.items():
        s = build()
        raw = bytes.fromhex(s["hex"].replace(" ", ""))
        pos = 0
        for f in s["fields"]:
            if f["offset"] != pos or f["hex"] != raw[pos // 8 : (pos + f["bits"]) // 8].hex(" "):
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
