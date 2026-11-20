# GUI Redesign Proposal

A UX redesign proposal for the editor GUI, with clickable prototypes. The texts in the prototypes are German. Nothing in the code has been changed yet.

## Boards

| File | Content |
| --- | --- |
| `project/Main.dc.html` | Clickable prototype of the new layout |
| `project/Analyse.dc.html` | Analysis of the current GUI, design principles, zone diagram, where each of the 22 panels and the menus go |
| `project/Kommunikationsobjekte.dc.html` | Group objects: filters, links, flags, batch GA creation with name templates |
| `project/Gruppenadressen.dc.html` | Group addresses: tree with usage, free ranges, bulk edits, inspector |
| `project/Bus.dc.html` | Bus and monitor: recording, telegrams, bus monitor mode, values, statistics, timeline, bus diagram |
| `project/canvas.json` | Arrangement of the boards on the canvas |

## Concept in Short

- **Fixed zones instead of free docking:** top bar (project, search and command palette ⌘P, pending changes, connection), activity rail (Project, Catalog, Bus, Check, Tools), navigator (Building | Topology | Group Addresses), workspace, context inspector (device, group object or group address), a bottom drawer that can be collapsed (operations, telegrams, log, history) and a status bar.
- **One way to show a panel**, not three (the ▾ per dock, View › Windows and × on the tab).
- **The device parameter editor stays as it is**, because the device's configuration defines it.
- Programming runs from one split button per device with all scopes and a queue in the drawer.

## Viewing the Files

The `.dc.html` files are Claude Design sources. They need the Claude Design runtime (`support.js`), which is not part of this repository, so they do not open on their own in a browser. To view them, publish the `project/` folder as a Claude Design artifact.

`project/_blob/` holds the two screenshots of the current editor that `Analyse.dc.html` refers to as `/_blob/<id>`.

## Open Points

- The devices in the prototypes come from a real project; values, group addresses and warnings are partly invented.
- Not designed yet: programming in detail, and the Check area.
