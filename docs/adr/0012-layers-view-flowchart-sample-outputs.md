# ADR 0012: Layers view for the model page, flowchart, documented sample outputs

- Status: accepted
- Date: 2026-11-12

## Context

The OSI and TCP/IP page owns no message type: its frames (a DNS query, an HTTP request, a
TCP SYN) are there to show where each layer sits. Shown like every other packet (bit
diagram, Wireshark tree, hex dump, guided tour, list of 40 fields), they repeated the
Ethernet and IPv4 pages and hid the one thing to see. The owner asked for a lighter chapter,
for network icons in the diagrams, for an end-to-end journey showing what each device reads
and rewrites, for the expected output under each verification command and for a
troubleshooting chart that reads like a flowchart.

## Decision

- **Layers view.** A packet article with `data-view="layers"` shows the bit diagram coloured
  by OSI layer (the builder gives each field its `osi` number and a `stack`), a layer strip
  (one box per protocol with its size and the field naming the next layer) and the detail
  panel. It has no tree, hex dump, guided tour or field list. Only a page that teaches the
  layers and owns no message type may use it, and it links to the page of each protocol,
  where the same headers have both mandatory views. Every other page keeps the rule "bit
  diagram and Wireshark tree, always".
- **Flowchart** (`ol.flow`). One entry, one question per decision, "yes" always goes down,
  "no" always leaves to the side towards a box that names the causes and sends the reader
  back to the question, one end. It is an ordered list drawn with CSS, not an image: it
  reflows at 360 px, prints, and is read in order by a screen reader. The older `ol.dtree`
  stays valid.
- **Sample outputs** (`details.outs`). Under a vendor's verification block, one box per
  command whose output the vendor documents: the output as documented (shortened, addresses
  replaced by documentation values), how to read it, the source. A command without a
  documented output is listed as such; no output is invented.
- **Icons in page diagrams.** `tools/page-icons.py` embeds the unaltered Cisco topology
  icons a page lists in its `<!--ICONS:...-->` marker as one hidden sprite;
  `check_pages.py` fails if the sprite differs from the tool's output.

Rejected: keeping both views and collapsing them (the chapter stays as long); an SVG
flowchart (does not reflow on a phone, text is harder to translate and to read aloud);
sample outputs written from memory (contrary to the vendor rules).

## Consequences

- The shared blocks of the template grow; every page receives them through
  `tools/sync-shared.py` without changing its own content.
- The topics removed from the model page (cross-layer protocols, tunnels, MTU and MSS,
  interactions between layers) are due as separate articles.
- The page embeds Cisco icons: it is listed with the home page in `REUSE.toml`.
