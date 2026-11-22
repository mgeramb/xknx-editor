# Device Links Proposal

A UX proposal for seeing all devices of a project and their links at once, as the successor of the Bus Diagram's Links view.

**Status (2026-11-22):** concept and clickable prototype are done. The design is **not approved yet** and the implementation is postponed; nothing in the editor has changed. The choices below are the proposal as prototyped.

## Files

| File | Content |
| --- | --- |
| `README.md` | Analysis, concept, rules, test results and implementation plan |
| `prototype.html` | The clickable prototype without data; its texts are German, as in the GUI redesign |
| `build_prototype.py` | Puts a project's data into the prototype |
| `Entwurf.local.html` | The built prototype, ignored by Git |

## Build the Prototype

```bash
uv run python docs/design/device-links/build_prototype.py <project.xknx>
```

This writes `Entwurf.local.html`, a single offline file. It contains the project's names, so do not commit or publish it. The project is only read. Flags and group object names come from the project's device snapshots, so open and save the project in the editor once before.

## The Problem

Today's Links view (`bus_diagram/flow.py`, `links_view.py`) draws every group address as a node between sending and receiving devices. The proposal was measured with a real reference project, which is not part of the repository: 57 devices, 771 group addresses, 2,414 links.

| Today's Links view, whole project | Value |
| --- | --- |
| Height | about 16,200 px |
| Lines | 1,814 |
| Crossings (lines taken as straight) | about 281,600 |
| Median vertical run of a line | 2,100 px, so the other end is off screen |
| Height for the busiest single device | 7,740 px |

Every device is drawn twice (sending and receiving), and its place changes with each scope. The view works well for one channel or one group address. It is no overview.

What makes such a project hard to draw:

- A few central devices (bridge, logic, actuators, room controllers) link with almost everything. The busiest has over 200 addresses.
- Most relations go both ways, as a command has its status.
- A few collective signals (time, day/night, all off) connect up to 22 devices each and add many pairs that say nothing about who works with whom.
- Distribution boards hold over a third of the devices, so grouping by room alone gives one huge group.

## Principles

1. **Devices are the map, group addresses are the detail.** A project has far fewer devices than addresses.
2. **Stable places.** Rooms stand outside, distribution boards in the middle. Selecting, filtering and folding never move a place to another column.
3. **Lines on demand.** At rest only bundles; a hover previews, a click holds.
4. **Collective signals are listed, not drawn.**
5. **Direction is never color alone.** Arrow heads and the arrows in the inspector repeat it.

## Levels

| Level | Question | Shows |
| --- | --- | --- |
| Overview | Who is there, who works with whom? | All devices by place; bundles at rest, the partners with the number of shared addresses on selection |
| Device, function, connection | What does this channel work with? | The same map narrowed, with functions and partners in the inspector |
| Signal Path | Over which address exactly? | Senders, addresses and receivers of the selection only |
| Matrix | Where are clusters and gaps? | Sender by receiver, without lines |

The "Heute" tab of the prototype redraws today's layout for comparison and is not part of the proposal.

## Specification

### Layout of the Overview

- One card per space that holds devices, in the order of the building tree, with a card for devices without a space at the end.
- Spaces of the type distribution board form the middle column. The others are split into a left and a right column of about equal height; the split is computed from all devices, whatever is folded or hidden.
- A device is one row: individual address and its name without the leading room name, which the card already says. Outside its card (inspector, Signal Path) it has its full name.
- The row height follows the height available, from 17 to 30 px.
- A card folds to one row and its lines merge. "Rooms only" folds all.

### Lines

| Situation | Drawn |
| --- | --- |
| Nothing selected | One neutral bundle per room and device in the middle, wider and stronger with more addresses. Room to room and lines within the boards appear on selection. |
| Device, room or function selected | One line per partner, the others dimmed, with the number of shared addresses at the partner |
| Group address selected | Its senders to its receivers, also for a collective signal |
| Direction | Orange: the selection sends. Blue: it receives. Neutral with two arrow heads: both. |
| Room to room across the middle | Routed above the middle column, never behind a device it does not link with |
| Same column | An arc in the gap beside it |

### Meaning of a Link

- Sending and receiving as in `project_hubs`: Transmit on the sending link sends, Write or Update receives, both only with Communication.
- Two devices are linked when one sends on an address the other receives on. Two receivers of one address are not linked with each other.
- A collective signal is an address with eight or more devices. It is listed in the inspector and drawn when switched on or selected.

