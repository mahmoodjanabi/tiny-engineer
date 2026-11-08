"""Round-face mod for Tiny Engineer: graft a housing for the Waveshare 1.28inch LCD
Module (GC9A01, 240x240) onto the stock Head, plus a separate front bezel and a
trimmed Hat.

v2: the module loads from the FRONT and is clamped by a press-fit bezel ring.
(v1 had the bezel moulded in and a closed back, so the 37.5 mm module could not
get into its pocket from either side.)

Module (Waveshare drawing): round PCB d37.5 with a 14.28 x 3.59 tab at the bottom
(the LCD flex wraps around it). PH2.0 8-pin side-entry socket on the back, centred,
opening faces UP 11.0 mm above the board centre; the cable leaves past the top edge.
Panel + PCB stack is not published: STACK below is an estimate, measure yours.

Head coordinates = stock Head.3mf print frame: +x = back, -x = front (face),
y = left/right (box y +-16.45), z = up (floor z=0, hat seat z=14.6).
Pitch axis: x=-2, z=8.3.

Usage: python3 build_round_face.py <stock sg90 3mf dir> <out dir>
Writes HeadRound, BezelRound, HatRound as .stl and .3mf, each in print orientation.
"""
import sys, numpy as np, trimesh
from trimesh.creation import box, cylinder
from trimesh.transformations import rotation_matrix as rot

SRC = sys.argv[1]
OUT = sys.argv[2]

# ---- parameters (mm) ------------------------------------------------------------
CUT_X      = -18.5          # stock head is kept behind this plane, replaced in front
FRONT_X    = -31.0          # bezel front face
BEZEL_T    = 1.4            # bezel face thickness
X_H        = FRONT_X + BEZEL_T   # housing front = display glass front
ZC         = 25.0           # display centre height (16.7 above the pitch axis)
R_OUT      = 21.75          # housing / bezel outer radius (d43.5)
R_MOD      = 37.5 / 2       # module PCB / panel radius
R_BORE     = R_MOD + 0.30   # module bore d38.1
R_CB       = 40.70 / 2      # counterbore for the bezel lip
CB_D       = 2.0
STACK      = 3.6            # panel + PCB thickness (estimate; measure and edit)
FOAM       = 0.6            # foam tape behind the PCB edge, takes up STACK tolerance
X_SEAT     = X_H + STACK + FOAM  # ledge the PCB edge sits on
R_BEHIND   = 17.0           # cavity behind the ledge (back components, connector)
BACKWALL_X = -20.0
TAB_HALF   = 14.28 / 2 + 0.45
TAB_DROP   = 3.59 + 0.40
CABLE_HALF = 11.0           # cable slot, top-back, |y| < 11
CABLE_Z0   = ZC + 10.5      # socket opening is at ZC + 11.0
R_WIN      = 33.5 / 2       # bezel window (active area d32.4)
LIP_OD     = 40.50
LIP_ID     = 38.50
LIP_D      = 1.9
PLINTH_Y   = 11.0
BOX_HALF_Y = 16.45
HAT_BOSS   = (-14.0, -12.9) # new hat screw (stock front boss is cut away)
HAT_OFF    = -8.1           # hat print frame x = head x + HAT_OFF


def X(mesh):
    mesh.apply_transform(rot(np.pi / 2, [0, 1, 0]))
    return mesh

def cyl_x(r, x0, x1, y=0.0, z=ZC, sections=160):
    c = X(cylinder(radius=r, height=x1 - x0, sections=sections))
    c.apply_translation([(x0 + x1) / 2, y, z])
    return c

def bx(x0, x1, y0, y1, z0, z1):
    b = box(extents=[x1 - x0, y1 - y0, z1 - z0])
    b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return b

def zcyl(r, cx, cy, z0, z1, sections=48):
    c = cylinder(radius=r, height=z1 - z0, sections=sections)
    c.apply_translation([cx, cy, (z0 + z1) / 2])
    return c

def load(name):
    s = trimesh.load(f"{SRC}/{name}.3mf", force="scene")
    return trimesh.util.concatenate(list(s.geometry.values()))

U = lambda *ms: trimesh.boolean.union(list(ms), engine="manifold")
D = lambda a, b: trimesh.boolean.difference([a, b], engine="manifold")

