# Ethernet sources

Hierarchy: standards (IEEE, RFC, IANA) > vendor documentation > books/whitepapers.
Accessed 24-25 October 2026. Same list as section 8 (Sources) of `index.html`.

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

### Cisco
- IOS XE 17.9 (Catalyst 9300) Interface & Hardware CG, Configuring System MTU: https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/configuration_guide/int_hw/b_179_int_and_hw_9300_cg/configuring_system_mtu.html
- Same guide, Configuring Interface Characteristics (802.3x): https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/configuration_guide/int_hw/b_179_int_and_hw_9300_cg/configuring_interface_characteristics.html
- VLAN CG 17.9, Configuring VLAN Trunks: https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/configuration_guide/vlan/b_179_vlan_9300_cg/configuring_vlan_trunks.html
- Network Management CG 17.9, Configuring Packet Capture: https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/configuration_guide/nmgmt/b_179_nmgmt_9300_cg/configuring_packet_capture.html
- TAC 217233 (MTU on Catalyst 9000): https://www.cisco.com/c/en/us/support/docs/switches/catalyst-9500-series-switches/217233-troubleshoot-mtu-on-catalyst-9000-series.html
- TAC 217726 (QinQ and L2PT on Catalyst 9000): https://www.cisco.com/c/en/us/support/docs/switches/catalyst-9300-switch/217726-configure-and-verify-and-troubleshoot-qi.html
- TAC 218397 (port flaps on Catalyst 9000): https://www.cisco.com/c/zh_cn/support/docs/switches/catalyst-9500-series-switches/218397-troubleshoot-port-flaps-on-catalyst-9000.html
- NX-OS 10.4 Interfaces CG, Basic Interface Parameters: https://www.cisco.com/c/en/us/td/docs/dcn/nx-os/nexus9000/104x/configuration/interfaces/cisco-nexus-9000-series-nx-os-interfaces-configuration-guide-release-104x/m_configuring_basic_interface_parameters_93x.html
- NX-OS 10.4 Interfaces CG, Q-in-Q VLAN Tunnels: https://www.cisco.com/c/en/us/td/docs/dcn/nx-os/nexus9000/104x/configuration/interfaces/cisco-nexus-9000-series-nx-os-interfaces-configuration-guide-release-104x/m_configuring_q-in-q_vlan_tunnels_9x.html
- NX-OS 10.3 QoS CG, Link Level Flow Control: https://www.cisco.com/c/en/us/td/docs/dcn/nx-os/nexus9000/103x/configuration/qos/cisco-nexus-9000-nx-os-quality-of-service-configuration-guide-103x/m-configuring-llfc.html
- TAC 220133 (Nexus 9000 CRC): https://bxin.cisco.com/c/en/us/support/docs/ios-nx-os-software/nx-os-software/220133-troubleshoot-nexus-9000-interface-crc-er.pdf
- TAC 218096 (Nexus cheat sheet, ethanalyzer): https://cisco.com/c/en/us/support/docs/switches/nexus-9000-series-switches/218096-troubleshoot-nexus-cheat-sheet-for-begin.pdf
- IOS XR 7.9 (ASR 9000), Configuring 802.1Q VLAN Interfaces: https://www.cisco.com/c/en/us/td/docs/routers/asr9000/software/asr9k-r7-9/configuration/guide/b-interfaces-hardware-component-cg-asr9000-79x/configuring-802-1q-vlan-interfaces.html

### Check Point
- R81.20 Gaia Admin Guide, Physical Interfaces: https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_Gaia_AdminGuide/Content/Topics-GAG/Physical-Interfaces.htm
- R81.20 Gaia Admin Guide, VLAN Interfaces: https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_Gaia_AdminGuide/Content/Topics-GAG/VLAN-Interfaces.htm
- R81.20 Gaia Admin Guide, ARP in Gaia Clish: https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_Gaia_AdminGuide/Content/Topics-GAG/ARP-Gaia-Clish.htm
- sk141412 (cppcap): https://support.checkpoint.com/results/sk/sk141412
- R82 CLI Reference, cppcap: https://sc1.checkpoint.com/documents/R82/WebAdminGuides/EN/CP_R82_CLI_ReferenceGuide/Content/Topics-CLIG/FWG/cppcap.htm
- R81.20 CLI Reference, fw monitor: https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_CLI_ReferenceGuide/Content/Topics-CLIG/FWG/fw-monitor.htm
- Not documented officially: Q-in-Q, 802.3x flow control, expert-mode L2 error counters.