### Interaction

- Hover previews while nothing is selected; a selection stays until Esc, "Alles zeigen" or a click on the background.
- A click on a partner or a line shows the connection with its addresses per direction; a click on an address shows its group objects.
- Back (button or Backspace) returns to the state before.
- Signal Path folds more than 18 addresses into middle groups, which open on click.
- Filters: trade (the names of the middle groups), main group, collective signals, hidden devices (e.g. test or retired ones).
- The search finds places, devices and group addresses.
- The inspector lists the ten busiest functions of a device with many, the others on request.

### Small Screens and Large Projects

- Phone: one column without lines, partners stay highlighted, the inspector is a sheet below.
- Large projects: from about 80 devices the places should start folded (an assumption, not tried).

## Results with the Reference Project

| Check | Result |
| --- | --- |
| All 57 devices without scrolling | Yes at 1600×1000, 1440×900, 1280×720 and 1024×768 |
| Lines at rest | 94 bundles instead of 1,814 lines |
| Most lines for one selected device | 31 |
| Every device selected, Overview and Signal Path | No script errors, at most about 20 ms per device |
| Partner and address counts | Same as a separate count from the same flags, for all 57 devices |

Tested in headless Chrome. Not tested: real touch input, screen readers, projects with hundreds of devices, and how it performs in ImGui.

## Implementation Plan

Read `apps/editor-gui/AGENTS.md` and `apps/editor-gui/docs/architecture.md` first. The paths are below `apps/editor-gui/src/editor_gui/`.

- [ ] **0. Approval:** show the artboards (the prototype's Overview, selection, Signal Path, Matrix and phone layout) and wait for the maintainer's explicit approval. No code before it; a later change of the design needs a new one.
- [ ] **1. Model:** a pure `build_map` in `plugins/bus_diagram/flow.py` beside `build_flow`, from `project_hubs` and the space tree: places, columns, bundles, partners. Test it without imgui: stable columns, directions, collective signals, devices without a space, projects without boards.
- [ ] **2. Overview:** a new `plugins/bus_diagram/map_view.py` on the helpers of `canvas.py` (palette, zoom, drag), as the default of the Links mode. Physical and Building stay.
- [ ] **3. Signal Path:** narrow the existing `LinkView` and `build_flow` to the selection, with folding into middle groups. "Show in Bus Diagram" keeps working.
- [ ] **4. Channels:** the real channels from `com_object_channels` (loaded in the background, as today) in place of the names guessed in the prototype.
- [ ] **5. Inspector:** in the workbench the app's inspector shows the selection; in the docking layout the diagram has its own side panel.
- [ ] **6. Findings:** take them from the Health plugin's checks, see below.
- [ ] **7. Matrix:** last, as it is independent of the others.
- [ ] **8. Browser and touch:** everything that a hover shows also by tap, 44 px rows on touch, pinch zoom, keyboard movement between devices.
- [ ] **9. MCP:** extend `project_link_graph` (`plugins/mcp/tools/details.py`) or add a read tool for partners and bundles, with tests.
- [ ] **10. Texts:** all languages; update the feature inventory in `apps/editor-gui/AGENTS.md`.

## Differences of the Prototype from What to Build

- **Findings are simplified.** The prototype calls an address "ohne Sender" when no object transmits on it. The Health plugin (`_check_group_addresses`) also accepts read responders, unresolved objects and external senders such as Home Assistant, and leaves out inactive objects. Its rule applies; the prototype's counts can contain false alarms. "Ohne Empfänger" and "Nur an einem Gerät" have no such check yet and need the same care.
- **Functions are guessed** from the group object names.
- **Application defaults come from the snapshots**, not from evaluated applications.
- **The colors are the redesign's tokens**, not today's `theme.py`. The orange for sending is new and needs a token.

## Open Questions

- What stands in the middle when a project has no distribution boards: the devices with the most partners, or ones the user pins?
- The trade filter relies on consistently named middle groups. Should datapoint types or the project's trades stand in otherwise?
- Are hidden devices and the threshold of collective signals saved per project or per user?
- Should a device that is named or marked as retired but still linked become a Health finding?
- Is the Matrix needed in the first release?
