# RAL-Farben einlernen

Die Farbtabelle ist nicht abgeschrieben, sondern **gemessen**: 216 RAL-Classic-
Töne, jede Farbe dreimal, mit Plausibilitätsprüfung. Wiederholstreuung im
Mittel 0,08 ΔE, im schlechtesten Fall 0,50.

## Die Vorlage

Gemessen wurde mit einem **originalen RAL® K5 in seidenmatt** — dem
Standardfächer für RAL Classic.

Das ist kein Detail. **Nachbau-Farbkarten aus dem Zubehörhandel weichen oft
spürbar ab**, teils um mehrere ΔE, und untereinander sind sie auch nicht
einheitlich. Wer damit einlernt, schreibt den Fehler der Karte dauerhaft in
die Tabelle. Wer damit prüft, misst den Fehler der Karte statt den der Farbe.

Dazu kommt der Glanzgrad: seidenmatt, hochglänzend und matt derselben
RAL-Nummer messen sich unterschiedlich, weil bei 45°/0°-Geometrie der
Glanzanteil zwar ausgeblendet wird, die Oberfläche das Licht aber trotzdem
anders streut. Für ein einheitliches Wörterbuch also durchgehend denselben
Glanzgrad nehmen.

## Das Werkzeug am PC

`cr4501_suite.py` (Kern) und `cr4501_suite_gui.py` (Oberfläche, tkinter).
Braucht `pyserial` und `pillow`.

```
python cr4501_suite_gui.py
```

Die Bereiche:

| Bereich | Inhalt |
|---|---|
| Messung | Messung auslösen, Lab lesen, Farbfeld, RAL-Sofortabgleich |
| RAL | einzeln nachmessen, geführtes Einlernen 3× je Farbe, mehrere Wörterbücher |
| Kalibrierung | über `0x51` auslesen und sichern |
| Startbild | laden, skalieren, Vorschau, ins Geräteformat wandeln |
| Konfiguration | erweiterter Modus, Screen-ID, Rohkommando |
| DFU | Abzug lesen, Anwendung schreiben |
| Flash-Patch | Byte-Patch mit Bereichswarnung, Konfig-CRC, Export |
| Konsole | `help`, `status`, `measure`, `read`, `dump`, `raw` |

Konfigurationsändernde Aktionen haben eine Sicherheitsabfrage.

## Ablauf beim Einlernen

1. Farbe im Fächer aufschlagen, Gerät aufsetzen
2. Dreimal messen — das Werkzeug fordert dazu auf
3. Streuung prüfen: liegt die Spanne über 1,5 ΔE, wird die Farbe zur
   Wiederholung vorgeschlagen
4. Mittelwert übernehmen, weiter zur nächsten

Ergebnis ist eine CSV im Format `ral,L,a,b,streuung,abweichung,hinweis`.

## Die wichtigste Regel

**Lichtart und Beobachter über den gesamten Durchlauf gleich lassen**, etwa
D65/10°. Wechselt die Kombination zwischendurch, werden die Werte
unvergleichbar.

Der Hintergrund: Die Umrechnung XYZ → CIELAB (`FUN_08011F82` →
`FUN_080124BC`) holt den Weißpunkt aus einer Tabelle bei `DAT_0801255C`,
indexiert mit `beobachter * 0x48 + lichtart * 4`. Beide Werte kommen aus der
Konfiguration (`+2` und `+3`). Ist die Kombination ungültig, greift die
Funktion auf Nullbytes zu, Yn wird nahezu null — und L explodiert auf Werte
wie 511. Das ist kein Rohwert, sondern ein mit falschem Weißpunkt normiertes
L\*.

Auch beim Auslesen über USB gilt: erst prüfen, welche Kombination im Gerät
gesetzt ist.

## Der richtige Lab-Puffer

Es gibt zwei Strukturen `{float L, a, b}` relativ zur Messbasis
`0x20000E44`:

| Adresse | wann geschrieben |
|---|---|
| `0x20000EC0` | Kalibrierung (Parameter 4) |
| `0x20000ECC` | normale Messung (Parameter 8) |

Wer versehentlich den falschen liest, bekommt plausible, aber falsche Zahlen.

## Aus der CSV wird die Flash-Tabelle

`ral_flash_build.py` erzeugt aus der CSV den Binärblock im Format `MTP1`
(Aufbau siehe [ral-bildschirm.md](ral-bildschirm.md)). Die deutschen Farbnamen
werden dabei in Wortbausteine zerlegt, sonst passt es nicht in den freien
Speicher: 216 Einträge à 10 Byte sind 2160 Byte, mit Kopf, Namensblock und
Vorlage kommt man auf 3732 Byte.

Umlaute gibt es nicht — der Zeichensatz des Geräts ist GB2312 plus ASCII.
Deshalb steht auf dem Display `Gruengrau` und nicht `Grüngrau`.

## Grenzen der Daten

Ein Fächer, ein Gerät, drei Messungen je Farbe. Fächer altern und vergilben,
jedes Messgerät hat seine eigene Kalibrierung. Für die Frage „welcher RAL-Ton
ist das ungefähr" reicht das gut. Für eine Abnahme oder einen
Reklamationsfall nicht — dafür bleibt der Fächer maßgeblich.