### F5
- TMSH Reference (latest = 17.0), net vlan / net interface / net arp: https://clouddocs.f5.com/cli/tmsh-reference/latest/modules/net/net_vlan.html, https://clouddocs.f5.com/cli/tmsh-reference/latest/modules/net/net_interface.html, https://clouddocs.f5.com/cli/tmsh-reference/latest/modules/net/net_arp.html
- TMOS Routing Administration 14.1.0, About double tagging: https://techdocs.f5.com/en-us/bigip-14-1-0/big-ip-tmos-routing-administration-14-1-0/vlans-vlan-groups-and-vxlan/about-vlans/about-vlans-and-interfaces/about-tagged-interfaces/about-double-tagging.html
- TMOS Routing Administration 14.1.0, About flow control: https://techdocs.f5.com/en-us/bigip-14-1-0/big-ip-tmos-routing-administration-14-1-0/interfaces/interface-properties/about-flow-control.html
- Agility Labs (training), tcpdump switches: https://clouddocs.f5.com/training/community/adc/html/class4/module1/lab01.html, https://clouddocs.f5.com/training/community/adc/html/class4/module1/lab03.html

### Palo Alto Networks
- PAN-OS 11.1, Configure Session Settings: https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-networking-admin/session-settings-and-timeouts/configure-session-settings
- Web Interface Help 11.1, Layer 3 Subinterface: https://docs.paloaltonetworks.com/ngfw/help/11-1/network/network-interfaces/layer-3-subinterface
- PAN-OS 11.1, Take Packet Captures: https://docs.paloaltonetworks.com/content/techdocs/en_US/pan-os/11-1/pan-os-admin/monitoring/take-packet-captures.html
- PAN-OS 11.1, Protocol Protection: https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-admin/zone-protection-and-dos-protection/zone-defense/zone-protection-profiles/protocol-protection
- KB Jumbo Frame: https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClVaCAK
- KB MTU and MSS from CLI: https://knowledgebase.paloaltonetworks.com/kcsArticleDetail?id=kA10g000000ClLI
- KB CRC errors: https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClJVCA0
- KB hardware counters: https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClV7CAK
- KB global counters: https://knowledgebase.paloaltonetworks.com/articles/en_US/Knowledge/How-to-check-global-counters-f-65794
- KB Getting Started: Packet Capture: https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClTJCA0
- Not documented officially: Q-in-Q, 802.3x flow control, CLI `layer3 units ... tag` syntax.

### NetScaler
- ADC CLI Commands 14.1, interface / vlan / nstrace: https://developer-docs.netscaler.com/en-us/adc-command-reference-int/current-release/network/interface.html, https://developer-docs.netscaler.com/en-us/adc-command-reference-int/current-release/network/vlan.html, https://developer-docs.netscaler.com/en-us/adc-command-reference-int/current-release/basic/nstrace.html
- ADC CLI Commands 13.0, arp / bridgetable: https://developer-docs.netscaler.com/en-us/adc-command-reference-int/13/network/arp.html, https://developer-docs.netscaler.com/en-us/adc-command-reference-int/13/network/bridgetable.html
- Understanding VLANs (14.1): https://docs.netscaler.com/us/en/citrix-adc/current-release/networking/interfaces/understanding-vlans.html
- Not documented officially: Q-in-Q / 802.1ad, separate runt/giant/PAUSE counters.

### Fortinet
- FortiOS 7.4.0 Admin Guide, Interface MTU packet size: https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/596096/interface-mtu-packet-size
- FortiOS 7.4.0 Admin Guide, VLAN: https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/402940/vlan
- FortiOS 7.4.0 Admin Guide, QinQ 802.1Q in 802.1ad: https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/78126
- FortiOS 7.4.0 Admin Guide, QinQ 802.1Q in 802.1Q (VM only): https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/554099
- FortiOS 7.4.0 Admin Guide, Hardware NIC information: https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/306050/displaying-detail-hardware-nic-information
- FortiOS 7.4.0 Admin Guide, Sniffer trace: https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/680228/performing-a-sniffer-trace-or-packet-capture
- FortiOS 7.4.0 Admin Guide, ARP table: https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/473534/arp-table
- CLI Reference 7.4.4, config system interface: https://docs.fortinet.com/document/fortigate/7.4.4/cli-reference/317104469/config-system-interface
- New Features 6.4.3, FortiSwitch flow control: https://docs.fortinet.com/document/fortigate/6.4.0/new-features/359959/add-option-to-enable-flow-control-and-pause-metering-6-4-3
- Not documented officially: 802.3x flow control on FortiGate ports.

## Physical layers

22. IEEE 802.3 Ethernet Working Group: https://www.ieee802.org/3/index.html, archive https://www.ieee802.org/3/archive.html, task forces P802.3dj https://www.ieee802.org/3/dj/index.html, 802.3df https://www.ieee802.org/3/df/index.html, 802.3dk https://www.ieee802.org/3/dk/index.html, 802.3da https://www.ieee802.org/3/da/index.html, maintenance request 1066 https://www.ieee802.org/3/maint/requests/maint_1066.pdf
23. TIA FOTC, IEEE 802.3 standards update: https://www.tiafotc.org/ieee-802-3-ethernet-standards-update/singlemode-standards-update/, https://www.tiafotc.org/ieee-802-3-ethernet-standards-update/multimode-standards-update/
24. Wikipedia, Ethernet physical layer (cross-check only): https://en.wikipedia.org/wiki/Ethernet_physical_layer
