# Ethernet sources

Hierarchy: standards (IEEE, RFC, IANA) > vendor documentation > books/whitepapers.
Accessed 24 October to 15 November 2026. Same list as section 8 (Sources) of `index.html`.

## Standards

- **IEEE Std 802.3-2022**: Clause 1.4 (definitions: frame vs packet); Clause 3: §3.1.1 packet format, §3.2.1 preamble, §3.2.2 SFD, §3.2.3 addresses (§3.2.3.1 I/G), §3.2.6 Length/Type, §3.2.7 MAC client data, §3.2.8 pad, §3.2.9 FCS, §3.3 bit transmission order; Clause 4: §4.2 MAC, §4.2.3 CSMA/CD, §4.4.2 parameters (minFrameSize, maxUntaggedFrameSize, maxEnvelopeFrameSize, interPacketGap, slotTime, attemptLimit, backoffLimit, jamSize); Clause 31 + Annex 31A (opcodes), 31B (PAUSE), 31D (PFC).
- **IEEE 802.3ac**: VLAN tag frame extension (max + 4 octets): https://www.ieee802.org/3/ac/public/maxframe.pdf
- **IEEE 802.3as**: envelope frames (maxEnvelopeFrameSize 2000).
- **IEEE Std 802.1Q-2022**: §6.9 tag insertion/removal and re-padding; §8.6.3, Tables 8-1/8-2 reserved addresses; §8.7 learning; §8.8.3 ageing time (300 s); §9.5 TPID; §9.6 TCI (PCP/DEI/VID); Table 9-2 reserved VIDs; Annex I traffic types (Table I-2); Clause 14 spanning tree; Clause 36 PFC (ex-802.1Qbb).
- **IEEE 802.1 public group address listing** (2018): https://ieee802.org/1/files/public/docs2018/maint-seaman-public-group-addresses-0918-v01.html
- **IEEE 802.1Qbb PFC proposal** (frame layout, opcode 0x0101): https://grouper.ieee.org/groups/802/1/files/public/docs2008/bb-pelissier-pfc-proposal-0408.pdf
- **IEEE Std 802-2014**: §9 EtherType, OUI, SNAP.
- **ISO/IEC 8802-2 (IEEE 802.2) LLC**: §5.2 LSAP (I/G, C/R), §5.4 control field.
- **IEEE 802.1AB** (LLDP), **802.1AE** (MACsec, 0x88E5), **802.1X** (EAPOL 0x888E).
- **RFC 9542** (obsoletes RFC 7042): §2.1, §2.1.1 (I/G, U/L), §2.1.2 (CID), §2.1.3 (01-00-5E, IPv4 multicast range), §2.1.4 (documentation MACs 00-00-5E-00-53-xx), §2.3.1 (33-33 IPv6 multicast), §3 (EtherType ≥ 0x0600, 0x88B5/0x88B6): https://www.rfc-editor.org/rfc/rfc9542.html
- **RFC 894** IP over Ethernet II, **RFC 1042** IP over 802 + SNAP, **RFC 1112 §6.4** IPv4 multicast mapping, **RFC 2464 §7** IPv6 multicast mapping, **RFC 826** ARP, **RFC 2328 §10.6** OSPF DBD MTU check, **RFC 2281 §6.1** HSRP virtual MAC, **RFC 9568 §7.3** VRRPv3 virtual MAC, **RFC 7348** VXLAN, **RFC 5737** IPv4 documentation prefixes, **RFC 2544** benchmarking.
- **IANA IEEE 802 Numbers** (EtherTypes; last updated 2024-11-03): https://www.iana.org/assignments/ieee-802-numbers/ieee-802-numbers.xhtml (the IEEE RA public EtherType list is authoritative).

## Tools and analysis

- Wireshark Display Filter Reference (1.0.0-4.6.9): https://www.wireshark.org/docs/dfref/e/eth.html, https://www.wireshark.org/docs/dfref/v/vlan.html, https://www.wireshark.org/docs/dfref/l/llc.html, https://www.wireshark.org/docs/dfref/m/macc.html (`macc.*` since 1.8, `macctrl.*` ≤ 1.6).
- Wireshark source `epan/dissectors/packet-ethertype.c` (`add_dix_trailer`): https://github.com/wireshark/wireshark/blob/master/epan/dissectors/packet-ethertype.c
- P. Koopman, "32-Bit Cyclic Redundancy Codes for Internet Applications", DSN 2002.
- `tools/packet-builder.py --self-test`: FCS, CRC residue 0x2144DF1C, ≥ 64 octets for all 8 frames; cross-decoded with scapy.

