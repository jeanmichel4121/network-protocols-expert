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
    router_id="1.1.1.1",
    area="0.0.0.0",
    mask="255.255.255.0",
    hello=10,
    options=0x02,
    priority=1,
    dead=40,
    dr="192.0.2.2",
    bdr="192.0.2.1",
    neighbors=("2.2.2.2",),
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
    return {
        "protocol": "OSPFv2",
        "message": "Hello",
        "length": length,
        "checksum": f"0x{csum:04x}",
        "hex": pkt.hex(" "),
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
    print("self-test OK" if not errors else f"self-test FAILED ({errors})")
    return 1 if errors else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("sample", nargs="?", choices=sorted(SAMPLES))
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    if a.self_test:
        return self_test()
    if not a.sample:
        p.print_help()
        return 2
    print(json.dumps(SAMPLES[a.sample](), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
