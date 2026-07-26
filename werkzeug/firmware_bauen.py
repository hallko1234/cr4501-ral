#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
firmware_bauen.py  --  aus Messwerten und Originalfirmware eine fertige Datei bauen

Nimmt die Originalfirmware des eigenen Geraets (die Sicherung, die das
Webwerkzeug beim Auslesen anlegt) und baut daraus eine Datei mit RAL-Anzeige.
Die eingemessenen Farbwerte kommen aus ral_fortschritt.csv.

Das Ergebnis ist ein vollstaendiges Abbild von 180224 Byte. Es laesst sich
mit dem Webwerkzeug unter "Sicherung einspielen" flashen oder mit dfu-util:

    dfu-util -a 0 -s 0x08004000 -D cr4501_ral.bin

Als eigenstaendiges Programm:

    python firmware_bauen.py original.bin ral_fortschritt.csv [ausgabe.bin]

Was hineingeschrieben wird
    0x0800A69C   Eingabetaste freigeben (Auswertung)
    0x0800A920   Eingabetaste freigeben (Abfrage)
    0x0800A95C   Taste links freigeben
    0x0800A9B4   Taste rechts freigeben
    0x08014288   Sprung in den RAL-Bildschirm
    0x0802E3D0   RAL-Bildschirm, 1328 B
    0x0802E900   Farbtabelle, 3732 B