## Vendor documentation

Numbers 16 to 21 in the page, one entry per vendor.

### Cisco (16)

- Interface and Hardware Components Configuration Guide, IOS XE Cupertino 17.9.x (Catalyst 9300), "Configuring System MTU": https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/configuration_guide/int_hw/b_179_int_and_hw_9300_cg/configuring_system_mtu.html
- Interface and Hardware Components Configuration Guide, IOS XE Cupertino 17.9.x (Catalyst 9300), "Configuring Per-Port MTU": https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/configuration_guide/int_hw/b_179_int_and_hw_9300_cg/configuring_per_port_mtu.html
- Interface and Hardware Components Configuration Guide, IOS XE Cupertino 17.9.x (Catalyst 9300), "Configuring Interface Characteristics" (IEEE 802.3x flow control): https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/configuration_guide/int_hw/b_179_int_and_hw_9300_cg/configuring_interface_characteristics.html
- VLAN Configuration Guide, IOS XE Cupertino 17.9.x (Catalyst 9300), "Configuring VLAN Trunks": https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/configuration_guide/vlan/b_179_vlan_9300_cg/configuring_vlan_trunks.html
- Layer 2 Configuration Guide, IOS XE Cupertino 17.9.x (Catalyst 9300), "Configuring IEEE 802.1Q Tunneling": https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/configuration_guide/lyr2/b_179_lyr2_9300_cg/configuring_ieee_802_1q_tunneling.html
- Network Management Configuration Guide, IOS XE Cupertino 17.9.x (Catalyst 9300), "Configuring Packet Capture": https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/configuration_guide/nmgmt/b_179_nmgmt_9300_cg/configuring_packet_capture.html
- Command Reference, IOS XE Cupertino 17.9.x (Catalyst 9300), "Interface and Hardware Commands": https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/command_reference/b_179_9300_cr/interface_and_hardware_commands.html
- Command Reference, IOS XE Cupertino 17.9.x (Catalyst 9300), "Layer 2/3 Commands": https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/command_reference/b_179_9300_cr/layer_2_3_commands.html
- Command Reference, IOS XE Cupertino 17.9.x (Catalyst 9300), "System Management Commands": https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/command_reference/b_179_9300_cr/system_management_commands.html
- TAC 217233, "Understand and Troubleshoot MTU on Catalyst 9000 Series Switches": https://www.cisco.com/c/en/us/support/docs/switches/catalyst-9500-series-switches/217233-troubleshoot-mtu-on-catalyst-9000-series.html
- TAC 217726, "Configure and Troubleshoot QinQ and L2PT on Catalyst 9000 Switches" (IOS XE 17.3.3): https://www.cisco.com/c/en/us/support/docs/switches/catalyst-9300-switch/217726-configure-and-verify-and-troubleshoot-qi.html
- TAC 218397, "Troubleshoot Port Flaps on Catalyst 9000 Switches": https://www.cisco.com/c/en/us/support/docs/switches/catalyst-9500-series-switches/218397-troubleshoot-port-flaps-on-catalyst-9000.html
- TAC 225617, "Troubleshooting Network Latency and Packet Drops on Catalyst 9000 Switches": https://www.cisco.com/c/en/us/support/docs/switches/catalyst-9300-series-switches/225617-troubleshooting-network-latency-and.html
- Cisco Nexus 9000 Series NX-OS Interfaces Configuration Guide, Release 10.4(x), "Configuring Basic Interface Parameters": https://www.cisco.com/c/en/us/td/docs/dcn/nx-os/nexus9000/104x/configuration/interfaces/cisco-nexus-9000-series-nx-os-interfaces-configuration-guide-release-104x/m_configuring_basic_interface_parameters_93x.html
- Cisco Nexus 9000 Series NX-OS Interfaces Configuration Guide, Release 10.4(x), "Configuring Q-in-Q VLAN Tunnels": https://www.cisco.com/c/en/us/td/docs/dcn/nx-os/nexus9000/104x/configuration/interfaces/cisco-nexus-9000-series-nx-os-interfaces-configuration-guide-release-104x/m_configuring_q-in-q_vlan_tunnels_9x.html
- Cisco Nexus 9000 Series NX-OS Quality of Service Configuration Guide, Release 10.4(x), "Configuring Link Level Flow Control": https://www.cisco.com/c/en/us/td/docs/dcn/nx-os/nexus9000/104x/configuration/qos/cisco-nexus-9000-series-nx-os-quality-of-service-configuration-guide-104x/m-configuring-llfc.html
- Cisco Nexus 9000 Series NX-OS Quality of Service Configuration Guide, Release 10.4(x), "Configuring Priority Flow Control": https://www.cisco.com/c/en/us/td/docs/dcn/nx-os/nexus9000/104x/configuration/qos/cisco-nexus-9000-series-nx-os-quality-of-service-configuration-guide-104x/m-configuring-priority-flow-control.html
- TAC 216239, "Identify and Trace Nexus 9000 Cloud Scale ASIC CRC": https://www.cisco.com/c/en/us/support/docs/switches/nexus-9000-series-switches/216239-nexus-9000-cloud-scale-asic-crc-identifi.html
- TAC 220133, "Troubleshoot Nexus 9000 Interface CRC Error with Script": https://www.cisco.com/c/en/us/support/docs/ios-nx-os-software/nx-os-software/220133-troubleshoot-nexus-9000-interface-crc-er.html
- TAC 218096, "Troubleshoot Nexus Cheat Sheet for Beginners": https://www.cisco.com/c/en/us/support/docs/switches/nexus-9000-series-switches/218096-troubleshoot-nexus-cheat-sheet-for-begin.html
- Interface and Hardware Component Configuration Guide for Cisco ASR 9000 Series Routers, IOS XR Release 7.9.x, "Configuring 802.1Q VLAN Interfaces": https://www.cisco.com/c/en/us/td/docs/routers/asr9000/software/asr9k-r7-9/configuration/guide/b-interfaces-hardware-component-cg-asr9000-79x/configuring-802-1q-vlan-interfaces.html
- Interface and Hardware Component Configuration Guide for Cisco ASR 9000 Series Routers, IOS XR Release 7.9.x, "Configuring Ethernet Interfaces": https://www.cisco.com/c/en/us/td/docs/routers/asr9000/software/asr9k-r7-9/configuration/guide/b-interfaces-hardware-component-cg-asr9000-79x/configuring-ethernet-interfaces.html
- Interface and Hardware Component Command Reference for Cisco ASR 9000 Series Routers, "Global Interface Commands": https://www.cisco.com/c/en/us/td/docs/routers/asr9000/software/interfaces/command/reference/b-interfaces-hardware-component-cr-asr9000/global-interface-commands.html
- Interface and Hardware Component Command Reference for Cisco ASR 9000 Series Routers, "Ethernet Interface Commands": https://www.cisco.com/c/en/us/td/docs/routers/asr9000/software/interfaces/command/reference/b-interfaces-hardware-component-cr-asr9000/ethernet-interface-commands.html
- TAC 214057, "ASR9000 Ethernet loopback testing": https://www.cisco.com/c/en/us/support/docs/routers/asr-9000-series-aggregation-services-routers/214057-asr9000-ethernet-loopback-testing.html

