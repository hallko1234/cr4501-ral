# Referenzdateien

Die Originaldateien aus der Entwicklung. Zum Nachvollziehen, Disassemblieren
und Weiterbauen — **nicht** zum blinden Aufspielen.

| Datei | Größe | Was es ist |
|---|---|---|
| `ral_bildschirm.bin` | 1328 B | der RAL-Bildschirm als reiner Maschinencode |
| `ral_tabelle_216.bin` | 3732 B | die Farbtabelle im Format `MTP1` |
| `app_ral_v18.bin` | 180224 B | vollständiger Anwendungsbereich mit RAL-Anzeige |
| `daten_schreiben_geraet_J61973.bin` | 180224 B | Loader — **gerätespezifisch, siehe unten** |

---

## ⚠ daten_schreiben_geraet_J61973.bin

**Diese Datei gehört zu genau einem Gerät und darf auf keinem anderen
geflasht werden.**

Sie ist kein reiner Loader, sondern trägt einen vollständigen Abzug des
permanenten Speicherbereichs mit sich: Startbild, Menüeinstellungen und die
**Werkskalibrierung** des Geräts mit der Seriennummer J61973. Beim Ausführen
schreibt sie diesen Abzug ab `0x08030000` zurück.

Auf einem fremden Gerät ersetzt sie also dessen Werkskalibrierung durch eine
fremde. Das Gerät misst danach falsch — ohne Fehlermeldung, ohne sichtbares
Anzeichen, und der eigene Werkszustand ist unwiederbringlich weg.

Sie liegt hier, weil ihr Aufbau in
[../doku/permanenter-speicher.md](../doku/permanenter-speicher.md)
beschrieben ist und man ihn am Original nachvollziehen können soll. Wer selbst
einen Loader braucht, baut ihn aus dem Abzug **seines eigenen** Geräts.

**Für die RAL-Anzeige braucht man diese Datei nicht.** Die Tabelle liegt
inzwischen im Anwendungsbereich und wird beim normalen Flashen mitgeschrieben.

---

## app_ral_v18.bin

Der Stand, mit dem der RAL-Bildschirm zuerst stabil lief: Anwendungsbereich
`0x08004000`–`0x0802FFFF` mit Hook bei `0x08014288` und dem eigenen Code bei
`0x0802E3D0`. Die Farbtabelle steckt **nicht** darin — die lag damals noch bei
`0x08039400` im permanenten Speicher.

Zwei Gründe, das nicht einfach aufzuspielen:

* Es enthält die Firmware-Version dieses einen Geräts. Weicht deine ab, wäre
  es ein Versionswechsel, kein Patch.
* Ohne Tabelle bei `0x08039400` zeigt der RAL-Bildschirm nichts an.

Der bessere Weg ist das [Werkzeug auf der Projektseite](https://hallko1234.github.io/cr4501-ral-hack/)
oder `werkzeug/firmware_bauen.py` — beide bauen aus **deiner** Sicherung.

Nützlich ist die Datei zum Disassemblieren:

```
arm-none-eabi-objdump -D -b binary -m arm -Mforce-thumb \
  --adjust-vma=0x08004000 app_ral_v18.bin | less
```

## ral_bildschirm.bin

Der Bildschirmcode allein, wie er bei `0x0802E3D0` liegt. Aufbau, Trampolin
und Hilfsroutinen stehen in
[../doku/ral-bildschirm.md](../doku/ral-bildschirm.md).

Das Literal bei Offset `0x2CC` (Flash `0x0802E69C`) enthält die Basis der
Farbtabelle. Es steht hier noch auf `0x08039000`; wer den Code woanders hin
legt, setzt es auf `Tabellenadresse − 0x400`.

```
arm-none-eabi-objdump -D -b binary -m arm -Mforce-thumb \
  --adjust-vma=0x0802E3D0 ral_bildschirm.bin
```

## ral_tabelle_216.bin

216 RAL-Classic-Töne, eingemessen mit einem Fächer, je drei Messungen.
Format `MTP1`, Aufbau und Namenskompression in
[../doku/ral-bildschirm.md](../doku/ral-bildschirm.md).

Die Zeiger im Kopf zeigen noch auf die alte Lage `0x08039400`. Beim Verschieben
alle drei um die Differenz verschieben — `werkzeug/firmware_bauen.py` macht
genau das.

Auslesen lässt sie sich mit ein paar Zeilen:

```python
import struct
d = open('ral_tabelle_216.bin','rb').read()
kopf = struct.unpack('<8I', d[:32])
basis, eintraege, anzahl = 0x08039400, kopf[1]-0x08039400, kopf[2]
for i in range(anzahl):
    L,a,b,ral,rgb = struct.unpack('<hhhHH', d[eintraege+i*10:eintraege+i*10+10])
    print(ral, L/100, a/100, b/100)
```

---

## Rechtliches

`ral_bildschirm.bin` und `ral_tabelle_216.bin` sind eigene Arbeit. Die beiden
vollständigen Abbilder enthalten dagegen die Gerätefirmware von 3nh und liegen
hier ausschließlich zur Analyse des eigenen, gekauften Geräts.
