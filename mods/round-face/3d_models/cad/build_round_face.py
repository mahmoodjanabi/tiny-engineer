"""Graft a round GC9A01 (Waveshare 1.28" LCD Module) housing onto the stock
Tiny Engineer Head. Interfaces (pitch servo pocket, neck yoke pins, hat seat,
cable clips) are the untouched stock mesh. Only the OLED front wall is replaced.

Head coordinates = stock Head.3mf print frame: +x = back, -x = front,
y = left/right (box is y ±16.45), z = up (floor z=0, hat seat z=14.6).
"""
import sys, numpy as np, trimesh
from trimesh.creation import box, cylinder
from trimesh.transformations import rotation_matrix as rot

SRC = sys.argv[1]      # folder with stock Head.3mf / Hat.3mf
OUT = sys.argv[2]   # stl + 3mf are written here

# ---- parameters --------------------------------------------------------------
CUT_X      = -18.5     # everything in front of this plane is replaced
FRONT_X    = -31.0     # new bezel face
BEZEL_T    = 1.4
POCKET_D   = 4.0       # module depth in front of the cavity (display + PCB)
BACKWALL_X = -20.0     # rear wall of the housing starts here (to CUT_X)
ZC         = 25.0      # face centre height (pitch axis is z=8.2)
R_OUT      = 21.75     # housing Ø43.5
R_PCB      = 38.1 / 2  # Waveshare PCB Ø37.5 + 0.6 clearance
R_WIN      = 33.5 / 2  # active area Ø32.4
TAB_W, TAB_R = 20.0, 3.7   # connector tab slot, at the bottom (PH2.0 8P is ~18.5 long)
BOX_HALF_Y = 16.45
HAT_BOSS   = (-14.0, -12.9)   # new hat screw boss (stock boss A is removed)

def X(mesh):  # rotate a z-axis primitive to the x axis
    mesh.apply_transform(rot(np.pi / 2, [0, 1, 0]))
    return mesh

def cyl_x(r, x0, x1, y=0.0, z=ZC, sections=128):
    c = X(cylinder(radius=r, height=x1 - x0, sections=sections))
    c.apply_translation([(x0 + x1) / 2, y, z])
    return c

def bx(x0, x1, y0, y1, z0, z1):
    b = box(extents=[x1 - x0, y1 - y0, z1 - z0])
    b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return b

def load(name):
    s = trimesh.load(f"{SRC}/{name}.3mf", force="scene")
    return trimesh.util.concatenate(list(s.geometry.values()))

def U(a, b): return trimesh.boolean.union([a, b], engine="manifold")
def D(a, b): return trimesh.boolean.difference([a, b], engine="manifold")

# ---- head --------------------------------------------------------------------
head = load("Head")
head = D(head, bx(-40, CUT_X, -40, 40, -5, 40))              # drop OLED front wall
head = D(head, bx(-19.5, -13.0, 5.0, 14.4, 1.8, 14.6))       # drop OLED end-pocket stub

bridge  = bx(-26.0, CUT_X + 0.01, -BOX_HALF_Y, BOX_HALF_Y, 0.0, 14.6)  # restores box envelope
housing = cyl_x(R_OUT, FRONT_X, CUT_X + 0.01)
boss    = cylinder(radius=2.6, height=14.6 - 1.8, sections=48)
boss.apply_translation([HAT_BOSS[0], HAT_BOSS[1], (14.6 + 1.8) / 2])

plinth  = bx(FRONT_X, CUT_X + 0.01, -11.0, 11.0, 0.0, 4.0)
solid = U(U(U(U(head, bridge), housing), boss), plinth)

# flatten the housing so it prints floor-down (chord at z=0, ~11 mm wide)
solid = D(solid, bx(-40, CUT_X + 1, -40, 40, -10, 0.0))

cuts = [
    cyl_x(R_WIN, FRONT_X - 1, FRONT_X + BEZEL_T + 0.01),                      # window
    cyl_x(R_PCB, FRONT_X + BEZEL_T, BACKWALL_X),                              # pocket + cavity
    bx(FRONT_X + BEZEL_T, BACKWALL_X, -TAB_W / 2, TAB_W / 2, ZC - (R_PCB + TAB_R), ZC),  # tab slot, bottom
    bx(BACKWALL_X - 0.01, CUT_X + 0.5, -14.0, 14.0, 2.0, 14.6),              # passage into box
    cyl_x(1.0, HAT_BOSS[0] - 20, HAT_BOSS[0] + 20, y=0, z=0, sections=24),   # placeholder (replaced below)
]
cuts.pop()  # remove placeholder
pilot = cylinder(radius=1.0, height=9.0, sections=32)
pilot.apply_translation([HAT_BOSS[0], HAT_BOSS[1], 14.6 - 4.5 + 0.01])
cuts.append(pilot)

for c in cuts:
    solid = D(solid, c)

# crush ribs for friction fit (two 0.5 mm ribs at ±y inside the pocket)
for sgn in (+1, -1):
    rib = bx(FRONT_X + BEZEL_T, FRONT_X + BEZEL_T + POCKET_D + 2.0,
             sgn * (R_PCB - 0.5) - 0.6, sgn * (R_PCB - 0.5) + 0.6, ZC - 0.6, ZC + 0.6)
    rib = bx(FRONT_X + BEZEL_T, FRONT_X + BEZEL_T + POCKET_D + 2.0,
             min(sgn * R_PCB, sgn * (R_PCB - 0.5)), max(sgn * R_PCB, sgn * (R_PCB - 0.5)),
             ZC - 1.0, ZC + 1.0)
    solid = U(solid, rib)

solid.merge_vertices(); solid.update_faces(solid.nondegenerate_faces())
print("HeadRound watertight:", solid.is_watertight, "bounds:", np.round(solid.bounds, 2), "vol mm3:", round(solid.volume))
solid.export(f"{OUT}/HeadRound.stl")
solid.export(f"{OUT}/HeadRound.3mf")

# ---- hat ---------------------------------------------------------------------
hat = load("Hat")                       # hat frame: x_hat = x_head - 8.1
HAT_OFF = -8.1
hat = D(hat, bx(-50, CUT_X + 0.3 + HAT_OFF, -40, 40, -5, 10))      # trim brim in front of housing
hole = cylinder(radius=1.2, height=12, sections=32)
hole.apply_translation([HAT_BOSS[0] + HAT_OFF, HAT_BOSS[1], 2.5])
hat = D(hat, hole)
print("HatRound watertight:", hat.is_watertight, "bounds:", np.round(hat.bounds, 2))
hat.export(f"{OUT}/HatRound.stl")
hat.export(f"{OUT}/HatRound.3mf")
