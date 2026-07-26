# RAL-Farben einlernen

Die Farbtabelle ist nicht abgeschrieben, sondern **gemessen**: 216 RAL-Classic-
Töne von einem Fächer, jede Farbe dreimal, mit Plausibilitätsprüfung.
Wiederholstreuung im Mittel 0,08 ΔE, im schlechtesten Fall 0,50.

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
