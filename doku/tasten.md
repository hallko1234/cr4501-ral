# Das Tastensystem

Fünf Tasten, davon drei ab Werk auf den Messansichten gesperrt. Hier steht,
wie es aufgebaut ist und wo die Sperre sitzt.

## Registrierung

`vTaskInterface` meldet beim Start fünf Tasten an:

```c
FUN_0800A8C8(index, lesefunktion, handler);
```

Die Zeiger liegen als Literale im Flash und lassen sich mit vier Byte
umbiegen:

| Index | Taste | Handler | Literal | Lesefunktion | Literal |
|---|---|---|---|---|---|
| 0 | Messtaste | `0x0800A731` | `0x08018EDC` | `0x0800A995` | `0x08018EE0` |
| 1 | Eingabe | `0x0800A699` | `0x08018EE4` | `0x0800A91D` | `0x08018EE8` |
| 2 | rechts | `0x0800A74D` | `0x08018EEC` | `0x0800A9B1` | `0x08018EF0` |
| 3 | links | `0x0800A6D9` | `0x08018EF4` | `0x0800A959` | `0x08018EF8` |
| 4 | Hall-Kontakt | `0x0800A675` | `0x08018EFC` | `0x0800A8E9` | `0x08018F00` |

**Achtung:** Ein Hook in die *Lesefunktionen* (`0x08018EE0` und folgende) führt
zum Absturz. Die *Handler*-Literale lassen sich dagegen problemlos umbiegen.

## Ablauf

`key_scan_a` bei `0x0800A7A4` läuft in `vTaskInterface` alle 10 ms. Die
Tastentabelle liegt im RAM bei `0x2000104C`, fünf Einträge à 16 Byte:

| Offset | Inhalt |
|---|---|
| `+0x00` | Zeiger auf die Lesefunktion |
| `+0x04` | Zähler ausstehender Ereignisse |
| `+0x05` | **frei** — hier lagen die Zähler des Diagnose-Patches |
| `+0x06` | Zeitgeber (uint16) |
| `+0x08` | Druckart: 1 kurz, 2 lang |
| `+0x09` | Zustand des Automaten |
| `+0x0C` | Zeiger auf den Handler |

Der Handler wird als `handler(druckart)` gerufen. Die 800-ms-Schwelle für den
langen Druck sind schlicht 80 Durchläufe der 10-ms-Schleife.

## Ereignisse

Die Handler posten in eine FreeRTOS-Ereignisgruppe (`event_post` bei
`0x0801957E`, Handle-Zeiger im RAM bei `0x20000008`). Am UI-Verteiler
`FUN_08006CD0` kommen an:

| Wert | Auslöser | Wirkung ab Werk |
|---|---|---|
| `1` | Messtaste kurz | Messung |
| `2` | Messtaste lang | erreicht das UI nicht |
| `4` | rechts | blättert Datensätze |
| `8` | links | blättert Datensätze |
| `0x10` | Eingabe kurz | schaltet Messung ↔ Pass |
| `0x20` | Eingabe lang | **ungenutzt** |
| `0x100` / `0x200` | nach abgeschlossener Messung | Neuzeichnen |
| `0` | Neuzeichnen | |

## Die Sperre

Sie sitzt nicht im Handler, sondern in der **Lesefunktion** — zwei Stufen vor
dem Ereignis, weshalb sie so schwer zu finden war:

```
0800A9B0  key2_read (rechts)
  ldrb.w r0, [r0, #0x270]     ← Screen-ID
  cmp r0, #0x0E  → return 0
  cmp r0, #0x11  → return 0
  cmp r0, #0x15  → return 0   ← der Normalzustand
  cmp r0, #0x18  → return 0
  cmp r0, #0x19  → return 0
  cmp r0, #0x1A  → return 0
  ... erst danach wird die GPIO gelesen
```

Dieselbe Kette steht wortgleich in `key3_read` (`0x0800A958`) und `key1_read`
(`0x0800A91C`). Die Eingabetaste hat sie **zusätzlich** im Handler
(`0x0800A69A`).

`key0_read` (Messtaste) hat keine solche Prüfung — deshalb ging nur die.

Die Screen-ID bei `0x200044D4` steht dauerhaft auf `0x15`. Also liefern die
Lesefunktionen immer 0, der Zustandsautomat sieht nie einen Druck, der Handler
wird nie gerufen.

## Die Freigabe

Vier Stellen, je vier Byte. `ldrb.w r0,[r0,#0x270]` wird zu `movs r0,#0 ; nop`
— dann ist r0 null, keiner der sechs Vergleiche trifft, und es geht direkt zur
GPIO-Abfrage.

| Adresse | vorher | nachher | wirkt auf |
|---|---|---|---|
| `0x0800A9B4` | `90 f8 70 02` | `00 20 00 bf` | rechts |
| `0x0800A95C` | `90 f8 70 02` | `00 20 00 bf` | links |
| `0x0800A920` | `90 f8 70 02` | `00 20 00 bf` | Eingabe, Lesefunktion |
| `0x0800A69C` | `91 f8 70 12` | `00 21 00 bf` | Eingabe, Handler |

Ergebnis: sämtliche Menüs und Einstellungen des Geräts werden zugänglich,
inklusive Datensatzspeicherung.

## Taste 4 ist eine Falle

Die Lesefunktion von Taste 4 (`0x0800A8E8`, Pin `0x1000`) meldet fast
durchgehend „gedrückt": Ist der Pin hoch, liefert sie 1; ist er niedrig,
liefert sie erst nach zwölf Durchläufen 0. Ihr Handler gibt nur eine
Textzeile aus.

Ein Diagnose-Patch, der aus dem Tastenhandler heraus zeichnete und dabei
150 ms wartete, brachte das Gerät deshalb schon beim Booten zum Stehen — Taste
4 löste dauernd aus. Aus dem Tastentask darf weder gezeichnet noch gewartet
werden.
