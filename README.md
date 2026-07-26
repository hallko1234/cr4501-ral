# Welches RAL ist das?

Das **3nh CR4501** misst Farben sehr genau — nur sagt es einem nicht, welcher
RAL-Ton dabei herauskommt. Dafür braucht es sonst Handy, App und Geduld.

Diese Erweiterung legt die Antwort direkt aufs Display: Nach jeder Messung
steht dort die nächstliegende RAL-Classic-Farbe mit Namen und wie gut sie
passt. Messen, ablesen, weiter.

Nebenbei werden die Tasten freigegeben, die die Werksfirmware auf den
Messansichten sperrt — links, rechts und die Eingabetaste tun danach das,
was man von ihnen erwartet.

**→ [Werkzeug öffnen](https://hallko1234.github.io/cr4501-ral/)**

Alles läuft im Browser. Es wird nichts hochgeladen, es gibt keinen Server,
und die Firmware deines Geräts verlässt deinen Rechner nicht.

---

## Bevor du anfängst

* **Chrome oder Edge.** Firefox und Safari können kein WebUSB.
* **Unter Windows** braucht das Gerät einmalig den WinUSB-Treiber, siehe unten.
* **Zeit:** fünf Minuten, davon vier fürs Warten.

## In den Aktualisierungsmodus

Das ist der einzige Handgriff, der etwas Gefühl braucht. Der zweite Schritt
ist der, den alle überspringen.

1. **Ausschalten** — Messtaste lange drücken, bis das Gerät ausgeht.
2. **Mindestens fünf Sekunden warten**, nichts anfassen. Ohne diese Pause
   reagiert das Gerät im nächsten Schritt nicht.
3. **Messtaste wieder lange halten**, bis der Ring um die Taste **rot blinkt**.
   Sofort loslassen.

Es geht auch anders herum: nach dem Ausschalten und den fünf Sekunden
Messtaste und Eingabetaste zusammen drücken — die Wippe dafür in der Mitte
hineindrücken. Das rote Blinken kommt dann sofort, gleich wieder loslassen.

Blinkt der Ring rot, ist das Gerät bereit. Der Bildschirm bleibt dabei dunkel,
das gehört so.

## Dann

1. Per USB anstecken, Werkzeug öffnen, **Gerät suchen**
2. **Auslesen und sichern** — die Datei aufheben, sie ist der Rückweg
3. **Einspielen** — das Werkzeug prüft vorher jede Änderungsstelle und bricht
   bei der kleinsten Abweichung ab
4. Gerät neu starten, messen, mit der Eingabetaste durch die Ansichten

## Treiber unter Windows

Windows liefert für den Aktualisierungsmodus keinen Treiber mit, den ein
Browser ansprechen kann. [Zadig](https://zadig.akeo.ie) erledigt das in einer
Minute:

1. Gerät im Aktualisierungsmodus anstecken
2. Zadig starten, *Options → List All Devices*
3. In der Liste **STM32 BOOTLOADER** (0483:DF11) auswählen
4. Rechts **WinUSB** einstellen, *Replace Driver*

Einmalig. Danach findet der Browser das Gerät jedes Mal.

---

## Was verändert wird

| Adresse | Änderung | Größe |
|---|---|---|
| `0x08014288` | RAL-Bildschirm einhängen | 4 B |
| `0x0800A9B4` | Taste rechts freigeben | 4 B |
| `0x0800A95C` | Taste links freigeben | 4 B |
| `0x0800A920` | Eingabetaste freigeben (Abfrage) | 4 B |
| `0x0800A69C` | Eingabetaste freigeben (Auswertung) | 4 B |
| `0x0802E3D0` | RAL-Bildschirm | 1328 B |
| `0x0802E900` | Farbtabelle, 216 Töne mit Namen | 3732 B |

Sieben Stellen, zusammen gut fünf Kilobyte, alles im Programmbereich
`0x08004000`–`0x0802FFFF`.

**Nicht angefasst wird alles ab `0x08030000`** — Startbild, Einstellungen und
vor allem die **Werkskalibrierung**. Die ist bei jedem Gerät anders. Eine
fremde hineinzuschreiben würde das Gerät dauerhaft falsch messen lassen, ohne
dass es jemand merkt. Das Werkzeug verweigert dort jeden Schreibzugriff.

## Woher die Farben kommen

216 RAL-Classic-Töne, mit einem Fächer eingemessen, jede Farbe dreimal.
Wiederholstreuung im Schnitt 0,08 ΔE, im schlechtesten Fall 0,50.

Je Eintrag zehn Byte: L, a und b als Ganzzahl mal hundert, dazu die RAL-Nummer
und ein Farbwert für die Anzeige. Die Namen liegen als gemeinsamer Textblock
dahinter, mit Verweisen statt Wiederholungen — anders hätte es nicht in den
freien Speicher gepasst.

Ehrlich dazugesagt: Die Werte stammen von *einem* Fächer und *einem* Gerät.
Fächer altern und vergilben, jedes Messgerät hat seine eigene Kalibrierung.
Für „welches RAL ist das ungefähr" ist das genau richtig. Für eine Abnahme
oder einen Reklamationsfall nimmt man weiterhin den Fächer in die Hand.

## Zurück zum Original

Im Werkzeug Schritt 4, gesicherte Datei auswählen, fertig. Falls die Seite
gerade nicht erreichbar ist, geht es auch mit
[dfu-util](https://dfu-util.sourceforge.net):

```
dfu-util -a 0 -s 0x08004000 -D cr4501_original_....bin
```

Zwei Dinge dabei: **niemals die Option `-t`**, und immer den gesamten
Programmbereich am Stück schreiben. Der Bootloader löscht beim ersten
Schreibbefehl den ganzen Bereich und erwartet danach das vollständige Abbild —
seitenweise zu schreiben zerstört alles andere.

## Haftung

Ein Feierabendprojekt, kein Produkt von 3nh, keine Garantie auf gar nichts.
Benutzung auf eigene Gefahr — aber mit gesichertem Rückweg, und die
Kalibrierung deines Geräts bleibt in jedem Fall unberührt.

Wenn das Werkzeug bei dir abbricht, weil es eine Firmware-Version nicht
kennt: melde dich, dann schaue ich sie mir an.
