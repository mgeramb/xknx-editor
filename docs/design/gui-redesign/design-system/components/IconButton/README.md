# IconButton

Quadratischer Knopf nur mit Icon, für wiederkehrende Werkzeugaktionen.

- Immer mit Tooltip, der den Namen und, falls vorhanden, die Taste nennt („Navigator ein/aus (⌘B)“), und mit `aria-label`.
- Icon aus Font Awesome 4 in `muted` oder `text`, 14–16px; Größe `control-h` bzw. `control-h-touch`.
- Nur für Aktionen, deren Icon eindeutig ist (Kopieren, Löschen, Suchen, Schließen). Sonst ein Button mit Text.
- Auf Touch gibt es keinen Tooltip: Was nicht eindeutig ist, steht zusätzlich im ⋯-Menü mit Text.
