# Werkzeuge

*[English version](README.en.md)*

## ral_einlernen.py

Misst den RAL-Fächer mit dem CR4501 ein: 216 Farben, jede dreimal, mit
Plausibilitätsprüfung — und baut daraus auf Wunsch gleich die fertige
Firmware.

```
python -m pip install pyserial openpyxl
python ral_einlernen.py COM3 --original cr4501_original_....bin
```

Das Programm nennt die nächste Farbe, du legst die Karte auf und drückst am
Gerät. Mehr nicht — keine Tastatureingabe. Nach drei sauberen Messungen geht
es von selbst weiter.

**Die Originaldatei** ist die Sicherung, die das Werkzeug auf der Projektseite
beim Auslesen anlegt: 180224 Byte, der Anwendungsbereich deines Geräts. Aus
ihr und deinen Messwerten entsteht `cr4501_ral.bin`, die du im Webwerkzeug
unter *Sicherung einspielen* wieder aufs Gerät bringst.

Ohne `--original` läuft nur das Einlernen; die Firmware kannst du jederzeit
nachträglich bauen:

```
python ral_einlernen.py --nur-bauen --original cr4501_original_....bin
```

### Was geprüft wird

| Prüfung | Schwelle | Reaktion |
|---|---|---|
| Doppelmessung derselben Karte | unter 1,0 ΔE zur Vorfarbe | verworfen |
| Streuung der drei Messungen | über 1,5 ΔE zueinander | Ausreißer verworfen |
| Abgleich mit der Erwartung | über 18 ΔE zum Sollwert | Warnung, Wert zählt trotzdem |

Nach vier Ausreißern in Folge beginnt die Farbe von vorn. Der Stand liegt nach
jeder Farbe in `ral_fortschritt.csv` — Abbruch mit Strg+C ist folgenlos, beim
nächsten Start geht es an derselben Stelle weiter.

Am Ende entsteht zusätzlich `ral_einlernung.xlsx` mit Soll- und Ist-Werten,
Streuung, Abweichung und Farbvorschau.

### Wichtig vor dem Start

**Lichtart und Beobachter über den ganzen Durchlauf gleich lassen**, etwa
D65/10°. Wechselt die Kombination zwischendurch, werden die Werte
unvergleichbar — und bei einer ungültigen Kombination liefert das Gerät
Unsinn wie L\*=511. Der Grund steht in
[doku/einlernen.md](../doku/einlernen.md).

Vorher schwarz und weiß kalibrieren.

## firmware_bauen.py

Der Bauteil allein, falls du ihn getrennt brauchst:

```
python firmware_bauen.py original.bin ral_fortschritt.csv [ausgabe.bin]
```

Er prüft an jeder der sieben Änderungsstellen die erwarteten Originalbytes und
bricht bei der kleinsten Abweichung ab, statt auf gut Glück zu schreiben.
Ist die Datei schon umgebaut, sagt er das ebenfalls.

Was hineingeschrieben wird:

```
0x0800A69C   Eingabetaste freigeben (Auswertung)      4 B
0x0800A920   Eingabetaste freigeben (Abfrage)         4 B
0x0800A95C   Taste links freigeben                    4 B
0x0800A9B4   Taste rechts freigeben                   4 B
0x08014288   Sprung in den RAL-Bildschirm             4 B
0x0802E3D0   RAL-Bildschirm                        1328 B
0x0802E900   Farbtabelle mit 216 Farben            3732 B
```

Alles ab `0x08030000` — Startbild, Einstellungen und **Werkskalibrierung** —
bleibt unberührt. Die ist bei jedem Gerät anders.

Farbnamen und ihre Kodierung stammen aus der mitgelieferten Vorlage und
bleiben unverändert; ersetzt werden nur L, a, b und die Anzeigefarbe. Farben,
die in deiner CSV fehlen, behalten die Werte der Vorlage.

Die Dateien `_code.txt` und `_tab.txt` daneben enthalten den Bildschirmcode
und die Tabellenvorlage, gepackt und base64-kodiert.
