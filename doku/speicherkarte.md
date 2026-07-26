# Speicherkarte des CR4501

Alles hier ist aus dem echten Flash-Abzug verifiziert, nicht aus Datenblättern
abgeleitet.

## Der Chip

STM32F103xC-Klasse (Cortex-M3, 72 MHz, keine Fließkommaeinheit), 256 KB Flash,
48 KB RAM, Seitengröße 2 KB. Möglicherweise ein pinkompatibler GD32F103 — aus
dem Abzug allein nicht unterscheidbar.

Vektortabellen: Bootloader SP `0x20002EE8` / Reset `0x08000145`;
Anwendung ab `0x08004000` SP `0x2000C000` / Reset `0x080041E9`.

## Aufteilung

| Bereich | Inhalt | per DFU? |
|---|---|---|
| `0x08000000`–`0x08003FFF` | Bootloader, 16 KB | nur lesen |
| `0x08004000`–`0x0802FFFF` | Anwendung, 176 KB | **ja** |
| `0x0802E3D0`–`0x0802F7FF` | frei, 5168 B — hier liegen alle Patches | ja |
| `0x08030000`–`0x080374FF` | Startbild (BMP 122×122, RGB565) | nein |
| `0x08037800`–`0x08037BFF` | Menüeinstellungen (Block A), 1 KB, CRC-16 | nein |
| `0x08038000`–`0x080382FF` | Gerätedaten + **Werkskalibrierung** (Block B) | nein |
| `0x08039000`–`0x0803FE00` | gespeicherte Messdatensätze | nein |

## Die harte Grenze bei 0x08030000

Der Bootloader schreibt **nicht** über `0x08030000` hinaus. Ein DFU-Versuch
darüber meldet beim Löschen Erfolg und bricht beim Download bei 0 % ab. Das
erklärt auch, warum ein Schreibvorgang über die vollen 240 KB reproduzierbar
bei 72 % hängt.

Alles oberhalb erreicht nur die geräteinterne Routine `flash_write_page`
(siehe [permanenter-speicher.md](permanenter-speicher.md)).

## Der Bootloader löscht alles

**Die wichtigste Regel überhaupt:** Beim ersten Schreibbefehl nach dem
Einschalten löscht der Bootloader den **kompletten** Anwendungsbereich
(Seiten 8–95, 180224 Byte) und erwartet danach das vollständige Abbild.

Einzelne Seiten zu schreiben zerstört daher alles andere. Richtig ist immer:

```
dfu-util -a 0 -s 0x08004000 -D app.bin
```

Und **niemals** die Option `-t`. Mit `-t 256` rechnete das Gerät weiterhin mit
seiner eigenen Transfergröße 1024 — die Daten landeten an vierfacher Position
und zerstörten 88 Seiten.

## Prüfung beim Start

Der Bootloader testet nur, ob der Stapelzeiger plausibel im RAM liegt:

```c
(*(uint32_t*)0x08004000 & 0x2FFE0000) == 0x20000000
```

Keine Prüfsumme, keine Signatur. Deshalb startet auch selbstgebauter Code.

## Datensatzspeicher

Ein Datensatz belegt einen 256-Byte-Block, acht Blöcke pro Seite:

```c
flash_write_page(0x08039000 + ((n-1) >> 3) * 0x800, (n-1) % 8, quelle, 0x40);
```

Bei maximal 110 Datensätzen reicht der Bereich bis `0x0803FE00` — praktisch
der gesamte freie obere Flash. Wer dort eigene Daten ablegt, verliert sie,
sobald genug Messungen gespeichert werden. Genau das ist der RAL-Tabelle bei
`0x08039400` einmal passiert.
