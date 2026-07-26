# USB-Protokoll

Im Normalbetrieb meldet sich das Gerät als USB-CDC („STM32 Virtual ComPort",
115200). Darüber läuft **kein** Textprotokoll, sondern Binärframes.

## Rahmenformat

PC → Gerät:

```
55 AA A6 01 00 00 00 00 <len_lo len_hi> <cmd> [payload] <crc_lo crc_hi>
```

Antwort Gerät → PC beginnt mit `AA 55` — die Kennung ist vertauscht.

Die Prüfsumme ist CRC-16/CCITT-FALSE (Polynom `0x1021`, Startwert `0xFFFF`)
und läuft **nur über Kommando und Nutzdaten**, nicht über den Rahmen.

Minimaler Frame:

```
55 AA A6 01 00 00 00 00 03 00 <cmd> <crc_lo crc_hi>
```

Selbstgebaute Frames sind byteidentisch mit dem Mitschnitt der
Originalsoftware.

## Kommandos

| Code | Wirkung | gefahrlos? |
|---|---|---|
| `0x22` | Status und Zähler | ja |
| `0x23` | Datensatz lesen (Klartext `L=..;a=..;b=..;K/S=..;`) | ja |
| `0x51` | alle Datensätze auflisten | ja |
| `0xA7` | Handschlag | ja |
| `0x24` | Messung auslösen | ja |
| `0x21` | Weißabgleich | greift in die Kalibrierung ein |
| `0x25` | Messung mit Modus-Unterbyte | |
| `0x30` | Konfiguration zurücksetzen | **Vorsicht** |
| `0xA2` | Konfiguration setzen | **Vorsicht** |

`0xA2` hat unkontrollierte Nebenwirkungen auf die Kalibrierung — ein Aufruf
hat einmal die Werks-Weißkalibrierung mit der Nutzerkalibrierung
überschrieben. Vor jedem Versuch damit einen vollen Abzug sichern.

## Nach jeder Messung

Das Gerät sendet den Datensatz von selbst: erst ein Binärframe, dann Klartext
`L=..;a=..;b=..;K/S=..;`. Praktisch zum Mitschneiden, aber es mischt sich mit
eigener Ausgabe.

## Debug-Ausgabe umleiten

`fw_printf` (`0x0800FA14`) schreibt über einen Kanalschalter bei `0x2000024C`:

```
== 1   → FUN_080065E0, direkt auf den CDC-Endpunkt 0x81
sonst  → FUN_0800A190, ein anderer Puffer
```

Ab Werk steht er auf dem zweiten Kanal, weshalb im Terminal nur Messdaten
ankommen. Zwei Änderungen leiten die Ausgabe auf den COM-Port um:

```
0x08012F84   ldrb r0,[r0] ; cmp r0,#1   →   movs r0,#1 ; cmp r0,#1
0x080065EE   das rekursive printf im Busy-Zweig durch nops ersetzen
```

Der zweite Punkt ist Pflicht: Die CDC-Sendefunktion ruft bei belegtem Endpunkt
selbst `fw_printf` auf. Zeigt `printf` auf denselben Kanal, ruft sie sich
endlos selbst — ein echter Fehler, der nur deshalb nicht zündet, weil die
Ausgabe ab Werk woanders hinläuft.

Danach liefert PuTTY (COM-Port, 115200, Flow control None) auch die Meldungen
der Original-Firmware wie `key_left is press`.

## Kommandokonsole

Es gibt eine Textkonsole: Parser `FUN_08012AA0`, Kommandosuche
`FUN_080126E0`, Tabelle im RAM bei `0x200012DC`, je Eintrag `0x4C` Byte
(Name, Handler bei `+0x0C`, Argumentpuffer ab `+0x10`). Registriert werden die
Gruppen `cmd`, `as7341`, `test` und `measure`.

Die Tabelle wird zur Laufzeit gefüllt, steht also nicht lesbar im Abzug — die
vollständige Kommandoliste bekommt man nur am laufenden Gerät.
