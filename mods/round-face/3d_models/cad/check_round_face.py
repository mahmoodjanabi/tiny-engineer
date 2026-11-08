"""Fit checks for the round-face mod. Run after build_round_face.py.

Usage: python3 check_round_face.py <stock sg90 3mf dir> <dir with HeadRound/HatRound .stl>

Checks, all in head coordinates:
  1. module seated: no overlap with HeadRound or BezelRound
  2. module insertion from the front: no overlap at any point along the path
  3. bezel seated in HeadRound: no overlap (lip is a 0.1 mm radial slip fit)
  4. hat seated on HeadRound: no overlap
  5. cable: plug + 8-wire bundle leaving through the top-back slot: no overlap
  6. pitch-servo load vs stock
The module mock follows the Waveshare drawing; back-side parts are estimates.
"""
import sys, importlib.util, numpy as np, trimesh
from trimesh.creation import box, cylinder
from trimesh.transformations import rotation_matrix as rot

SRC, OUT = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("b", __file__.replace("check_round_face", "build_round_face"))
sys.argv = [sys.argv[0], SRC, OUT]
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)

I = lambda a, c: trimesh.boolean.intersection([a, c], engine="manifold")
def overlap(a, c):
    i = I(a, c)
    return 0.0 if i is None or len(i.faces) == 0 else abs(i.volume)

head = trimesh.load(f"{OUT}/HeadRound.stl")
bezel = b.build_bezel(head_frame=True)
hat = trimesh.load(f"{OUT}/HatRound.stl"); hat.apply_translation([-b.HAT_OFF, 0, 14.6])

pcb_front = b.X_H
pcb_back = b.X_H + b.STACK
mod = b.U(b.cyl_x(b.R_MOD, pcb_front, pcb_back),
          b.bx(pcb_front, pcb_back, -14.28 / 2, 14.28 / 2, b.ZC - b.R_MOD - 3.59, b.ZC - b.R_MOD + 1),
          b.bx(pcb_back - 0.1, pcb_back + 4.8, -10.25, 10.25, b.ZC + 3.9, b.ZC + 11.0),   # PH2.0 socket
          b.bx(pcb_back - 0.1, pcb_back + 1.3, -3.5, 3.5, b.ZC - 6.0, b.ZC - 1.0),        # driver IC
          b.bx(pcb_back - 0.1, pcb_back + 1.0, -14.28 / 2, 14.28 / 2,
               b.ZC - b.R_MOD - 3.59, b.ZC - b.R_MOD + 2))                                  # flex fold
plug = b.bx(pcb_back + 0.3, pcb_back + 4.5, -8.6, 8.6, b.ZC + 11.0, b.ZC + 15.0)
wires = b.U(b.bx(pcb_back + 0.6, pcb_back + 3.6, -8.4, 8.4, b.ZC + 15.0, b.ZC + 18.0),     # up off the plug
            b.bx(pcb_back + 0.6, b.CUT_X + 6, -8.4, 8.4, b.ZC + 15.0, b.ZC + 17.5))        # back over the hat

res = {}
res["1 module seated vs head"] = overlap(mod, head)
res["1 module seated vs bezel"] = overlap(mod, bezel)
worst = 0.0
for dx in np.arange(-25.0, 0.01, 0.5):
    t = mod.copy(); t.apply_translation([dx, 0, 0])
    worst = max(worst, overlap(t, head))
res["2 insertion path, worst step"] = worst
res["3 bezel vs head"] = overlap(bezel, head)
res["4 hat vs head"] = overlap(hat, head)
res["5 plug vs head"] = overlap(plug, head)
res["5 wire bundle vs head"] = overlap(wires, head)
res["5 wire bundle vs hat"] = overlap(wires, hat)
for k, v in res.items():
    print(f"{k:32s} {v:8.2f} mm3  {'OK' if v < 0.5 else 'CLASH'}")

# pitch servo load (static, about the pitch axis x=-2, z=8.3), PLA 1.24 g/cm3, 20 % infill ~ 0.55 effective
PIVOT_X = -2.0
def moment(mesh, dens=1.24e-3 * 0.55):
    return mesh.volume * dens, mesh.volume * dens * abs(mesh.center_mass[0] - PIVOT_X)
stock_h, stock_hat = b.load("Head"), b.load("Hat"); stock_hat.apply_translation([-b.HAT_OFF, 0, 14.6])
m0 = moment(stock_h); m1 = moment(stock_hat)
st = (m0[0] + m1[0] + 2.0, m0[1] + m1[1] + 2.0 * abs(-24.0 - PIVOT_X))                      # + 2 g OLED
n0 = moment(head); n1 = moment(hat); n2 = moment(bezel)
nw = (n0[0] + n1[0] + n2[0] + 15.0,
      n0[1] + n1[1] + n2[1] + 15.0 * abs(b.X_H + 2.0 - PIVOT_X))                             # + 15 g module
SG90 = 18000.0
print(f"head mass   stock {st[0]:5.1f} g   round {nw[0]:5.1f} g")
print(f"pitch load  stock {st[1]:6.0f} g.mm  round {nw[1]:6.0f} g.mm  = {100 * nw[1] / SG90:.1f} % of SG90 stall (1.8 kg.cm)")