### Check Point (17)

- R81.20 Gaia Administration Guide, "Physical Interfaces": https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_Gaia_AdminGuide/Content/Topics-GAG/Physical-Interfaces.htm
- R81.20 Gaia Administration Guide, "VLAN Interfaces": https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_Gaia_AdminGuide/Content/Topics-GAG/VLAN-Interfaces.htm
- R81.20 Gaia Administration Guide, "Configuring ARP in Gaia Clish": https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_Gaia_AdminGuide/Content/Topics-GAG/ARP-Gaia-Clish.htm
- sk98348 "Best Practices - Security Gateway Performance" (R81.10, R81.20, R82): https://support.checkpoint.com/results/sk/sk98348
- sk61922 "Excessive RX Errors / RX Drops found on interface": https://support.checkpoint.com/results/sk/sk61922
- sk166424 "Number of RX packet drops on interfaces increases on a Security Gateway R80.30 and higher with Gaia kernel 3.10": https://support.checkpoint.com/results/sk/sk166424
- R81.20 ClusterXL Administration Guide, "Viewing Bond Interfaces": https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_ClusterXL_AdminGuide/Content/Topics-CXLG/Viewing-Bond-Interfaces.htm
- sk141412 "cppcap - Check Point Traffic Capture Tool" (built in since R80.40): https://support.checkpoint.com/results/sk/sk141412
- R82 CLI Reference Guide, "cppcap": https://sc1.checkpoint.com/documents/R82/WebAdminGuides/EN/CP_R82_CLI_ReferenceGuide/Content/Topics-CLIG/FWG/cppcap.htm

