# Colorimeter 3nh CR4501 RAL Hack

*[Deutsche Fassung](README.de.md)*

The **3nh CR4501** measures colour very accurately — it just won't tell you
which RAL tone that is. For that you're meant to reach for your phone, open an
app and pair over Bluetooth.

This modification puts the answer straight onto the device's own display:
after every measurement it shows the closest RAL Classic tone with its name and
how well it matches. Measure, read, move on.

<br>

<div align="center">

<table>
<tr><td align="center">

# 🔴 &nbsp; [START THE TOOL](https://hallko1234.github.io/cr4501-ral-hack/) &nbsp; 🔴

### Everything runs in your browser — nothing is uploaded

[![Open the tool](https://img.shields.io/badge/▶%20START%20THE%20TOOL-hallko1234.github.io-f7d117?style=for-the-badge&labelColor=e8622a&color=f7d117)](https://hallko1234.github.io/cr4501-ral-hack/)

**Chrome or Edge · five minutes · fully reversible**

</td></tr>
</table>

</div>

<br>

The tool walks you through it step by step: put the device into update mode,
check the driver, **back up first**, then flash, then try it out. Nothing is
uploaded, there is no server, and your device's firmware never leaves your
computer.

As a bonus it unlocks the buttons that the factory firmware disables on the
measurement screens — left, right and enter start doing what you'd expect.

---

## Before you start

* **Chrome or Edge.** Firefox and Safari cannot do WebUSB.
* **On Windows** the device needs the WinUSB driver once, see below.
* **Time:** five minutes, four of them waiting.

## Getting into update mode

The one step that takes a bit of feel. **The device must be switched off** —
hold the measure button until it turns off. Then wait **at least five seconds**
without touching anything; without that pause it won't respond.

**Option A** — hold the measure button again until the ring around it
**flashes red**. Let go immediately.

**Option B** — press the measure button and the enter button together, pushing
the rocker in at its centre. The red flash comes right away; let go at once.

When the ring flashes red the device is ready. The screen stays dark, that's
normal.

## Then

1. Plug in over USB, open the tool, **Find device**
2. **Read and back up** — keep that file, it is your way back
3. **Flash** — the tool checks every patch location beforehand and aborts on
   the slightest mismatch
4. Restart the device, measure, cycle through the views with the enter button

## Driver on Windows

Windows ships no driver for update mode that a browser is allowed to talk to.
[Zadig](https://zadig.akeo.ie) sorts that out in a minute:

1. Plug in the device in update mode
2. Start Zadig, *Options → List All Devices*
3. Select **STM32 DownLoad Firmware Update** (0483:DF11)
4. Set **WinUSB** on the right, then *Install Driver*

Once only. **It must be WinUSB** — not libusbK, not libusb-win32. Those work
with dfu-util but the browser won't see the device. That is the most common
mistake here.

---

## What gets changed

| Address | Change | Size |
|---|---|---|
| `0x08014288` | hook the RAL screen in | 4 B |
| `0x0800A9B4` | unlock right button | 4 B |
| `0x0800A95C` | unlock left button | 4 B |
| `0x0800A920` | unlock enter button (read function) | 4 B |
| `0x0800A69C` | unlock enter button (handler) | 4 B |
| `0x0802E3D0` | RAL screen | 1328 B |
| `0x0802E900` | colour table, 216 tones with names | 3732 B |

Seven locations, just over five kilobytes, all inside the application area
`0x08004000`–`0x0802FFFF`.

**Nothing above `0x08030000` is touched** — splash screen, settings and above
all the **factory calibration**. That is different on every device. Writing a
foreign one would make the instrument measure wrong for good, without anyone
noticing. The tool refuses any write access up there.

## Where the colours come from

216 RAL Classic tones, each colour measured three times. Repeatability
averaged 0.08 ΔE, worst case 0.50.

Measured with an **original RAL® K5 in semi-matt**. Its colour panels are
considerably larger than a fan deck's, so the 8 mm aperture sits well inside
the panel and catches no edges.

That is not a detail:
**replica colour cards from the accessories trade often deviate noticeably**,
sometimes by several ΔE, and they are not consistent among themselves. If your
reading disagrees with one of those, the card is usually to blame.

Ten bytes per entry: L, a and b as integers times a hundred, plus the RAL
number and a colour value for the display. The names sit behind that as a
shared block of word fragments with references rather than repetitions —
otherwise they would not have fit into the free memory.

Honestly said: these values come from *one* fan deck and *one* device. Fan
decks age and yellow, every instrument has its own calibration. For „roughly
which RAL is this" that is exactly right. For sign-off or a complaint, reach
for the fan deck.

## Measuring your own colours

The table shipped here comes from one fan deck and one device. If you want your
own values — a different deck, your own device, or simply as a check — the
program for that is under [werkzeug/](werkzeug/) (German).

It measures the 216 colours one after another, checks scatter and duplicate
readings, and builds the finished firmware from your own backup at the end.
You then flash that in the tool under *Restore a backup*.

```
python ral_einlernen.py COM3 --original cr4501_original_....bin
```

## Reference files

For disassembling or building on: the screen code, the colour table and the
original images from development are under [referenz/](referenz/).

**None of it is meant to be flashed blindly** — least of all the loader, which
carries one specific device's factory calibration. The reasons are in the
README there.

## Technical documentation

Memory map, button system, screen handling, measuring the colours, the USB
protocol and how to write the permanent memory:

**→ [doku/](doku/)** (German — but the addresses, byte sequences and tables
speak for themselves)

Every address in there is verified on the device or in the flash dump. It also
records what went wrong and why, which saves the expensive detours.

## Undoing it

In the tool, step 5, pick your backup file. If the page is unreachable, this
works too:

```
dfu-util -a 0 -s 0x08004000 -D your_backup.bin
```

Never use the `-t` option, and always write the whole region in one go — the
bootloader erases everything on the first write command and expects the
complete image afterwards.

## Liability

A weekend project, not a 3nh product, no warranty on anything. Use at your own
risk — but with a secured way back, and your device's calibration stays
untouched in every case.

If the tool aborts on your device because it doesn't recognise a firmware
version, get in touch and I'll take a look.

---

<div align="center">

### [▶  Open the tool](https://hallko1234.github.io/cr4501-ral-hack/)

</div>
