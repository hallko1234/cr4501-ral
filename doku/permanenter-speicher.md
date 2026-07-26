# Den permanenten Speicher beschreiben

Alles ab `0x08030000` — Startbild, Menüeinstellungen, Werkskalibrierung,
Messdatensätze — ist per DFU nicht erreichbar. Der Bootloader schreibt dort
schlicht nicht.

## Die geräteinterne Routine

```c
undefined4 flash_write_page(int seitenbasis,   // 2 KB-ausgerichtet
                            int block,         // 0…7
                            void *quelle,      // 256 Byte
                            uint laenge);      // in Wörtern, < 0x201
```

Adresse: `0x08007A1C` (Thumb: `0x08007A1D`).

Sie arbeitet als Read-Modify-Write über die **ganze Seite**: erst die 2 KB in
einen Zwischenpuffer lesen, dann den 256-Byte-Block ersetzen, Seite löschen,
alles zurückschreiben. Pro Aufruf also 256 Byte.

Im ganzen Programm gibt es genau vier Aufrufer:

| Adresse | wofür |
|---|---|
| `0x0800BDBC` | Startbild |
| `0x0800BE1A` | Startbild |
| `0x0800D37A` | Messdatensatz |
| `0x0800D4B0` | Messdatensatz |

**Keiner davon hat eine frei wählbare Zieladresse.** Es gibt kein
USB-Kommando, mit dem sich ein beliebiger Bereich beschreiben ließe.

## Datensatzspeicherung stilllegen

Wer den oberen Flash für eigene Daten braucht, kann die beiden Datensatz-
Aufrufe neutralisieren — je vier Byte:

```
0x0800D37A   bl flash_write_page   →   movs r0,#0 ; nop
0x0800D4B0   bl flash_write_page   →   movs r0,#0 ; nop
```

`r0 = 0` meldet dem Aufrufer Erfolg. Danach wird nie wieder in den
Datensatzbereich geschrieben, egal was im Menü steht — stärker als ein
Menüschalter, den man versehentlich umlegen kann.

## Der Loader

`daten_schreiben.bin` ist ein **eigenständiges Programm**, das anstelle der
Firmware läuft. Es benutzt nicht die geräteinterne Routine, sondern
programmiert den Flash-Controller bei `0x40022000` selbst.

```
Reset-Vektor  0x08004013
Schreibbasis  0x0802FFFE   (Literal bei 0x080041D0)
Datenquelle   0x080041E4   (Literal bei 0x080041D4)
```

Es schreibt halbwortweise fortlaufend ab `0x08030000`. Die RAL-Tabelle landet
bei `0x08039400`, weil sie im eingebetteten Block an Offset `0x9400` liegt.

**Das ist der gefährliche Teil:** Der Loader überschreibt den *gesamten*
permanenten Bereich mit der Kopie, die in ihm eingefroren ist — Startbild,
Einstellungen und **Werkskalibrierung** inbegriffen. Auf einem fremden Gerät
würde er dessen Kalibrierung durch eine fremde ersetzen. Das Gerät misst
danach falsch, ohne dass es jemand merkt, und der Werkszustand ist weg.

Ein Loader darf deshalb **niemals** weitergegeben werden. Er ist nur für das
Gerät gültig, aus dessen Abzug er gebaut wurde.

Ablauf beim eigenen Gerät:

```
1. Vollen Abzug sichern:
   dfu-util -a 0 -s 0x08000000:262144 -U dump.bin
2. Loader flashen:
   dfu-util -a 0 -s 0x08004000 -D daten_schreiben.bin
3. Gerät normal starten, ~10 s warten
4. Firmware zurückflashen:
   dfu-util -a 0 -s 0x08004000 -D app_ral.bin
```

## Der bessere Weg: gar nicht dorthin

Die RAL-Tabelle sind 3732 Byte und passt damit in den freien Bereich der
Anwendung (`0x0802E900`–`0x0802F7FF`, 3840 Byte). Dort wird sie bei jedem
normalen DFU-Vorgang mitgeschrieben, der Datensatzspeicher erreicht sie nie,
und ein Loader wird überflüssig.

Nötig sind dafür nur zwei Dinge:

1. Die drei Zeiger im Tabellenkopf um die Adressdifferenz verschieben
2. Das Literal bei `0x0802E69C` auf `Basis − 0x400` setzen

Genau so arbeitet das Werkzeug auf der Projektseite.

## Startbild über USB

Für das Startbild gibt es eine eigene Zustandsmaschine im Betriebsprotokoll
(`logo --1/--2/--3`, Quelle im RAM bei `0x20003780`), die intern
`flash_write_page` benutzt und damit die DFU-Grenze umgeht. Sie zählt ab
`0x08030000` seitenweise hoch, maximal 120 Seiten. Format: BMP 122 × 122,
16 bpp RGB565, DIB-Kopf 56 Byte, davor ein 8-Byte-Vorspann
(`FF FF FF FF` + Länge).

Theoretisch ließe sich damit auch eine Datentabelle schreiben — aber nur ab
`0x08030000` aufwärts, also unter Verlust des Startbilds, und der Sendeweg ist
bisher nicht verifiziert.
