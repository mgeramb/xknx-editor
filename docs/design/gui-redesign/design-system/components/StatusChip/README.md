# StatusChip

Zustand eines Geräts in Worten, im Gerätekopf, im Inspektor und in Listen mit Platz.

- Vier Zustände, je Fläche `*-weak` mit Text in der Vollfarbe: `ok` Programmiert, `warn` Ausstehend, `danger` Nicht in Betrieb, neutral (`sub`, `muted`, Rahmen `line2`) Status unbekannt.
- Wo kein Platz für Worte ist (Navigator), steht der StatusDot; der Chip ist dann im Tooltip bzw. Inspektor.
- Satzanfang groß, Rest wie geschrieben (Sentence case).
