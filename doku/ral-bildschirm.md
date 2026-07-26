# Der RAL-Bildschirm (v18)

Der Bildschirm ist ein Maschinencode-Block von 1328 Byte bei `0x0802E3D0`.
Einen sauberen Quelltext dazu gibt es nicht — er ist über viele Iterationen
entstanden. Was hier steht, ist aus `app_ral_v18.bin` zurückgelesen.

## Einhängen

Die Firmware zeichnet die Ergebnisanzeige in `screen_values` bei
`0x08014288`. Deren erste vier Byte (`2d e9 f0 4f`, also `push {r4-r11,lr}`)
werden durch einen **Sprung ohne Link** ersetzt:

```
0x08014288:  f0 1a a2 b8      b.w 0x0802E3D0
```

Weil es `B.W` und nicht `BL` ist, bleibt das Rücksprungregister unangetastet —
der eigene Code kehrt am Ende direkt zum ursprünglichen Aufrufer zurück.

## Aufbau des eigenen Codes

```
0x0802E3D0  push {r4-r11,lr}          Prolog nachgebaut
            r6 = Tabellenbasis
            sub sp, #108
            bl 0x0802E88C             Trampolin
0x0802E3DC  ... Tabelle prüfen, suchen, zeichnen ...
0x0802E88C  Trampolin: push {r4-r11,lr}; bx 0x0801428D
0x0802E810  float → int ×100
0x0802E85A  Zahl in Text (rückwärts)
0x0802E89A  Ganzzahl-Wurzel (Newton)
0x0802E8B8  Text zentriert zeichnen
0x0802E69C  Literal: Tabellenbasis
```

Das Trampolin ist der Trick: Es holt den überschriebenen Prolog nach und
springt auf `Original+4`. Dessen Epilog `pop {r4-r11,pc}` kehrt dadurch in den
eigenen Code zurück, nicht zum Aufrufer.

## Tabellenformat

Die Basis steht als Literal bei `0x0802E69C`. Der Kopf liegt bei
**Basis + 0x400**:

| Offset | Inhalt |
|---|---|
| `+0x00` | Kennung `'MTP1'` = `0x3150544D` |
| `+0x04` | Zeiger auf die Einträge |
| `+0x08` | Anzahl der Farben |
| `+0x0C` | Zeiger auf den Namensblock |
| `+0x10` | Anzahl der Namen |
| `+0x14` | Zeiger auf die Namensvorlage |

Ein Eintrag ist zehn Byte:

```c
int16_t  L, a, b;      // ×100, also 7512 = L*75,12
uint16_t ral;          // 1000 … 9023
uint16_t rgb;          // RGB565 für den Hintergrund
```

## Die Namen sind komprimiert

216 deutsche Farbnamen hätten als Klartext nicht in den freien Speicher
gepasst. Deshalb liegen sie in zwei Teilen.

**Der Bausteinblock** (`Kopf+0x0C`, 226 Byte) enthält 40 nullterminierte
Wortstücke:

```
rau        gruen      blau       Verkehrs   orange     gelb
Signal     chwarz     Perl       rot        violett    weiss
Leucht     Pastell    eige       uerkis     ein        Gruen
liv        aluminium  ell        Gelb       urpur      Tele
Licht      Graphit    Bla        rosa       beer       enb
nen        Sch        Ocker      nster      Rot        ief
ach        nzian      Weiss      upfer
```

**Die Vorlage** (`Kopf+0x14`, 1282 Byte) enthält je Farbe eine
nullterminierte Bytefolge in derselben Reihenfolge wie die Einträge. Darin
gilt:

| Byte | Bedeutung |
|---|---|
| `< 0x80` | Zeichen im Klartext |
| `>= 0x80` | Baustein Nummer `byte − 0x80` |

Beispiel, der erste Name:

```
91 62 8e 00
│  │  └── Baustein 0x0E = 14 → "eige"
│  └───── Zeichen 'b'
└──────── Baustein 0x11 = 17 → "Gruen"
                              = "Gruenbeige"   (RAL 1000)
```

So kommt der gesamte Block auf 3732 Byte:

| Teil | Größe |
|---|---|
| Kopf | 32 B |
| 216 Einträge à 10 B | 2160 B |
| Bausteine | 226 B |
| Vorlage | 1282 B |
| Ausrichtung | 32 B |

Umlaute gibt es nicht — der Zeichensatz des Geräts ist GB2312 plus ASCII.
Deshalb steht auf dem Display `Gruengrau` und nicht `Grüngrau`.

Wer die Tabelle neu erzeugt, muss die Kodierung nicht nachbauen: Die Namen
ändern sich beim Nachmessen ja nicht. `werkzeug/firmware_bauen.py` nimmt die
vorhandene Vorlage und ersetzt darin nur L, a, b und die Anzeigefarbe.

## Was der Code tut

1. Kennung prüfen (`MTP1`), Anzahl auf 2…400 begrenzen
2. Lab aus dem RAM lesen, Fließkomma nach Ganzzahl ×100
3. Plausibilität: L zwischen 0,01 und 105, a und b jeweils ±130
4. Über alle Einträge laufen, quadratischen Abstand rechnen, besten und
   zweitbesten merken
5. Wurzel ziehen, Prozent = `100 − 4·dE`
6. Fläche füllen, RAL-Nummer, Name, Prozent und Zweitplatzierten zeichnen

Liegt einer der Prüfpunkte daneben, kehrt der Code **still zurück** und die
normale Anzeige bleibt stehen. Von außen sieht das aus, als hätte die
Umschaltung nicht funktioniert — bei der Fehlersuche daran denken.

## Lab-Puffer

Der Code liest bei `0x20000EC0`. Die Analyse nennt `0x20000ECC` als frischen
Messwert und `0x20000EC0` als Kalibrierpuffer — im Hook-Kontext ist es aber
nachweislich `0x20000EC0`, und die Anzeige stimmt. Nicht „korrigieren".

## Zeichenfunktionen der Firmware

```c
void fill_rect(int x1, int y1, int x2, int y2, uint16_t farbe);
```
Fünfter Parameter liegt auf dem Stapel; die Funktion reicht dessen **Adresse**
an den SPI-Schreiber weiter. Fensterbereich ist `(x1, y1, x2-1, y2-1)`,
Bildschirm 135 × 240.

```c
void fw_text(int x, int y, const char *s, int null, uint16_t farbe,
             int groesse, uint16_t hintergrund);
```
Drei Parameter auf dem Stapel. Größen 20, 24 und 32 sind belegt; bei Größe 20
sind es rund zehn Pixel je Zeichen, also dreizehn Zeichen pro Zeile.

## Nützliche Firmware-Adressen

| Adresse | Funktion |
|---|---|
| `0x0800AE24` | `fill_rect` |
| `0x0800B6D0` | Text zeichnen |
| `0x0800FA14` | `printf` |
| `0x0800FA64` | `sprintf` |
| `0x080042B0` | `strlen` |
| `0x08004E86` | `__aeabi_f2d` |
| `0x08011E3A` | Farbabstand dE |
| `0x08011F82` | XYZ → CIELAB |
| `0x0801957E` | Ereignis posten |
| `0x08007A1C` | `flash_write_page` |
