# Bildschirme und Umschaltung

## Es gibt nur zwei Zeichenfunktionen

```
0x08014288   screen_values    Messansicht
0x080138B0   screen_compare   Vergleich / Pass
```

Eine Bildschirmtabelle oder Registrierung existiert **nicht**. Wer eine dritte
Ansicht will, muss sich in die vorhandene Auswahl einhängen.

## Das Modus-Byte

Ausgewählt wird über ein einzelnes Byte im RAM bei `0x2000001C`. Im gesamten
Programm greifen nur drei Stellen darauf zu:

| Adresse | was |
|---|---|
| `0x08006CD6` | in `FUN_08006CD0` — die einzige Lesestelle |
| `0x08006DE2` | schreibt nur 0 |
| `0x0800B80A` | schreibt nur 0 |

Ein **dritter Wert ist deshalb unbedenklich**. Eine frühere Vermutung, das
Byte werde an vielen Stellen gelesen, war falsch.

Der Verteiler steht am Ende von `FUN_08006CD0`:

```
0x08006DA0  ldrb r0,[r5]          r5 = &modus
            cbz  r0, →  b.w 0x08014288    screen_values
            cmp  r0,#1 → b.w 0x080138B0   screen_compare
0x08006DBC  sonst: einfach zurück          ← hier ist Platz
```

Umgeschaltet wird das Byte im selben Verteiler bei Ereignis `0x10`, und zwar
nur, wenn ein Datensatz ausgewählt ist. Der Übergang 1 → 0 liegt bei
`0x08006D8A`.

## Die Screen-ID ist eine Sackgasse

Das Byte bei `0x200044D4` (Konfigbasis `0x20004264` + `0x270`) sieht nach einer
Bildschirmverwaltung aus und wird überall abgefragt — aber vom UI **nie
geschrieben**. Nur das USB-Kommando `0xA2` setzt es. Es steht dauerhaft auf
`0x15`.

Alle Versuche, darüber umzuschalten, mussten scheitern. Das hat mehrere
Anläufe gekostet.

## Zwei Wege zur dritten Ansicht

**A — eigenes Flaggen-Byte.** Ein freies RAM-Byte (etwa `0x20001051` in der
Tastentabelle), umgeschaltet über ein Ereignis, und ein Haken in
`screen_values`, der bei gesetzter Flagge den eigenen Bildschirm zeichnet.
Greift zuverlässig, weil **alle** Zeichenpfade durch `screen_values` laufen —
auch `FUN_08006DDC` und `0x0800B7F8`, die direkt zeichnen.

**B — dritter Wert im Modus-Byte.** Die Drehung bei `0x08006D8A` auf
1 → 2 → 0 erweitern und den Verteiler um einen Zweig für 2 ergänzen. Näher am
Original, weil dieselbe Taste und dieselbe Logik wie bei Messung ↔ Pass.

Wichtig bei beiden: Ein Haken **nur** am Verteiler reicht nicht. Andere Pfade
zeichnen direkt und überschreiben das Ergebnis Sekundenbruchteile später —
das sieht dann aus, als würde die Umschaltung nicht greifen, obwohl der Code
sauber durchläuft.

## Die Ampelfarbe der Prozentzahl

Liegen erster und zweiter Treffer weniger als 4 % auseinander, wird die
Prozentzahl orange statt grün hinterlegt — ein Hinweis, dass die Messung
allein nicht entscheiden kann.
