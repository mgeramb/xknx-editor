# GUI Redesign Roadmap

Findings of the review of the workbench (`XKNX_REDESIGN=1`) on 2026-11-22, and the order of the next steps.

## What the Review Covered

- The code of the workbench, the design boards, and the running browser UI at 1440×900 and at phone size.
- A test project with one device, seven group addresses and no telegrams. Group addresses, checks and the monitor still need a look at a large project.
- Not reviewed: Topology, DALI, KNX Secure, Home Assistant, Backups, the connection and programming dialogs.
- The efforts below are estimates from the screens and the code: S up to 2 days, M 3 to 5 days, L over a week.

## Main Finding

The workbench has moved the panels, but apart from the group objects it hardly changes what is in them. The building tree, the device inspector and the bottom panel stay in every area (Catalog, Bus, Check, Tools), so the screen actually worked in gets about 40 % of a 1440×900 window.

## Priorities

| Priority | Screen | Problem | Goal | Design | Effort |
| --- | --- | --- | --- | --- | --- |
| P0 | Frame | The same zones in every area | Navigator and inspector per area, bottom panel closed by default | Yes | M |
| P1.1 | Group addresses | A tree in a narrow column, four buttons above it, no overview of DPT, usage and links | Groups in the navigator, a table in the workspace, free ranges, bulk edits | Yes | L |
| P1.2 | Device header and programming | Actions spread over header, inspector and bottom panel; Reset beside Restart | One split button, a "more" menu, one flow up to the result | Rough | L |
| P1.3 | Check | A flat list (11 findings for one device), long texts cut off | Grouped by cause, details with the fix, bulk fixes | Missing | M |
| P2.1 | Device overview | A tab that is easily missed, a list without actions | Start view of project, line and room; program several devices | Rough | M |
| P2.2 | Bus and monitor | Two levels of tabs (3 + 5), icons without labels | Views in the navigator, telegram details in the inspector | Yes | L |
| P2.3 | Tools and mass linking | Up to 10 tabs in two levels, instructions in place of guidance | A start page by task, linking with a preview | Rough | M |
| P3.1 | Catalog | Three separate sources, no place for product details | Manufacturers left, results in the middle, the product right | Missing | M |
| P3.2 | Recover from the bus | All steps at once, most of them disabled | Guided: search, select, verify, take over | Missing | M |
| P4 | Bottom panel, settings | "History" twice, project information in the wrong place | Tidy up, no rebuild | Partly | S |

Left as they are: the content of the parameters (the device defines it) and the group objects (already rebuilt, only polish).

## Stages

1. **Foundation:** P0 and the defects below.
2. **Group addresses:** sets the pattern navigator, table, inspector for the other screens. Design programming in parallel.
3. **Commissioning:** plan programming, Check and the device overview together, as they share states and bulk actions.
4. **Diagnosis and bulk work:** Bus, Tools.
5. **The rest:** Catalog, Recover, tidying up.

## Defects for Stage 1

- [ ] The workbench is translated to German only: 23 languages are missing, which fails 46 translation tests.
- [ ] The indicator of the devices to program opens Operations, which says "No operations" as long as nothing is running; it has to show those devices.
- [ ] Quick clicks on tabs in the browser UI can get lost, also after the fix for quick taps. Seen with automated clicks; to be checked with a real mouse.

## Designed Separately

- **Device links** (part of stage 4, implementation postponed): an overview of all devices with their links as the successor of the Bus Diagram's Links view; concept, prototype and plan in [`../device-links`](../device-links/README.md).