### F5 (18)

- TMSH Reference, "net vlan": https://clouddocs.f5.com/cli/tmsh-reference/latest/modules/net/net_vlan.html
- TMSH Reference, "net interface": https://clouddocs.f5.com/cli/tmsh-reference/latest/modules/net/net_interface.html
- TMSH Reference, "net arp": https://clouddocs.f5.com/cli/tmsh-reference/latest/modules/net/net_arp.html
- TMSH Reference, "net fdb vlan": https://clouddocs.f5.com/cli/tmsh-reference/latest/modules/net/net_fdb_vlan.html
- BIG-IP TMOS Routing Administration 14.1.0, "About double tagging": https://techdocs.f5.com/en-us/bigip-14-1-0/big-ip-tmos-routing-administration-14-1-0/vlans-vlan-groups-and-vxlan/about-vlans/about-vlans-and-interfaces/about-tagged-interfaces/about-double-tagging.html
- BIG-IP TMOS Routing Administration 14.1.0, "About flow control": https://techdocs.f5.com/en-us/bigip-14-1-0/big-ip-tmos-routing-administration-14-1-0/interfaces/interface-properties/about-flow-control.html
- K6399 "Support for jumbo Ethernet frames": https://my.f5.com/manage/s/article/K6399
- K13339 "Configuring the BIG-IP system to support jumbo Ethernet frames": https://my.f5.com/manage/s/article/K13339
- Bug ID 484542 "QinQ tag-mode can be set on unsupported platforms": https://cdn.f5.com/product/bugtracker/ID484542.html
- K000138562 "Excessive amount of FCS errors on internal interfaces in limited amount of time": https://my.f5.com/manage/s/article/K000138562
- K000135378 "Unable to amend interface mtu": https://my.f5.com/manage/s/article/K000135378
- Bug ID 708415: https://cdn.f5.com/product/bugtracker/ID708415.html
- K77941522 "Interface mirroring with port-mirror configuration can result in increased interface drops": https://my.f5.com/manage/s/article/K77941522
- K58145248 "F5 appears to spoof MAC addresses": https://my.f5.com/manage/s/article/K58145248
- K15204131 "BIG-IP ARP cache table is not updated": https://my.f5.com/manage/s/article/K15204131
- K14107 "Configuring the media speed and duplex settings for network interfaces": https://my.f5.com/manage/s/article/K14107
- K49350294 "Interfaces showing down on BIG-IP hardware": https://my.f5.com/manage/s/article/K49350294
- K02391029 "vCMP guest not responding to SYN packets coming from clients due to incorrect FDB entry on vCMP host": https://my.f5.com/manage/s/article/K02391029
- K13637 "Capturing internal TMM information with tcpdump": https://my.f5.com/manage/s/article/K13637
- K411 "Overview of packet tracing with the tcpdump utility": https://my.f5.com/manage/s/article/K411
- K7227 "Considerations when using the tcpdump utility with tagged VLAN traffic": https://my.f5.com/manage/s/article/K7227
- K6546 "Recommended methods and limitations for running tcpdump on a BIG-IP system": https://my.f5.com/manage/s/article/K6546
- K65251607 "Using tcpdump to create rotating packet capture files": https://my.f5.com/manage/s/article/K65251607

### Palo Alto Networks (19)

