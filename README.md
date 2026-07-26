# CR4501 · RAL-Anzeige

Firmware-Erweiterung für das Farbmessgerät **3nh CR4501**. Nach jeder Messung
zeigt das Gerät die nächstgelegene RAL-Classic-Farbe mit Namen und
Übereinstimmung direkt auf dem Display — ohne PC, ohne App.

Zusätzlich werden die Tasten freigegeben, die die Werksfirmware auf den
Messansichten sperrt.

**Werkzeug:** https://hallko1234.github.io/cr4501-ral/

Das Einspielen läuft vollständig im Browser über WebUSB. Es wird nichts
hochgeladen, es gibt keinen Server.

---

## Voraussetzungen

* Chrome oder Edge (Firefox und Safari können kein WebUSB)
* Unter Windows: einmalig der WinUSB-Treiber für das DFU-Gerät, siehe unten
* Ein 3nh CR4501

## Ablauf

1. Gerät ausschalten, Messtaste gedrückt halten, einschalten. Der Bildschirm
   bleibt dunkel — das ist der Aktualisierungsmodus.
2. Per USB anstecken, Werkzeugseite öffnen, **Gerät suchen**.
3. **Auslesen und sichern.** Die Datei aufbewahren, sie ist der Rückweg.
4. **Einspielen.** Das Werkzeug prüft vorher jede Änderungsstelle gegen den
   erwarteten Originalinhalt und bricht bei der kleinsten Abweichung ab.
5. Gerät neu starten. Messen. Mit der Eingabetaste zwischen den Ansichten
   wechseln.

## Treiber unter Windows

Windows liefert für das DFU-Gerät keinen Treiber mit, den der Browser
ansprechen kann. Abhilfe schafft [Zadig](https://zadig.akeo.ie):

1. Gerät im Aktualisierungsmodus anstecken
2. Zadig starten, *Options → List All Devices*
3. In der Liste **STM32 BOOTLOADER** (0483:DF11) wählen
4. Rechts **WinUSB** einstellen, *Replace Driver*

Danach findet der Browser das Gerät. Der Schritt ist einmalig.

## Was geändert wird

| Adresse | Änderung | Größe |
|---|---|---|
| `0x08014288` | RAL-Bildschirm einhängen | 4 B |
| `0x0800A9B4` | Taste rechts freigeben | 4 B |
| `0x0800A95C` | Taste links freigeben | 4 B |
| `0x0800A920` | Eingabetaste freigeben (Abfrage) | 4 B |
| `0x0800A69C` | Eingabetaste freigeben (Auswertung) | 4 B |
| `0x0802E3D0` | RAL-Bildschirm | 1328 B |
| `0x0802E900` | Farbtabelle, 216 Töne mit Namen | 3732 B |

Alles liegt im Anwendungsbereich `0x08004000`–`0x0802FFFF`.

**Der Bereich ab `0x08030000` wird nicht angefasst.** Dort liegen Startbild,
Einstellungen und die *gerätespezifische Werkskalibrierung*. Das Werkzeug
verweigert jeden Schreibzugriff darüber — eine fremde Kalibrierung
einzuspielen würde das Gerät dauerhaft falsch messen lassen.

## Die Farbtabelle

216 RAL-Classic-Töne, mit einem RAL-Fächer eingemessen, je drei Messungen.
Wiederholstreuung im Mittel 0,08 ΔE, im schlechtesten Fall 0,50.

Je Eintrag zehn Byte: L, a, b als Ganzzahl mal 100, dazu RAL-Nummer und ein
Farbwert für die Anzeige. Die Namen liegen als gemeinsamer Textblock mit
Verweisen dahinter.

Die Werte stammen von *einem* Fächer und *einem* Gerät. Für die
Farberkennung im Alltag reicht das gut; als Referenz für Abnahmen ist es
nicht gedacht.

## Zurück zum Original

Im Werkzeug unter Schritt 4 die gesicherte Datei wählen. Falls die Seite
nicht erreichbar ist, geht es auch mit
[dfu-util](https://dfu-util.sourceforge.net):

```
dfu-util -a 0 -s 0x08004000 -D cr4501_original_....bin
```

Niemals die Option `-t` verwenden und immer den gesamten Anwendungsbereich am
Stück schreiben. Der Bootloader löscht beim ersten Schreibbefehl den ganzen
Bereich und erwartet danach das vollständige Abbild.

## Haftung

Privates Projekt, kein Produkt von 3nh. Benutzung auf eigene Gefahr — aber
mit gesichertem Rückweg. Die Werkskalibrierung bleibt in jedem Fall
unberührt.
