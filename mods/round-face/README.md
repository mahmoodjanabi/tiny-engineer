# Round face

Replaces the stock 0.91" OLED head with a **1.28" round TFT**: the [Waveshare 1.28inch LCD Module](https://www.waveshare.com/wiki/1.28inch_LCD_Module) (GC9A01, 240×240). Three printed parts replace stock `Head` and `Hat`; the rest of the robot is unchanged.

![Round face preview](round_face_preview.png)

> **Status: mechanical only.** Stock firmware drives the SSD1306 OLED over I2C and does not know about this display. The head is printable and checked for fit; the screen stays dark until GC9A01 support is added to the firmware.

## Parts

| Role | File | Replaces | Print |
| --- | --- | --- | --- |
| Head + display housing | `HeadRound` | `Head` | floor down, **supports on** (horizontal display bore, rear wings) |
| Front bezel ring | `BezelRound` | — (new) | face down, no supports |
| Lid | `HatRound` | `Hat` | flat like stock |

`parts/sg90/` only. Other servo presets need a regenerate (see below). Suggested colours: head in the body colour, bezel and hat in a contrast colour.

## What changed from stock

- Stock `Head` is kept whole behind x = −18.5 mm (print frame): pitch-servo pocket, neck-yoke pins, cable clips and hat seat are the untouched stock geometry. Only the OLED front wall is replaced.
- A Ø43.5 mm round housing is grafted on the front, display centre 16.7 mm above the pitch axis. Head with bezel: 53 × 53 × 46.75 mm (stock 48 × 53 × 14.6 + hat).
- **The display loads from the front** into a Ø38.1 bore and sits on a ledge. The **bezel** (1.4 mm face, Ø33.5 window, chin over the plinth) has a lip that presses into a Ø40.7 counterbore and clamps the display.
- **Cable exit at the top-back.** The module's socket faces up near the top edge, so the cable leaves through a slot in the top of the housing behind the display and runs back over the hat.
- `HatRound` is stock `Hat` trimmed at the front, with one new M2 hole at head (−14, −12.9); `HeadRound` has the matching boss. The rear hat screw is the stock one.

## Display module

Geometry from Waveshare's drawing: round PCB Ø37.5 with a 14.28 × 3.59 mm tab at the bottom (the LCD flex wraps around it), active area Ø32.4, PH2.0 8-pin side-entry socket on the back with its opening 11 mm above centre, facing up. Comes with a 20 cm PH2.0-to-female-jumper cable.

**Measure before printing:** panel + PCB thickness is not published. The design assumes `STACK = 3.6` mm plus 0.6 mm of foam tape. Measure the edge of your module with calipers; if it differs by more than ~0.5 mm, set `STACK` in the build script and regenerate.

Do not substitute the touch version or generic round GC9A01 boards: their PCB outlines and connectors differ.

## Assembly

1. Plug the PH2.0 cable into the module.
2. From the front, feed the cable through the bore and out of the slot at the top-back of the housing.
3. Put a few short pieces of thin foam tape (0.5–1 mm) on the ledge inside the bore.
4. Slide the module in from the front, tab down into the bottom notch, cable socket up.
5. Press `BezelRound` on: lip into the counterbore, chin down over the plinth. It is a slip fit; a dot of CA glue or a drop of hot glue on the lip if it is loose.
6. Fit the pitch servo and neck as in [docs/3d/assembly.md](../../docs/3d/assembly.md); those steps are unchanged.
7. Fit `HatRound` with two M2×8: stock hole at the rear, new hole at the front right.
8. Lay the cable back over the hat, leave a slack loop for nod and turn, and run it down the back with the servo lead.

The included cable is 20 cm. Head to the ESP32 in the desk is likely longer once you leave slack for head and body rotation; plan on 8 × 10 cm male–female jumper extensions.

## Wiring (for the firmware work)

Free ESP32-C3-Zero pins after the stock build: GP6, GP7, GP8, GP9, GP20, GP21. Proposed:

| Module | ESP32-C3-Zero | Note |
| --- | --- | --- |
| VCC | 3V3 | share via the PCA9685 far-end header, like the OLED |
| GND | GND | |
| CLK | GP6 | SPI SCK |
| DIN | GP7 | SPI MOSI |
| CS | GP20 | |
| DC | GP21 | |
| RST | GP9 | strapping pin, held high at boot; safe for an input that idles high |
| BL | GP8 | strapping pin; if flashing becomes unreliable, wire BL to 3V3 instead (always on) |

The stock OLED is no longer used; leave its I2C wires off.

## Fit checks

`3d_models/cad/check_round_face.py` models the module from Waveshare's drawing and checks, with booleans:

| Check | Result |
| --- | --- |
| Module seated vs head and bezel | no overlap |
| Module slid in from the front, every 0.5 mm of travel | no overlap |
| Bezel seated in head | no overlap |
| Hat seated on head | no overlap |
| Plug and 8-wire bundle leaving through the slot, over the hat | no overlap |
| Head mass (with display, 20 % infill) | ~30 g vs ~15 g stock |
| Static pitch-servo load | ~2.5 % of SG90 stall torque (stock ~0.4 %) |

**Not checked:** nod and turn clearance against the neck, chest and laptop. The repo has no assembled model to test against. The face sits 5 mm further forward and reaches ~3 mm lower at full nod than stock. Start with the HEAD servo minimum around 70° in the web UI (stock range 60–130°) and open it up after checking by hand.

## Regenerating

```bash
pip install trimesh manifold3d numpy
python3 mods/round-face/3d_models/cad/build_round_face.py 3d_models/parts/sg90/3mf mods/round-face/3d_models/parts/sg90/stl
python3 mods/round-face/3d_models/cad/check_round_face.py 3d_models/parts/sg90/3mf mods/round-face/3d_models/parts/sg90/stl
```

The build script writes `.stl` and `.3mf` to the output folder; copy the `.3mf` into `parts/sg90/3mf/`. There is no Fusion source for this mod; the script is the parametric source. Section view: `round_face_sections.png`.

## History

- **v2** — front-loading display with a separate `BezelRound`, cable slot at the top-back, module geometry from Waveshare's drawing, fit-check script. v1 could not be assembled: the bezel was moulded in and the back was closed, so the Ø37.5 module could not reach its pocket, and the cable exit was modelled at the wrong edge.
- **v1** — first version. Do not print.

## License

`3d_models/{cad,parts}/` are CERN-OHL-S-2.0, derived from the stock `Head` and `Hat`; see [`3d_models/NOTICE`](3d_models/NOTICE). This README is MIT like the rest of the docs.