- KB "How to Enable/Use/Disable/Check Jumbo Frame Support": https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClVaCAK
- KB "How to Configure MTU and MSS Settings from the CLI" (tagged 8.1-10.0): https://knowledgebase.paloaltonetworks.com/kcsArticleDetail?id=kA10g000000ClLI
- PAN-OS Networking Administrator's Guide, "Configure Session Settings": https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-networking-admin/session-settings-and-timeouts/configure-session-settings
- Web Interface Help 11.1, "Layer 3 Subinterface": https://docs.paloaltonetworks.com/ngfw/help/11-1/network/network-interfaces/layer-3-subinterface
- KB "How to Configure 802.1q VLAN tag on 802.3ad/Aggregate Group": https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClJQCA0
- KB "How to Disable Ethernet Flow on a Single Port": https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA14u000000HBc7CAG
- PAN-OS Administrator's Guide, "Zone Protection Profiles" (Protocol Protection): https://docs.paloaltonetworks.com/ngfw/administration/zone-protection-and-dos-protection/zone-defense/zone-protection-profiles
- KB "The Difference Between Receive Errors for Hardware and Logical Interface Counters": https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClWkCAK
- KB "Identify configured Interface MTU": https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000CljICAS
- KB "How to Check for CRC Errors on an Interface": https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClJVCA0
- KB "How to Check Interface Hardware Counters Including Errors": https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClV7CAK
- KB "How to identify and troubleshoot physical interface error counters on the firewall": https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA14u000000CqHJCA0
- KB "How to check global counters for a specific source and destination IP address": https://knowledgebase.paloaltonetworks.com/articles/en_US/Knowledge/How-to-check-global-counters-f-65794
- KB "How to mitigate an abnormal increase in "flow_rcv_dot1q_tag_err" global counter": https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClvhCAC
- KB "Getting Started: Packet Capture": https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClTJCA0
- KB "How to configure firewall to capture ARP packets on an Interface": https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClfqCAC
- PAN-OS Administrator's Guide 11.1, "Take Packet Captures": https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-admin/monitoring/take-packet-captures
- Web Interface Help 11.1, "Building Blocks for a Custom Packet Capture": https://docs.paloaltonetworks.com/ngfw/help/11-1/monitor/monitor-packet-capture/building-blocks-for-a-custom-packet-capture

### NetScaler (20)

- CLI Command Reference 14.1, "interface" (archived copy): https://web.archive.org/web/20240813193338/https://developer-docs.netscaler.com/en-us/adc-command-reference-int/current-release/network/interface
- CLI Command Reference 14.1, "vlan" (archived copy): https://web.archive.org/web/20241108044106/https://developer-docs.netscaler.com/en-us/adc-command-reference-int/current-release/network/vlan
- CLI Command Reference 14.1, "nstrace" (archived copy): https://web.archive.org/web/20241207122657/https://developer-docs.netscaler.com/en-us/adc-command-reference-int/current-release/basic/nstrace
- CLI Command Reference 13.0, "arp" (archived copy): https://web.archive.org/web/20250429151900/https://developer-docs.netscaler.com/en-us/adc-command-reference-int/13/network/arp
- CLI Command Reference 13.0, "bridgetable" (archived copy): https://web.archive.org/web/20250619222805/https://developer-docs.netscaler.com/en-us/adc-command-reference-int/13/network/bridgetable
- NetScaler ADC 14.1, "Understanding VLANs": https://docs.netscaler.com/us/en/citrix-adc/current-release/networking/interfaces/understanding-vlans.html
- NetScaler ADC 14.1, "Configure network interfaces": https://docs.netscaler.com/en-us/citrix-adc/current-release/networking/interfaces/configuring-network-interfaces.html
- NetScaler ADC 14.1, "Configuring NSVLAN": https://docs.netscaler.com/en-us/citrix-adc/current-release/networking/interfaces/configuring-nsvlan.html
- NetScaler ADC 14.1, "Configure allowed VLAN list": https://docs.netscaler.com/en-us/citrix-adc/current-release/networking/interfaces/configure-allowed-vlan-list.html
- NetScaler ADC 14.1, "Best practices for network configurations": https://docs.netscaler.com/en-us/citrix-adc/current-release/networking/best-practices-network-configurations.html
- NetScaler ADC 14.1, "How to record a packet trace on NetScaler": https://docs.netscaler.com/en-us/citrix-adc/current-release/system/troubleshooting-citrix-adc/how-to-record-a-packet-trace-on-citrix-adc.html

