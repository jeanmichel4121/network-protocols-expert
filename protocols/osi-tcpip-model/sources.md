# OSI and TCP/IP models: sources

Hierarchy: standards (ITU-T, ISO/IEC, RFC, IEEE, IANA) > vendor documentation > references.
Accessed 6 November 2026. Same list and numbering as the Sources chapter of `index.html`.

1. **ITU-T Recommendation X.200 (07/1994) | ISO/IEC 7498-1:1994, Open Systems Interconnection, Basic Reference Model: The basic model**: clause 5 (layered architecture: entities, services, (N)-PDU, (N)-SDU, (N)-SAP), clause 6 (the seven layers), clause 7 (each layer in detail). Earlier editions: ISO 7498:1984, CCITT X.200 (10/1984) and X.200 (11/1988), both superseded. https://www.itu.int/rec/T-REC-X.200-199407-I
2. **RFC 1122, Requirements for Internet Hosts: Communication Layers (STD 3)**: §1.1.3 (Internet protocol suite: application, transport, internet and link layers), §2.3.2 (ARP, in the link layer chapter), §2.3.2.1 (ARP cache validation: mechanisms, timeout on the order of a minute), §3.2.1.7 (Time to Live: configurable, no value), §3.3.1 (local or remote destination). https://www.rfc-editor.org/rfc/rfc1122
3. **RFC 1123, Requirements for Internet Hosts: Application and Support (STD 3)**: §1 (application layer of the Internet suite). https://www.rfc-editor.org/rfc/rfc1123
4. **RFC 3439, Some Internet Architectural Guidelines and Philosophy**: §3 (Layering Considered Harmful). https://www.rfc-editor.org/rfc/rfc3439
5. **RFC 791, Internet Protocol (STD 5)**: §1.4, §2.2, §3.1 (Protocol field, Time to Live). https://www.rfc-editor.org/rfc/rfc791
6. **RFC 894, A Standard for the Transmission of IP Datagrams over Ethernet Networks (STD 41)**: EtherType 0x0800. https://www.rfc-editor.org/rfc/rfc894
7. **RFC 826, An Ethernet Address Resolution Protocol (STD 37)**: whole document. https://www.rfc-editor.org/rfc/rfc826
8. **RFC 768, User Datagram Protocol (STD 6)**: whole document. https://www.rfc-editor.org/rfc/rfc768
9. **RFC 9293, Transmission Control Protocol (STD 7)**: §3.1 (header format), §3.1 (4 reserved bits), §3.5 (three-way handshake), §3.5.2 (reset generation), §3.7.1 (Maximum Segment Size option). https://www.rfc-editor.org/rfc/rfc9293
10. **RFC 9768, More Accurate Explicit Congestion Notification (AccECN) Feedback in TCP**: §3.1 (AE flag, taken from the reserved bits of RFC 9293). https://www.rfc-editor.org/rfc/rfc9768
11. **RFC 1035, Domain Names: Implementation and Specification (STD 13)**: §4.1.1 (header, without the AD and CD bits), §4.1.2 (question section), §4.2.1 (UDP usage). https://www.rfc-editor.org/rfc/rfc1035
12. **RFC 1812, Requirements for IP Version 4 Routers**: §5.2.1 (forwarding algorithm), §5.3.1 (Time to Live). https://www.rfc-editor.org/rfc/rfc1812
13. **RFC 3022, Traditional IP Network Address Translator (Traditional NAT)**: §2.2 (NAPT), §4.1 (header and checksum adjustment). https://www.rfc-editor.org/rfc/rfc3022
14. **RFC 3031, Multiprotocol Label Switching Architecture**: §3.9 (label stack), §3.10 (NHLFE); encoding in RFC 3032. https://www.rfc-editor.org/rfc/rfc3031
15. **RFC 7348, Virtual eXtensible Local Area Network (VXLAN)**: §5 (frame format). https://www.rfc-editor.org/rfc/rfc7348
16. **RFC 8446, The Transport Layer Security (TLS) Protocol Version 1.3**: §1, §5 (record protocol). https://www.rfc-editor.org/rfc/rfc8446
17. **RFC 9000, QUIC: A UDP-Based Multiplexed and Secure Transport**: §1 (overview); assigns no UDP port. https://www.rfc-editor.org/rfc/rfc9000
18. **RFC 9110, HTTP Semantics (STD 97)**: §3.7 (intermediaries), §4.2.2 (https scheme, default port 443). https://www.rfc-editor.org/rfc/rfc9110
19. **RFC 1191, Path MTU Discovery**: §3, §4. https://www.rfc-editor.org/rfc/rfc1191
20. **IEEE Std 802-2014, IEEE Standard for Local and Metropolitan Area Networks: Overview and Architecture**: reference model: LLC and MAC sublayers, physical layer. https://standards.ieee.org/ieee/802/4158/
21. **IANA, Assigned Internet Protocol Numbers**: values 1, 6, 17. https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml
22. **IANA, Service Name and Transport Protocol Port Number Registry**: ports 53, 443 (https: 443/tcp and 443/udp). https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml
23. **Wireshark Display Filter Reference**: eth, ip, udp, tcp, dns. https://www.wireshark.org/docs/dfref/
24. **tools/packet-builder.py**: samples osi-dns and osi-syn (computed lengths and checksums, cross-decoded with scapy).
25. **Cisco: Command Reference, Cisco IOS XE Cupertino 17.9.x (Catalyst 9300 Switches)**: Interface and Hardware Commands: show interfaces, show interfaces transceiver. https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/command_reference/b_179_9300_cr/interface_and_hardware_commands.html
26. **Cisco: Command Reference, Cisco IOS XE Cupertino 17.9.x (Catalyst 9300 Switches)**: System Management Commands: show mac address-table. https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/command_reference/b_179_9300_cr/system_management_commands.html
27. **Cisco: Troubleshoot Mac Address Table Manager on Catalyst 9000 Switches (TAC 222060)**: IOS XE 16.x and 17.x; section Check IP ARP and Mac Address of the Destination Device. https://www.cisco.com/c/en/us/support/docs/switches/catalyst-9300-series-switches/222060-troubleshoot-mac-address-table-manager-o.html
28. **Cisco: Cisco IOS IP Routing: Protocol-Independent Command Reference**: Cisco IOS XE 17; IP Routing Protocol-Independent Commands S through T: show ip route. https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/iproute_pi/command/iri-cr-book/iri-cr-s1.html
29. **Cisco: Understand the Extended Ping and Extended Traceroute Commands (TAC 13730)**: Cisco IOS Software; extended ping and extended traceroute dialogs. https://www.cisco.com/c/en/us/support/docs/ip/routing-information-protocol-rip/13730-ext-ping-trace.html
30. **Cisco: Command Reference, Cisco IOS XE Cupertino 17.9.x (Catalyst 9300 Switches)**: IP Addressing Services Commands: show ip ports all. https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/command_reference/b_179_9300_cr/ip_addressing_services_commands.html
31. **Cisco: Network Management Configuration Guide, Cisco IOS XE Cupertino 17.9.x (Catalyst 9300 Switches)**: Configuring Packet Capture. https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/configuration_guide/nmgmt/b_179_nmgmt_9300_cg/configuring_packet_capture.html
32. **Cisco: Cisco Nexus 9000 Series NX-OS Command Reference (Show Commands), Release 10.4(x)**: I Show Commands: show interface, show interface counters errors, show ip arp, show ip route. https://www.cisco.com/c/en/us/td/docs/dcn/nx-os/nexus9000/104x/command-reference/show/b_n9k_show_commands_104x/m_i_showcmds.html
33. **Cisco: Cisco Nexus 9000 Series NX-OS Command Reference (Show Commands), Release 10.4(x)**: M Show Commands: show mac address-table. https://www.cisco.com/c/en/us/td/docs/dcn/nx-os/nexus9000/104x/command-reference/show/b_n9k_show_commands_104x/m_m_showcmds.html
34. **Cisco: Cisco Nexus 9000 Series NX-OS Command Reference (Show Commands), Release 10.4(x)**: S Show Commands: show sockets connection. https://www.cisco.com/c/en/us/td/docs/dcn/nx-os/nexus9000/104x/command-reference/show/b_n9k_show_commands_104x/m_s_showcmds.html
35. **Cisco: Cisco Nexus 9000 Series NX-OS Troubleshooting Guide, Release 10.4(x)**: Troubleshooting Tools and Methodology: Using Ping, Using Traceroute, Using Ethanalyzer. https://www.cisco.com/c/en/us/td/docs/dcn/nx-os/nexus9000/104x/troubleshooting/cisco-nexus-9000-series-nx-os-troubleshooting-guide-104x/m-troubleshooting-tools-and-methodology.html
36. **Check Point: Gaia R81.20 Administration Guide**: Physical Interfaces; Interface Link Status; Monitoring Transceivers. https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_Gaia_AdminGuide/Content/Topics-GAG/Physical-Interfaces.htm
37. **Check Point: Gaia R81.20 Administration Guide**: Monitoring Transceivers. https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_Gaia_AdminGuide/Content/Topics-GAG/Monitoring-Transceivers.htm
38. **Check Point: Gaia R81.20 Administration Guide**: Configuring ARP in Gaia Clish. https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_Gaia_AdminGuide/Content/Topics-GAG/ARP-Gaia-Clish.htm
39. **Check Point: Gaia R81.20 Advanced Routing Administration Guide**: Routing Monitor. https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_Gaia_Advanced_Routing_AdminGuide/Content/Topics-GARG/Routing-Monitor.htm
40. **Check Point: Gaia R81.20 Administration Guide**: Configuring IPv4 Static Routes in Gaia Clish. https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_Gaia_AdminGuide/Content/Topics-GAG/IPv4-Static-Routes-Gaia-Clish.htm
41. **Check Point: Gaia R81.20 Administration Guide**: Roles: list of extended commands (ping, traceroute). https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_Gaia_AdminGuide/Content/Topics-GAG/Roles-Extended-Commands.htm
42. **Check Point: R81.20 CLI Reference Guide**: fw ctl conntab. https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_CLI_ReferenceGuide/Content/Topics-CLIG/FWG/fw-ctl-conntab.htm
43. **Check Point: R81.20 CLI Reference Guide**: cpstat. https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_CLI_ReferenceGuide/Content/Topics-CLIG/FWG/cpstat.htm
44. **Check Point: R81.20 CLI Reference Guide**: fw monitor. https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_CLI_ReferenceGuide/Content/Topics-CLIG/FWG/fw-monitor.htm
45. **F5: TMSH Reference v17.0.0**: net interface. https://clouddocs.f5.com/cli/tmsh-reference/latest/modules/net/net_interface.html
46. **F5: TMSH Reference v17.0.0**: net fdb vlan. https://clouddocs.f5.com/cli/tmsh-reference/latest/modules/net/net_fdb_vlan.html
47. **F5: TMSH Reference v17.0.0**: net arp. https://clouddocs.f5.com/cli/tmsh-reference/latest/modules/net/net_arp.html
48. **F5: TMSH Reference v17.0.0**: net route (lookup option). https://clouddocs.f5.com/cli/tmsh-reference/latest/modules/net/net_route.html
49. **F5: K000141350, bind: Cannot assign requested address message when trying to ping from source IP address**: ping -I with a non-floating self IP. https://my.f5.com/manage/s/article/K000141350
50. **F5: K53851362, Displaying and deleting BIG-IP connection table entries from the command line**: show sys connection filters. https://my.f5.com/manage/s/article/K53851362
51. **F5: K000134557, How to display Virtual Servers/Pools/Nodes and availability in CLI**: show ltm virtual detail recursive. https://my.f5.com/manage/s/article/K000134557
52. **F5: K411, Overview of packet tracing with the tcpdump utility**: interface 0.0, filters, -w. https://my.f5.com/manage/s/article/K411
53. **Palo Alto Networks: KB, Identify configured Interface MTU**: PAN-OS; show interface output. https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000CljICAS
54. **Palo Alto Networks: KB, How to Check Interface Hardware Counters Including Errors**: PAN-OS; show system state filter. https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClV7CAK
55. **Palo Alto Networks: PAN-OS Device Telemetry Metrics Reference**: MAC Address Table and ARP Table: equivalent CLI commands. https://docs.paloaltonetworks.com/pan-os/u-v/pan-os-device-telemetry-metrics-reference/device-health-and-performance/metric-dt-dhp-116
56. **Palo Alto Networks: PAN-OS 11.1 CLI Quick Start**: CLI Cheat Sheet: Networking (General Routing, Troubleshooting). https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-cli-quick-start/cli-cheat-sheets/cli-cheat-sheet-networking
57. **Palo Alto Networks: KB, How to Perform FIB Lookup for a Particular Destination**: PAN-OS; test routing fib-lookup. https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClYJCA0
58. **Palo Alto Networks: KB, How to Filter Active Sessions from the CLI**: PAN-OS; show session all filter, show session id. https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClFECA0
59. **Palo Alto Networks: KB, Getting Started: Packet Capture**: PAN-OS; packet-diag filters and capture. https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClTJCA0
60. **NetScaler: ADC CLI Commands 14.1**: interface (archived copy, 13 August 2024). https://web.archive.org/web/20240813193338/https://developer-docs.netscaler.com/en-us/adc-command-reference-int/current-release/network/interface
61. **NetScaler: ADC CLI Commands 14.1**: bridgetable (archived copy, 21 January 2025). https://web.archive.org/web/20250121120723/https://developer-docs.netscaler.com/en-us/adc-command-reference-int/current-release/network/bridgetable
62. **NetScaler: ADC CLI Commands 14.1**: arp (archived copy, 13 August 2024). https://web.archive.org/web/20240813180758/https://developer-docs.netscaler.com/en-us/adc-command-reference-int/current-release/network/arp
63. **NetScaler: NetScaler 14.1 documentation**: Configuring Static Routes: show route. https://docs.netscaler.com/en-us/citrix-adc/current-release/networking/ip-routing/configuring-static-routes.html
64. **NetScaler: ADC CLI Commands 14.1**: ping (archived copy, 8 March 2026). https://web.archive.org/web/20260308071932/https://developer-docs.netscaler.com/en-us/adc-command-reference-int/current-release/utility/ping
65. **NetScaler: ADC CLI Commands 14.1**: traceroute (archived copy, 12 August 2024). https://web.archive.org/web/20240812042534/https://developer-docs.netscaler.com/en-us/adc-command-reference-int/current-release/utility/traceroute
66. **NetScaler: ADC CLI Commands 13.0**: ns connectiontable (archived copy, 18 June 2025; no copy of the 14.1 page is available). https://web.archive.org/web/20250618052400/https://developer-docs.netscaler.com/en-us/adc-command-reference-int/13/ns/ns-connectiontable
67. **NetScaler: ADC CLI Commands 14.1**: lb vserver (archived copy, 12 May 2026). https://web.archive.org/web/20260512215958/https://developer-docs.netscaler.com/en-us/adc-command-reference-int/current-release/lb/lb-vserver
68. **NetScaler: ADC CLI Commands 14.1**: service (archived copy, 4 January 2026). https://web.archive.org/web/20260104073929/https://developer-docs.netscaler.com/en-us/adc-command-reference-int/current-release/basic/service
69. **NetScaler: NetScaler 14.1 documentation**: How to record a packet trace on NetScaler. https://docs.netscaler.com/en-us/citrix-adc/current-release/system/troubleshooting-citrix-adc/how-to-record-a-packet-trace-on-citrix-adc.html
70. **Fortinet: FortiOS 7.4.0 Administration Guide**: Displaying detail Hardware NIC information. https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/306050/displaying-detail-hardware-nic-information
71. **Fortinet: FortiOS 7.4.4 Administration Guide**: Checking the bridging information in transparent mode. https://docs.fortinet.com/document/fortigate/7.4.4/administration-guide/183521/checking-the-bridging-information-in-transparent-mode
72. **Fortinet: FortiOS 7.4.0 Administration Guide**: ARP table. https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/473534/arp-table
73. **Fortinet: FortiOS 7.4.4 Administration Guide**: Routing concepts: viewing the routing table in the CLI, route look-up. https://docs.fortinet.com/document/fortigate/7.4.4/administration-guide/139692/routing-concepts
74. **Fortinet: FortiOS 7.4.4 Administration Guide**: Running ping and traceroute. https://docs.fortinet.com/document/fortigate/7.4.4/administration-guide/982816/running-ping-and-traceroute
75. **Fortinet: FortiOS 7.4.9 CLI Reference**: execute ping-options, execute traceroute-options. https://docs.fortinet.com/document/fortigate/7.4.9/cli-reference/221756471/execute-ping-options
76. **Fortinet: FortiOS 7.4.4 and 7.4.7 Administration Guide**: Using a session table (filters; app= and url_cat= fields on the 7.4.7 page). https://docs.fortinet.com/document/fortigate/7.4.7/administration-guide/562859/using-a-session-table
77. **Fortinet: FortiOS 7.4.0 Administration Guide**: Performing a sniffer trace or packet capture. https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/680228/performing-a-sniffer-trace-or-packet-capture
78. **RFC 4035, Protocol Modifications for the DNS Security Extensions**: §3.2.2 (CD bit), §3.2.3 (AD bit); the two bits were first allocated by RFC 2535 §6.1, now obsolete. https://www.rfc-editor.org/rfc/rfc4035
79. **IANA, Internet Protocol Version 4 (IPv4) Parameters**: IP Time to Live Parameter: recommended default TTL 64 (the value published in the Assigned Numbers series, RFC 1700). https://www.iana.org/assignments/ip-parameters/ip-parameters.xhtml
80. **IEEE Registration Authority, EtherType public listing**: 0800: IPv4. https://standards-oui.ieee.org/ethertype/eth.txt
81. **IANA, Domain Name System (DNS) Parameters**: Resource Record (RR) TYPEs: A = 1; DNS header flags. https://www.iana.org/assignments/dns-parameters/dns-parameters.xhtml
82. **RFC 9114, HTTP/3**: §3.1 (discovering an HTTP/3 endpoint: QUIC connection to the port of the https URI, any UDP port allowed). https://www.rfc-editor.org/rfc/rfc9114
83. **RFC 3032, MPLS Label Stack Encoding**: §2.1 (label stack entry of 4 octets, the shim header). https://www.rfc-editor.org/rfc/rfc3032
84. **IEEE Std 802.1Q-2022, IEEE Standard for Local and Metropolitan Area Networks: Bridges and Bridged Networks**: §8.6 (forwarding process), §8.8 (filtering database: MAC address and VID). https://standards.ieee.org/ieee/802.1Q/10323/
