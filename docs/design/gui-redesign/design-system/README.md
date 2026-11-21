Das Design System des XKNX Editors für die neue Oberfläche: feste Zonen statt freier Docking-Fenster, ein Projekt in drei Sichten, ein Inspektor für das Gewählte. Es gilt für die Desktop-App (Dear ImGui) und den Browser-Modus (`--web`) auf Tablet und Phone. Den Inhalt des Parameter-Editors gibt die Gerätekonfiguration vor; dieses System regelt nur alles drumherum.

## Grundsätze

- **Ruhig und dicht.** Die App ist ein Werkzeug für Stunden am Stück. Fläche `panel` auf Grund `bg`, Text in `text` und `muted`, Farbe nur für Zustand und die eine Hauptaktion.
- **Zustand steht da, wo man hinschaut.** Ausstehende Programmierungen, Verbindung und Fehler sind Pillen und Chips, keine versteckten Logzeilen. Jeder Zustand ist anklickbar und führt zur Ursache.
- **Eine Hauptaktion je Bereich.** Höchstens ein primärer Button (`accent`) sichtbar je Zone; alles Weitere im ⋯-Menü.
- **Technisches in Mono.** Physikalische Adressen (1.1.16), Gruppenadressen (7/1/14), DPT (1.008), Zeiten und Rohdaten stehen in `mono`, damit Ziffern untereinanderstehen.
- **Alles auch ohne Maus.** Jede Aktion ist per Taste und per Finger erreichbar; nichts nur über Hover.

## Farben

- Flächen: `bg` für den Fenstergrund, `panel` für jede Zone, `sub` für vertiefte Flächen (Suchfeld, Segmentgrund, Seitenliste, Tabellenkopf). Linien `line` gliedern, `line2` rahmt Karten und Pillen, `control-border` rahmt alles, was man bedient.
- Text: `text` für Inhalte, `muted` für alles Nebensächliche (Adresse neben dem Namen, Einheiten, Spaltenköpfe). Beide erreichen auf `panel`, `sub`, `bg` und `hover` mindestens 4,5 : 1 in beiden Themes.
- Interaktion: `accent` für die Hauptaktion, aktive Tabs, den Auswahlstrich und den Fokusring; `accent-weak` als Grund für Gruppenadressen und Gewähltes. Hover `hover`, Auswahl `sel` plus 3px-Strich in `accent`.
- Zustand: `ok` Programmiert, `warn` Ausstehend und Warnung, `danger` Fehler, Nicht in Betrieb, Aufnahme und Löschen. Jeweils mit `*-weak` als Fläche. Gerätezustände über die Aliase `status-programmed`, `status-pending`, `status-error`, `status-unknown`.
- Zustand nie nur über Farbe: StatusDot hat vier Formen (voll, halb, Kreuz, Ring), Chips tragen Worte, Telegramme Buchstaben (W, L, A).
- `overlay` ist in beiden Themes dunkel: Meldungen, Tastenauswahl und Marken sollen sich vom Inhalt abheben.
- Zwei Themes, Hell und Dunkel, aus denselben Token-Namen. Die App übernimmt das Theme des Systems; die übrigen ImGui-Themes bleiben als Auswahl in den Einstellungen, ohne Gewähr für dieses System.

## Schrift

- **XKNX Sans** (`sans`) für alles, Gewichte 400, 350 (Semilight) und 700. Sie liegt der App bei (aus Selawik und Noto Sans, SIL OFL); für Japanisch und Chinesisch bringt die App Noto Sans JP/SC mit.
- **Inconsolata** (`mono`, 500) für Adressen, DPT, Zeiten, Flags und Tastenkappen.
- Grundgröße `body` 13px/18px. Stufen: `dialog-title` 18, `device-title` 16, `panel-title` 14, `body` 13, `small` 12, `label-caps` 11 (nur Gruppenköpfe im Navigator, in Versalien), `micro` 10,5 (nur unter Icons der Leiste).
- Fett nur für Titel, aktive Tabs, gewählte Seiten und Werte in Telegrammen; sonst 400.
- Die Klickdummys im Canvas nutzen Inter und JetBrains Mono als Ersatz, weil sie die App-Schriften nicht laden. Maßgeblich ist XKNX Sans.

## Abstände und Maße

- Raster aus `space-4`, `space-6`, `space-8`, `space-10`, `space-12`, `space-16`, `space-20`, `space-24`. Zonen innen `space-12` bis `space-16`, Formular `space-20`.
- Zonen: Kopfleiste `topbar-h` 52px, Statusleiste `statusbar-h` 28px, Leiste `rail-w` 64px, Navigator `nav-w` 310px (iPad 270px), Inspektor `inspector-w` 330px.
- Bedienelemente: `control-h` 30px und `row-h` 28px mit Maus; bei Touch `control-h-touch` 40px und `row-h-touch` 44px.
- Radien: `radius-xs` Tastenkappen, `radius-sm` Knöpfe und Felder, `radius-md` Suche, Menüs, Segmente, `radius-lg` Karten und Überlagerungen, `radius-xl` Blätter, `radius-pill` Pillen und Chips.
- Schatten nur für Schwebendes: `shadow-popover` (Menüs, Palette), `shadow-overlay` (Navigator und Inspektor über dem Inhalt), `shadow-sheet` (Blätter). Zonen selbst haben keinen Schatten, nur Linien.

