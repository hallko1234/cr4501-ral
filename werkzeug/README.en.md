# Tools

*[Deutsche Fassung](README.md)*

## ral_einlernen.py

Measures the RAL fan deck with the CR4501: 216 colours, each three times, with
sanity checks — and builds the finished firmware from it on request.

```
python -m pip install pyserial openpyxl
python ral_einlernen.py COM3 --original cr4501_original_....bin
```

The program names the next colour, you put the card on and press the button on
the device. That's all — no typing. After three clean readings it moves on by
itself.

**The original file** is the backup the tool on the project page writes when
reading the device out: 180224 bytes, your device's application area. From it
and your measurements it builds `cr4501_ral.bin`, which you flash back in the
web tool under *Restore a backup*.

Without `--original` it only measures; you can build the firmware later:

```
python ral_einlernen.py --nur-bauen --original cr4501_original_....bin
```

The program's own output is in German.

### What is checked

| Check | Threshold | Reaction |
|---|---|---|
| Same card measured twice | under 1.0 ΔE to the previous colour | discarded |
| Scatter across the three readings | over 1.5 ΔE between them | outlier discarded |
| Comparison with the expected value | over 18 ΔE from nominal | warning, value still counts |

After four outliers in a row the colour starts over. Progress is written to
`ral_fortschritt.csv` after every colour — pressing Ctrl+C is harmless, the
next start picks up where you left off.

At the end it also writes `ral_einlernung.xlsx` with nominal and measured
values, scatter, deviation and a colour preview.

### Important before you start

**Keep illuminant and observer the same throughout**, D65/10° for example. If
the combination changes midway the values are no longer comparable — and with
an invalid combination the device returns nonsense such as L\*=511. The reason
is in [doku/einlernen.md](../doku/einlernen.md) (German).

Calibrate black and white first.

## firmware_bauen.py

The builder on its own, if you need it separately:

```
python firmware_bauen.py original.bin ral_fortschritt.csv [output.bin]
```

It compares the expected original bytes at each of the seven patch locations
and aborts on the slightest mismatch rather than writing on the off chance. If
the file has already been patched, it says so too.

What gets written:

```
0x0800A69C   unlock enter button (handler)             4 B
0x0800A920   unlock enter button (read function)       4 B
0x0800A95C   unlock left button                        4 B
0x0800A9B4   unlock right button                       4 B
0x08014288   hook the RAL screen in                    4 B
0x0802E3D0   RAL screen                             1328 B
0x0802E900   colour table with 216 colours           3732 B
```

Everything above `0x08030000` — splash screen, settings and **factory
calibration** — stays untouched. That is different on every device.

Colour names and their encoding come from the bundled template and stay as they
are; only L, a, b and the display colour are replaced. Colours missing from
your CSV keep the template's values.

The files `_code.txt` and `_tab.txt` next to it hold the screen code and the
table template, compressed and base64-encoded.