### Fortinet (21)

- FortiOS 7.4.0 Administration Guide, "Interface MTU packet size": https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/596096/interface-mtu-packet-size
- FortiOS 7.4.0 Administration Guide, "VLAN": https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/402940/vlan
- FortiOS 7.4.0 Administration Guide, "QinQ 802.1Q in 802.1ad": https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/78126
- FortiOS 7.4.4 CLI Reference, "config system interface": https://docs.fortinet.com/document/fortigate/7.4.4/cli-reference/317104469/config-system-interface
- FortiOS 7.4.0 Administration Guide, "Displaying detail Hardware NIC information": https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/306050/displaying-detail-hardware-nic-information
- FortiOS 7.4.0 Administration Guide, "ARP table": https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/473534/arp-table
- FortiOS 7.4.0 Administration Guide, "Performing a sniffer trace or packet capture": https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/680228/performing-a-sniffer-trace-or-packet-capture
- FortiOS 7.4.0 Hardware Acceleration, "diagnose hardware deviceinfo nic (number of packets dropped by an interface)": https://docs.fortinet.com/document/fortigate/7.4.0/hardware-acceleration/90160/diagnose-hardware-deviceinfo-nic-interface-name-number-of-packets-dropped-by-an-interface
- FortiOS 6.4.0 New Features, "VLAN DEI bit": https://docs.fortinet.com/document/fortigate/6.4.0/new-features/298422

## Physical layers

22. IEEE 802.3 Ethernet Working Group: https://www.ieee802.org/3/index.html, archive https://www.ieee802.org/3/archive.html, task forces P802.3dj https://www.ieee802.org/3/dj/index.html, 802.3df https://www.ieee802.org/3/df/index.html, 802.3dk https://www.ieee802.org/3/dk/index.html, 802.3da https://www.ieee802.org/3/da/index.html, maintenance request 1066 https://www.ieee802.org/3/maint/requests/maint_1066.pdf
23. TIA FOTC, IEEE 802.3 standards update: https://www.tiafotc.org/ieee-802-3-ethernet-standards-update/singlemode-standards-update/, https://www.tiafotc.org/ieee-802-3-ethernet-standards-update/multimode-standards-update/
24. Wikipedia, Ethernet physical layer (cross-check only): https://en.wikipedia.org/wiki/Ethernet_physical_layer

## Advanced behaviour and troubleshooting

25. NIST National Vulnerability Database, CVE-2003-0001 (Etherleak: Ethernet drivers that pad frames with leftover memory): https://nvd.nist.gov/vuln/detail/CVE-2003-0001
26. Linux kernel documentation, Netdev features (offloads reported by ethtool, rx-fcs, VLAN tag offload): https://www.kernel.org/doc/Documentation/networking/netdev-features.txt
27. Wireshark User's Guide, §7.10 Checksums (checksum offloading): https://www.wireshark.org/docs/wsug_html_chunked/ChAdvChecksums.html
28. Cisco, IP Addressing Configuration Guide, IOS XE 17.x, Address Resolution Protocol (ARP cache timeout): https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/ip-addressing/b-ip-addressing/m_arp-config-arp-0.html
29. Cisco, document 23563, Unicast Flooding in Switched Campus Networks (asymmetric routing): https://www.cisco.com/c/en/us/support/docs/switches/catalyst-6000-series-switches/23563-143.html
30. Cisco, document 24062, Understanding Rapid Spanning Tree Protocol (802.1w): https://www.cisco.com/c/en/us/support/docs/lan-switching/spanning-tree-protocol/24062-146.html
31. Cisco Nexus 9000 Series NX-OS Layer 2 Switching Configuration Guide, Release 10.5(x), Configuring Switching Modes (cut-through and store-and-forward): https://www.cisco.com/c/en/us/td/docs/dcn/nx-os/nexus9000/105x/configuration/layer-2-switching/cisco-nexus-9000-series-nx-os-layer-2-switching-configuration-guide-105x/m-configuring-switching-modes.html
32. Cisco, document 217554, Understand Cyclic Redundancy Check Errors on Nexus Switches (stomped CRC): https://www.cisco.com/c/en/us/support/docs/ios-nx-os-software/nx-os-software/217554-understand-cyclic-redundancy-check-crc.html