Nicht angefasst wird alles ab 0x08030000 - Startbild, Einstellungen und die
Werkskalibrierung des Geraets. Die ist bei jedem Geraet anders.
"""

import sys, os, csv, math, struct, base64, zlib

APP_START   = 0x08004000
APP_LAENGE  = 180224
GRENZE      = 0x08030000
CODE_ADR    = 0x0802E3D0          # RAL-Bildschirm
TAB_ADR     = 0x0802E900          # Farbtabelle
LITERAL_ADR = 0x0802E69C          # im Bildschirmcode: Basis der Tabelle
HOOK_ADR    = 0x08014288          # screen_values

# Erwartete Originalbytes -> Ersatz
PATCHES = [
    (0x08014288, '2de9f04f', '1af0a2b8', 'RAL-Bildschirm einhaengen'),
    (0x0800A9B4, '90f87002', '002000bf', 'Taste rechts freigeben'),
    (0x0800A95C, '90f87002', '002000bf', 'Taste links freigeben'),
    (0x0800A920, '90f87002', '002000bf', 'Eingabetaste freigeben (Abfrage)'),
    (0x0800A69C, '91f87012', '002100bf', 'Eingabetaste freigeben (Auswertung)'),
]

_HIER = os.path.dirname(os.path.abspath(__file__))


def _laden(name):
    with open(os.path.join(_HIER, name), 'r') as f:
        return zlib.decompress(base64.b64decode(f.read()))


def lab_zu_rgb565(L, a, b):
    """Lab -> RGB565 fuer den Hintergrund auf dem Display."""
    y = (L + 16) / 116.0
    x = a / 500.0 + y
    z = y - b / 200.0
    def inv(t):
        return t ** 3 if t ** 3 > 0.008856 else (t - 16 / 116.0) / 7.787
    X, Y, Z = inv(x) * 0.95047, inv(y), inv(z) * 1.08883
    r = X * 3.2406 - Y * 1.5372 - Z * 0.4986
    g = -X * 0.9689 + Y * 1.8758 + Z * 0.0415
    bl = X * 0.0557 - Y * 0.2040 + Z * 1.0570
    def gam(c):
        c = max(0.0, min(1.0, c))
        return 1.055 * c ** (1 / 2.4) - 0.055 if c > 0.0031308 else 12.92 * c
    R, G, Bl = [int(round(gam(c) * 255)) for c in (r, g, bl)]
    return ((R >> 3) << 11) | ((G >> 2) << 5) | (Bl >> 3)


def messwerte_lesen(pfad):
    """ral_fortschritt.csv -> {ral: (L, a, b)}"""
    werte = {}
    with open(pfad, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            werte[int(r['ral'])] = (float(r['L']), float(r['a']), float(r['b']))
    return werte


def tabelle_bauen(werte, basis=TAB_ADR, melden=print):
    """Vorlage nehmen, Messwerte eintragen, Zeiger auf die neue Basis setzen.

    Farbnamen und ihre Kodierung bleiben unveraendert - die aendern sich beim
    Nachmessen ja nicht. Ersetzt werden nur L, a, b und die Anzeigefarbe.
    """
    tab = bytearray(_laden('_tab.txt'))
    kopf = list(struct.unpack('<8I', tab[:32]))
    assert kopf[0] == 0x3150544D, 'Vorlage beschaedigt'
    alt_basis = 0x08039400                     # Lage in der Vorlage
    anzahl = kopf[2]
    eintraege = kopf[1] - alt_basis            # Offset innerhalb der Vorlage

    getroffen = 0
    for i in range(anzahl):
        p = eintraege + i * 10
        L, a, b, ral, rgb = struct.unpack('<hhhHH', tab[p:p + 10])
        if ral in werte:
            nL, na, nb = werte[ral]
            struct.pack_into('<hhhHH', tab, p,
                             int(round(nL * 100)), int(round(na * 100)),
                             int(round(nb * 100)), ral, lab_zu_rgb565(nL, na, nb))
            getroffen += 1

    for n in (1, 3, 5):                        # Zeiger auf die neue Lage
        kopf[n] += basis - alt_basis
    tab[:32] = struct.pack('<8I', *kopf)

    melden('  Tabelle: %d von %d Farben aus den Messwerten uebernommen'
           % (getroffen, anzahl))
    if getroffen < anzahl:
        melden('  %d Farben stammen weiterhin aus der Vorlage'
               % (anzahl - getroffen))
    return bytes(tab)


def bauen(original, tabelle, melden=print):
    """Fertiges Abbild aus Originalfirmware und Farbtabelle."""
    if len(original) != APP_LAENGE:
        raise ValueError('Die Originaldatei ist %d Byte gross, erwartet werden %d.\n'
                         'Das muss die Sicherung des Anwendungsbereichs sein, '
                         'nicht der vollstaendige Abzug.' % (len(original), APP_LAENGE))
    neu = bytearray(original)
    def off(a): return a - APP_START

    for adr, alt, ers, was in PATCHES:
        ist = bytes(neu[off(adr):off(adr) + 4]).hex()
        if ist == ers:
            raise ValueError('Bei 0x%08X steht bereits der Patch - diese Datei '
                             'ist schon umgebaut.' % adr)
        if ist != alt:
            raise ValueError('Bei 0x%08X steht %s statt %s.\nDiese Firmware-Version '
                             'kenne ich nicht - bitte melden.' % (adr, ist, alt))

    code = bytearray(_laden('_code.txt'))
    struct.pack_into('<I', code, LITERAL_ADR - CODE_ADR, TAB_ADR - 0x400)

    for adr, blob, was in ((CODE_ADR, code, 'RAL-Bildschirm'),
                           (TAB_ADR, tabelle, 'Farbtabelle')):
        if adr + len(blob) > GRENZE:
            raise ValueError('%s wuerde ueber 0x%08X hinausreichen' % (was, GRENZE))
        bereich = neu[off(adr):off(adr) + len(blob)]
        if any(x != 0xFF for x in bereich):
            raise ValueError('Der Bereich ab 0x%08X ist belegt - laeuft schon eine '
                             'Erweiterung auf dieser Firmware?' % adr)
        neu[off(adr):off(adr) + len(blob)] = blob
        melden('  0x%08X  %-16s %5d B' % (adr, was, len(blob)))

    for adr, alt, ers, was in PATCHES:
        neu[off(adr):off(adr) + 4] = bytes.fromhex(ers)
        melden('  0x%08X  %-16s     4 B' % (adr, was))

    return bytes(neu)


def aus_dateien(original_pfad, csv_pfad, ausgabe_pfad=None, melden=print):
    melden('Original:   %s' % original_pfad)
    melden('Messwerte:  %s' % csv_pfad)
    original = open(original_pfad, 'rb').read()
    werte = messwerte_lesen(csv_pfad)
    melden('')
    tabelle = tabelle_bauen(werte, melden=melden)
    fertig = bauen(original, tabelle, melden=melden)
    if ausgabe_pfad is None:
        ausgabe_pfad = 'cr4501_ral.bin'
    with open(ausgabe_pfad, 'wb') as f:
        f.write(fertig)
    melden('')
    melden('Fertig: %s  (%d Byte)' % (ausgabe_pfad, len(fertig)))
    melden('')
    melden('Einspielen mit dem Webwerkzeug unter "Sicherung einspielen"')
    melden('oder mit:  dfu-util -a 0 -s 0x08004000 -D %s' % ausgabe_pfad)
    return ausgabe_pfad


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit('Aufruf: python firmware_bauen.py original.bin ral_fortschritt.csv '
                 '[ausgabe.bin]')
    try:
        aus_dateien(sys.argv[1], sys.argv[2],
                    sys.argv[3] if len(sys.argv) > 3 else None)
    except Exception as e:
        sys.exit('\nAbgebrochen: %s' % e)