def clean(m):
    m.merge_vertices()
    m.update_faces(m.nondegenerate_faces())
    return m

def export(m, name):
    m.export(f"{OUT}/{name}.stl")
    m.export(f"{OUT}/{name}.3mf")
    print(f"{name}: watertight={m.is_watertight} size={np.round(m.extents, 2)} vol={round(m.volume)} mm3")


# ---- HeadRound --------------------------------------------------------------------
def build_head():
    head = load("Head")
    head = D(head, bx(-40, CUT_X, -40, 40, -5, 40))           # stock OLED front wall
    head = D(head, bx(-19.5, -13.0, 5.0, 14.4, 1.8, 14.6))    # stock OLED end-pocket stub

    solid = U(head,
              bx(-26.0, CUT_X + 0.01, -BOX_HALF_Y, BOX_HALF_Y, 0.0, 14.6),  # box envelope
              cyl_x(R_OUT, X_H, CUT_X + 0.01),                              # housing
              bx(X_H, CUT_X + 0.01, -PLINTH_Y, PLINTH_Y, 0.0, 4.0),         # plinth / chin
              zcyl(2.6, *HAT_BOSS, 1.8, 14.6))                              # hat screw boss
    solid = D(solid, bx(-40, CUT_X + 1, -40, 40, -10, 0.0))                 # flat floor

    for c in [
        cyl_x(R_CB, X_H - 1, X_H + CB_D),                                    # bezel lip counterbore
        cyl_x(R_BORE, X_H - 1, X_SEAT),                                      # module bore (front-loading)
        cyl_x(R_BEHIND, X_SEAT - 0.01, BACKWALL_X),                          # cavity behind the ledge
        bx(X_H - 1, BACKWALL_X, -TAB_HALF, TAB_HALF,
           ZC - R_MOD - TAB_DROP, ZC - R_BEHIND + 0.5),                      # tab + flex slot
        bx(X_H + STACK, CUT_X + 1.0, -CABLE_HALF, CABLE_HALF,
           CABLE_Z0, ZC + R_OUT + 1),                                        # cable exit, top-back
        bx(BACKWALL_X - 0.01, CUT_X + 0.5, -14.0, 14.0, 2.0, 14.6),          # opening into the box
        zcyl(1.0, *HAT_BOSS, 14.6 - 9.0, 14.7),                              # M2 pilot for the hat
    ]:
        solid = D(solid, c)
    return clean(solid)


# ---- BezelRound (built in head frame, exported face-down) -------------------------
def build_bezel(head_frame=False):
    face = U(cyl_x(R_OUT, FRONT_X, X_H),
             bx(FRONT_X, X_H, -PLINTH_Y, PLINTH_Y, 0.0, ZC))                # chin covers the plinth front
    face = D(face, bx(-40, -20, -40, 40, -10, 0.0))
    face = D(face, cyl_x(R_WIN, FRONT_X - 1, X_H + 1))                      # window
    lip = D(cyl_x(LIP_OD / 2, X_H - 0.01, X_H + LIP_D),
            cyl_x(LIP_ID / 2, X_H - 1, X_H + LIP_D + 1))
    lip = D(lip, bx(X_H - 1, X_H + LIP_D + 1, -TAB_HALF - 0.3, TAB_HALF + 0.3,
                    ZC - 30, ZC - R_BEHIND))                                # notch for the tab
    bezel = clean(U(face, lip))
    if head_frame:
        return bezel
    p = bezel.copy()
    p.apply_transform(rot(-np.pi / 2, [0, 1, 0]))                           # face on the bed
    p.apply_translation(-p.bounds[0])
    return p


# ---- HatRound -----------------------------------------------------------------------
def build_hat():
    hat = load("Hat")
    hat = D(hat, bx(-50, CUT_X + 0.3 + HAT_OFF, -40, 40, -5, 10))           # clear the housing
    hat = D(hat, zcyl(1.2, HAT_BOSS[0] + HAT_OFF, HAT_BOSS[1], -1, 10))      # M2 clearance hole
    return clean(hat)


if __name__ == "__main__":
    export(build_head(), "HeadRound")
    export(build_bezel(), "BezelRound")
    export(build_hat(), "HatRound")