## Icons

- Die App nutzt **Font Awesome 4** (`fontawesome-webfont.ttf`, über hello_imgui geladen) als Icon-Schrift; Icons sind Zeichen und nehmen die Textfarbe an. In ImGui als Zeichen im Text (`""`), im Browser als Zeichen in der Familie `icon`.
- Größe 14–16px in Knöpfen und Zeilen, 18px in der Leiste. Farbe `muted`, aktiv `accent`, in Zuständen die Zustandsfarbe.
- Ein Icon steht nie allein ohne Namen: Tooltip am Desktop, Text daneben oder im ⋯-Menü auf Touch.
- Die SVGs in der Gruppe Icons sind aus der Schrift der App exportiert und in `text` (#1b2230) gefärbt; sie dienen der Dokumentation. In der App bleibt die Schrift die Quelle.
- Neue Icons nur aus Font Awesome 4 (Free), damit alles aus einer Hand kommt. Font Awesome 6 Solid liegt der App ebenfalls bei; ein Wechsel wäre ein eigener Schritt für alle Icons gemeinsam.

| Name | Zeichen | Bedeutung |
| --- | --- | --- |
| `home` | U+F015 | Projekt (Leiste) |
| `th-large` | U+F009 | Katalog (Leiste) |
| `exchange` | U+F0EC | Bus (Leiste) |
| `check-circle` | U+F058 | Prüfung (Leiste) |
| `wrench` | U+F0AD | Werkzeuge (Leiste) |
| `cog` | U+F013 | Einstellungen |
| `bars` | U+F0C9 | Menü mit allen Menüs |
| `search` | U+F002 | Suche, Befehlspalette |
| `filter` | U+F0B0 | Filter |
| `plus` | U+F067 | Hinzufügen |
| `ellipsis-h` | U+F141 | Weitere Aktionen |
| `chevron-down` | U+F078 | Aufklappen, Split-Button |
| `chevron-right` | U+F054 | Baum zu, weiter |
| `chevron-left` | U+F053 | Zurück (Phone) |
| `times` | U+F00D | Schließen |
| `check` | U+F00C | Bestätigt, gewählt |
| `download` | U+F019 | Herunterladen, Programmieren |
| `upload` | U+F093 | Hochladen, Import |
| `folder-open` | U+F07C | Öffnen |
| `floppy-o` | U+F0C7 | Speichern |
| `print` | U+F02F | Drucken |
| `files-o` | U+F0C5 | Kopieren |
| `trash` | U+F1F8 | Leeren, Löschen |
| `repeat` | U+F01E | Wiederholen, Replay |
| `undo` | U+F0E2 | Rückgängig |
| `history` | U+F1DA | Änderungsverlauf |
| `play` | U+F04B | Aufnahme starten |
| `stop` | U+F04D | Aufnahme stoppen |
| `stop-circle` | U+F28D | Replay stoppen |
| `paper-plane` | U+F1D8 | Senden |
| `eye` | U+F06E | Speichervorschau |
| `link` | U+F0C1 | Verknüpfen |
| `chain-broken` | U+F127 | Trennen |
| `sitemap` | U+F0E8 | Topologie |
| `building` | U+F1AD | Gebäude |
| `tag` | U+F02B | Gruppenadresse |
| `microchip` | U+F2DB | Gerät |
| `plug` | U+F1E6 | Verbindung |
| `lock` | U+F023 | KNX Secure |
| `unlock` | U+F09C | Nicht gesichert |
| `info-circle` | U+F05A | Hinweis |
| `exclamation-triangle` | U+F071 | Warnung |
| `times-circle` | U+F057 | Fehler |
| `bug` | U+F188 | Debug-Log |
| `keyboard-o` | U+F11C | Tastenkürzel |
| `sliders` | U+F1DE | Parameter |
| `columns` | U+F0DB | Inspektor ein/aus |
| `outdent` | U+F03B | Navigator ein/aus |
| `sun-o` | U+F185 | Hell |
| `moon-o` | U+F186 | Dunkel |

## Symbole und Schreibweisen

- **Physikalische Adresse** `1.1.16` (Bereich.Linie.Gerät), **Gruppenadresse** `7/1/14` (dreistufig) oder `7/270` (zweistufig) bzw. `3854` (frei), je nach Projekt; immer `mono`.
- **DPT** als Nummer und Name: `1.008 Auf/Ab`, `9.001 Temperatur`. In Tabellen die Nummer, im Tooltip beides.
- **Flags** in fester Reihenfolge K L S Ü A I (englisch C R W T U I), gesetzt in `accent`, Kurzform `K·S··`.
- **Telegrammart** als Buchstabe: W Schreiben, L Lesen, A Antwort (englisch W, R, A). Richtung: → vom Bus, ← an den Bus.
- **Gerätezustand** als StatusDot (Form) und StatusChip (Wort): Programmiert, Ausstehend, Nicht in Betrieb, Status unbekannt.
- **KNX Secure** mit `lock` in `ok`, ungesicherte Verbindung zu einem Secure-Gerät mit `unlock` in `warn`.
- **Geändert, nicht programmiert:** 3px-Strich links in `warn` am Feld oder an der Zeile.
- **Sendende Gruppenadresse:** GaChip mit Rahmen in `accent`, steht vorn.

## Texte

- Englisch ist die Ausgangssprache (msgids); alle Sprachen folgen ihren eigenen Regeln. Für Englisch gilt: **Title Case** für Titel, Menüs, Knöpfe, Tabs, Spaltenköpfe und Labels („Load OpenKNX from URL or Folder…“), **Sentence case** für Optionen, Hinweise, Tooltips und Meldungen („Nothing new imported (already in the catalog)“).
- „…“ (U+2026) am Ende eines Knopfs oder Menüeintrags, der einen Dialog oder eine Dateiauswahl öffnet.
- Zahlen mit richtigem Singular und Plural in jeder Sprache, nie „Gerät(e)“. Eine Zahl neben einem Label („Parameter (12)“) braucht keine Pluralform.
- Namen von KNX und Herstellern so, wie sie geschrieben werden: KNX, OpenKNX, MDT, .knxprod.
- Knöpfe sagen, was passiert („Programmieren“, nicht „OK“); Meldungen sagen, was passiert ist und was zu tun ist, ohne Entschuldigung.
- Texte aus den Gerätedaten (Kanalnamen, Parameter) bleiben, wie sie kommen; Labels aus Daten laufen durch `title_case`.

## Tastatur

- **Rahmen mit einer Taste:** ⌘B Navigator, ⌘I Inspektor, ⌘J unterer Bereich, ⌘. alles aus/zurück, ⌘1–⌘5 Bereiche der Leiste. Unter Windows und Linux Strg statt ⌘.
- **Befehle in zwei Stufen:** ⌘G Gehe zu, ⌘D Gerät, ⌘L Verknüpfen, ⌘K KNX-Bus, danach ein Buchstabe aus dem Wort der eingestellten Sprache, im Text unterstrichen. Die vier Bereichstasten sind in allen Sprachen gleich.
- Bestehende Kürzel bleiben: ⌘P Befehlspalette, ⌘S, ⌘O, ⌘E, ⌘Z/⌘Y, ⌘, Einstellungen, F2 Umbenennen. F1 zeigt alle Tasten.
- Sichtbar machen mit Kbd in Menüs, Tooltips und Palette, WhichKey nach der ersten Stufe, Marken beim Halten von ⌘.
- Fokusring immer sichtbar: `focus-w` in `accent`, 2px Abstand.

## Touch und kleine Bildschirme

- Stufen wie `form_factor` im Browser-Modus: ab 1000 Einheiten Breite das volle Layout; darunter Navigator als Schiebe-Panel und Inspektor als Sheet (Tablet hoch), am Phone eine Ansicht nach der anderen mit Tab-Leiste unten.
- Bei Touch gelten `control-h-touch` und `row-h-touch`; langes Drücken öffnet das Kontextmenü; alles, was die Maus per Hover zeigt, gibt es auch per Tippen.
- Tabellen werden am Phone Karten (KoCard) oder zweizeilige Zeilen (TelegramRow).

## Zugänglichkeit

- Text mindestens 4,5 : 1 auf seinem Grund in beiden Themes; Rahmen von Bedienelementen, Fokusring und bedeutungstragende Zeichen mindestens 3 : 1 (`control-border`, `status-unknown`).
- `line` und `line2` liegen darunter (1,4–1,5 : 1); sie gliedern nur und tragen keine Bedeutung.
- Zustand immer mit Form oder Wort zusätzlich zur Farbe.

## Umsetzung in ImGui

- Die Tokens werden in `theme.py` auf die `imgui.Col_`-Farben abgebildet: `panel` → `window_bg`/`child_bg`, `bg` → `docking_empty_bg`, `text`/`muted` → `text`/`text_disabled`, `control-border` → `border` für Felder, `line` → `separator`, `hover` → `header_hovered`/`button_hovered`, `sel` → `header`, `accent` → `tab_selected_overline`, `check_mark`, `slider_grab`, `button` des primären Knopfs.
- Zustandsfarben ersetzen `_STATUS_COLORS` (heute Windows-Töne: Warnung #B06000, Fehler #C41E1E, Erfolg #107C10) und gelten in Hell und Dunkel aus einer Quelle.
- Radien und Abstände über `imgui.Style`: `frame_rounding` = `radius-sm`, `popup_rounding` = `radius-md`, `frame_padding` aus `space-8`/`space-6`, bei Touch zusätzlich `touch_extra_padding`.
