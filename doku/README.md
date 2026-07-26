# Dokumentation

> **English readers:** this documentation is in German, but its substance is
> addresses, byte sequences and tables — `0x0800A9B4 · 90 f8 70 02 →
> 00 20 00 bf` reads the same in any language. Chapters cover the memory map,
> the button system and where the factory lock sits, the screen handling, the
> RAL screen and its table format, writing above the DFU boundary, the USB
> protocol, and how the 216 colours were measured. Everything is verified on
> the device or in the flash dump.


Was beim Erschließen der CR4501-Firmware herausgekommen ist. Alle Adressen
sind am Gerät oder im Flash-Abzug verifiziert, nicht geraten. Wo etwas
unsicher ist, steht es dabei.

| Datei | Inhalt |
|---|---|
| [speicherkarte.md](speicherkarte.md) | Flash-Aufteilung, DFU-Grenze, die Regeln beim Schreiben |
| [tasten.md](tasten.md) | Tastensystem, wo die Sperre sitzt, wie man sie löst |
| [bildschirme.md](bildschirme.md) | Zeichenfunktionen, Modus-Byte, dritte Ansicht |
| [ral-bildschirm.md](ral-bildschirm.md) | Aufbau des eigenen Bildschirms, Tabellenformat |
| [permanenter-speicher.md](permanenter-speicher.md) | Schreiben oberhalb 0x08030000, der Loader und seine Gefahr |
| [usb-protokoll.md](usb-protokoll.md) | Binärframes, Kommandos, Debug-Ausgabe umleiten |
| [einlernen.md](einlernen.md) | Farben einmessen, Prüfungen, und wie daraus die Firmware entsteht |

Die Programme dazu liegen unter [../werkzeug/](../werkzeug/).

## Wie das entstanden ist

Firmware per DFU ausgelesen, in Ghidra dekompiliert, Adressen am laufenden
Gerät gegengeprüft. Der entscheidende Durchbruch bei den Tasten kam erst über
ein Protokoll auf dem COM-Port — im Dekompilat allein war die Sperre nicht zu
finden, weil sie an einer Stelle sitzt, an der niemand sie vermutet.

## Die teuer gelernten Regeln

1. **Niemals `dfu-util -t`.** Das Gerät rechnet weiter mit seiner eigenen
   Transfergröße; die Daten landen an vierfacher Position.
2. **Immer den ganzen Anwendungsbereich am Stück schreiben.** Der Bootloader
   löscht beim ersten Schreibbefehl alles.
3. **Nichts über `0x08030000` schreiben**, außer man weiß genau, was dort
   steht. Dort liegen Einstellungen und die Werkskalibrierung.
4. **Aus dem Tastentask weder zeichnen noch warten.** Taste 4 meldet fast
   durchgehend „gedrückt" und bringt das Gerät sonst beim Booten zum Stehen.
5. **Vor jedem schreibenden Versuch einen vollen Abzug sichern.** Lesen ist
   ungefährlich.
6. **Prüfen statt vertrauen:** Vor einem Patch die erwarteten Originalbytes an
   jeder Adresse vergleichen und lieber abbrechen als raten.