## Das Programm im Detail

`werkzeug/ral_einlernen.py`, 690 Zeilen, braucht `pyserial` und für die
Excel-Ausgabe `openpyxl`.

```
python ral_einlernen.py COM3 --original cr4501_original_....bin
```

Es liest keine Tastatureingaben. Das Gerät schickt nach jeder Messung von
selbst `L=..;a=..;b=..;` über den COM-Port; darauf wartet das Programm mit
einem regulären Ausdruck. Du legst also nur Karten auf und drückst am Gerät.

### Die drei Prüfungen

| Prüfung | Schwelle | Reaktion |
|---|---|---|
| Doppelmessung derselben Karte | unter 1,0 ΔE zur Vorfarbe **und** näher an ihr als an der erwarteten | verworfen, Hinweis „bitte nächste Karte" |
| Streuung der Einzelmessungen | über 1,5 ΔE zueinander | Ausreißer verworfen, Ersatzmessung |
| Abgleich mit der Erwartung | über 18 ΔE zum Sollwert | Warnung mit dem besser passenden RAL-Ton |

Nach vier Ausreißern in Folge beginnt die Farbe von vorn. Die Sollwerte
stammen aus der öffentlichen RAL-Tabelle und sind nur eine Näherung aus
Farbcodes — sie dienen der Plausibilität, nicht als Referenz.

### Fortschritt und Ausgabe

Nach **jeder** Farbe wird `ral_fortschritt.csv` geschrieben. Abbruch mit
Strg+C ist folgenlos; beim nächsten Start geht es an derselben Stelle weiter.

```
ral,L,a,b,streuung,abweichung,hinweis
1000,75.12,0.27,29.08,0.08,1.10,
```

Am Ende entsteht zusätzlich `ral_einlernung.xlsx` mit Soll- und Ist-Werten,
Streuung, Abweichung, Farbvorschau für beide und einer Hinweisspalte.

## Aus Messwerten wird Firmware

`werkzeug/firmware_bauen.py` nimmt deine **eigene** Firmware-Sicherung und
die CSV und baut daraus ein fertiges Abbild:

```
python firmware_bauen.py original.bin ral_fortschritt.csv cr4501_ral.bin
```

Das Einlernprogramm ruft das mit `--original` von selbst am Ende auf.

Die Sicherung ist die Datei, die das Webwerkzeug beim Auslesen anlegt: 180224
Byte, der Anwendungsbereich `0x08004000`–`0x0802FFFF`. Das Ergebnis hat
dieselbe Größe und lässt sich im Webwerkzeug unter *Sicherung einspielen*
aufs Gerät bringen — oder mit `dfu-util -a 0 -s 0x08004000 -D`.

### Was hineingeschrieben wird

| Adresse | Inhalt | Größe |
|---|---|---|
| `0x0800A69C` | Eingabetaste freigeben (Auswertung) | 4 B |
| `0x0800A920` | Eingabetaste freigeben (Abfrage) | 4 B |
| `0x0800A95C` | Taste links freigeben | 4 B |
| `0x0800A9B4` | Taste rechts freigeben | 4 B |
| `0x08014288` | Sprung in den RAL-Bildschirm | 4 B |
| `0x0802E3D0` | RAL-Bildschirm | 1328 B |
| `0x0802E900` | Farbtabelle | 3732 B |

Alles ab `0x08030000` bleibt unberührt. Der Bauteil bricht ab, wenn eine
Adresse über dieser Grenze läge.

### Warum das sicher ist

An jeder der sieben Stellen werden vorher die erwarteten Originalbytes
verglichen. Passt eine nicht, bricht das Programm ab und nennt Adresse, Soll
und Ist — statt auf gut Glück zu schreiben. Steht dort bereits der Patch,
sagt es das ebenfalls. Die Zielbereiche für Code und Tabelle müssen komplett
`0xFF` sein, sonst läuft schon eine Erweiterung auf dieser Firmware.

Die Farbnamen und ihre Kodierung stammen aus einer mitgelieferten Vorlage
(`_tab.txt`, gepackt und base64-kodiert) und bleiben unverändert. Ersetzt
werden nur L, a, b und der Anzeigefarbwert, den das Programm aus dem neuen
Lab-Wert über sRGB nach RGB565 rechnet. Farben, die in deiner CSV fehlen,
behalten die Werte der Vorlage.

### Warum nicht der Loader

Der Weg über `daten_schreiben.bin` wäre auch möglich, hat aber zwei Nachteile:
Die Tabelle läge im Bereich des Messwertspeichers und wird dort früher oder
später überschrieben, und der Loader überschreibt beim Schreiben den gesamten
permanenten Bereich inklusive Werkskalibrierung. Im Anwendungsbereich ist die
Tabelle dauerhaft sicher und wird bei jedem normalen DFU-Vorgang
mitgeschrieben. Einzelheiten in
[permanenter-speicher.md](permanenter-speicher.md).
