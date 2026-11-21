# GUI Redesign Proposal

A UX redesign proposal for the editor GUI, with clickable prototypes and a design system. The texts in the prototypes and the design system are German. A first implementation runs behind `XKNX_REDESIGN=1`.

## Boards

| File | Content |
| --- | --- |
| `project/Analyse.dc.html` | Analysis of the current GUI, design principles, zone diagram, where each of the 22 panels and the menus go |
| `project/Main.dc.html` | Clickable prototype of the new layout; responsive, its four modes (wide, mid, narrow, phone) follow the window width as in `KleineBildschirme.dc.html` |
| `project/Kommunikationsobjekte.dc.html` | Group objects: filters, links, flags, batch GA creation with name templates |
| `project/Gruppenadressen.dc.html` | Group addresses: tree with usage, free ranges, bulk edits, inspector |
| `project/Bus.dc.html` | Bus and monitor: recording, telegrams, bus monitor mode, values, statistics, timeline, bus diagram |
| `project/KleineBildschirme.dc.html` | iPad mini (landscape and portrait) and phone, with a switchable prototype and the Jalousieaktor on the iPhone |
| `project/Tastatur.dc.html` | Keyboard: one key for the panels, two-step shortcuts for commands, how the keys are shown |
| `project/canvas.json` | Arrangement of the boards on the canvas, and the linked design system |
| `project/ds/xknxeditor/tokens.json` | Copy of the design system's tokens for the canvas |

## Design System

`design-system/` holds the design system: `README.md` (rules for colors, type, icons, symbols, texts, keyboard, touch, accessibility and the mapping to ImGui), `tokens.json` (colors for light and dark, type, spacing, radii, sizes, shadows), `components/` (20 components with a preview and guidelines each, and a cover), `assets/` (the app icon and 50 Font Awesome 4 icons exported as SVG) and `design-system.json` (its index). Its fonts are the app's own in `apps/editor-gui/src/editor_gui/assets/fonts/` (XKNX Sans, Inconsolata, fontawesome-webfont).

## Concept in Short

- **Fixed zones instead of free docking:** top bar (project, search and command palette ⌘P, pending changes, connection), activity rail (Project, Catalog, Bus, Check, Tools), navigator (Building | Topology | Group Addresses), workspace, context inspector (device, group object or group address), a bottom drawer that can be collapsed (operations, telegrams, log, history) and a status bar.
- **One way to show a panel**, not three (the ▾ per dock, View › Windows and × on the tab); ⌘B, ⌘I and ⌘J toggle the navigator, the inspector and the drawer.
- **The device parameter editor stays as it is**, because the device's configuration defines it.
- Programming runs from one split button per device with all scopes and a queue in the drawer.
- **Small screens** follow the browser UI's `form_factor`: the full layout on an iPad in landscape, overlays in portrait, one view after the other on a phone.

## Viewing the Files

The `.dc.html` files and the design system are Claude Design sources. They need the Claude Design runtime (`support.js`), which is not part of this repository, so they do not open on their own in a browser. To view them, publish `project/` as a Claude Design canvas and `design-system/` as a Claude Design design system.

`project/_blob/` holds the files the boards refer to as `/_blob/<id>`: two screenshots of the current editor and the app icon. In the design system, `design-system.json` names the uploaded icons by the same kind of id.

## Open Points

- The devices in the prototypes come from a real project; values, group addresses and warnings are partly invented.
- The prototypes use Inter and JetBrains Mono in place of the app's fonts.
- The accent and status colors come from the prototypes and differ from today's `theme.py`.
- Not designed yet: programming in detail, and the Check area.
