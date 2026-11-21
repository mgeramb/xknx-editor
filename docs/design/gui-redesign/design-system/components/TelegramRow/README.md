# TelegramRow

Ein Telegramm im Gruppenmonitor, zweizeilig, wenn die Spaltentabelle keinen Platz hat.

- Zeit in `mono`, Art als Buchstabe: W Schreiben (`accent`), L Lesen (`warn`), A Antwort (`ok`); englisch W, R, A.
- Gruppenadresse in `mono`, Name dahinter, decodierter Wert rechts in `body-strong`, Quelle mit Adresse und Name darunter in `muted`.
- Neue Telegramme blenden kurz in `sel` ein, ohne die Liste springen zu lassen, solange „Folgen“ aus ist.
