# Button

Knöpfe für Aktionen: primär, sekundär, ohne Rahmen (ghost) und zerstörend.

- **Primär** (`accent`, Text `accent-ink`): höchstens einer je Bereich, für die Hauptaktion (Programmieren, Speichern, Anlegen).
- **Sekundär**: Rahmen `control-border` auf `panel`; Abbrechen und alles Weitere.
- **Ghost**: in Kopfleisten und Werkzeugleisten, wo viele Knöpfe nebeneinander stehen.
- **Zerstörend**: Text und Rahmen `danger`, öffnet immer eine Bestätigung (Text endet auf „…“).
- Höhe `control-h` (30px) mit Maus, `control-h-touch` (40px) bei Touch; Radius `radius-sm`, bei Touch `radius-md`.
- Beschriftung in Title Case (englisch), sie sagt, was passiert („Program“, nicht „OK“). Öffnet der Knopf einen Dialog, endet sie auf „…“ (U+2026).
- Deaktiviert nur mit Tooltip, der den Grund nennt; auf Touch steht der Grund als Hinweis darunter.
