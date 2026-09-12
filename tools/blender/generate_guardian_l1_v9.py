#!/usr/bin/env python3
"""Guardian L1 v9 — clean short-hair refinement over the v8 majestic human base.

This pass deliberately keeps the improved v8 human proportions and armor while
replacing the unfinished multi-blob hairstyle with a continuous, groomed short
hair cap plus controlled swept locks. The hairline stays covered across the
crown so there is no bald-looking center gap.
"""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import bpy


V8_PATH = Path(__file__).with_name("generate_guardian_l1_v8.py")
spec = importlib.util.spec_from_file_location("guardian_v8", V8_PATH)
v8 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(v8)


def _hair_cap(mat_hair):
    """Build one continuous short-hair shell with a natural front hairline."""
    cx, cy, cz = 0.0, 0.018, 1.762
    rx, ry, rz = 0.142, 0.118, 0.142
    rings = 12
    sides = 64
    verts = []
    faces = []

    # Pole vertex duplicated per side through ring 0 is avoided by starting with
    # a very small top ring; subdivision smooths it into a single crown mass.
    for r in range(rings + 1):
        t = r / rings
        for i in range(sides):
            phi = 2.0 * math.pi * i / sides
            # Front is -Y. Keep the forehead hairline higher, allow sides/back
            # to descend naturally around the temples and occipital area.
            theta_max = math.radians(97.0 + 17.0 * math.sin(phi))
            theta = max(math.radians(2.0), theta_max * t)
            st = math.sin(theta)
            x = cx + rx * st * math.cos(phi)
            y = cy + ry * st * math.sin(phi)
            z = cz + rz * math.cos(theta)
            # Slight crown lift toward the swept-left front section.
            if y < cy and x < 0.035:
                z += 0.010 * (1.0 - t)
            verts.append((x, y, z))

    for r in range(rings):
        for i in range(sides):
            a = r * sides + i
            b = r * sides + (i + 1) % sides
            c = (r + 1) * sides + (i + 1) % sides
            d = (r + 1) * sides + i
            faces.append((a, b, c, d))

    me = bpy.data.meshes.new("GuardianHairCapMesh")
    me.from_pydata(verts, [], faces)
    me.update()
    cap = bpy.data.objects.new("GuardianHairCap", me)
    bpy.context.collection.objects.link(cap)
    cap.data.materials.append(mat_hair)
    v8.smooth(cap, 2)
    solid = cap.modifiers.new("HairThickness", "SOLIDIFY")
    solid.thickness = 0.009
    return cap


def hair_v9(mat_hair):
    """Neat short heroic hair with full scalp coverage and swept front."""
    _hair_cap(mat_hair)

    # Controlled swept top locks. These overlap the cap instead of replacing it,
    # so no visible scalp gaps appear even from front/three-quarter/side views.
    locks = [
        (-0.082, -0.075, 1.842, 0.070, 0.034, 0.050, -18, -10),
        (-0.026, -0.090, 1.858, 0.076, 0.032, 0.052, -10, -6),
        ( 0.035, -0.086, 1.850, 0.070, 0.032, 0.050,  -2,  3),
        ( 0.088, -0.060, 1.830, 0.060, 0.034, 0.047,   8, 12),
        (-0.105, -0.018, 1.815, 0.047, 0.039, 0.060, -20, -18),
        ( 0.108, -0.010, 1.805, 0.045, 0.040, 0.058,  18, 18),
        (-0.070,  0.070, 1.814, 0.060, 0.050, 0.058, -10, -12),
        ( 0.020,  0.083, 1.820, 0.066, 0.052, 0.058,   2,  4),
        ( 0.082,  0.060, 1.806, 0.052, 0.048, 0.056,  12, 14),
    ]
    for i, (x, y, z, sx, sy, sz, rx_deg, rz_deg) in enumerate(locks):
        v8.uv(
            f"HairSweep.{i}",
            (x, y, z),
            (sx, sy, sz),
            mat_hair,
            40,
            20,
            rot=(math.radians(rx_deg), 0.0, math.radians(rz_deg)),
        )

    # Clean temple/sideburn pieces that visually connect the cap to the face.
    for side, lab in ((-1, "L"), (1, "R")):
        v8.uv(
            f"HairTemple.{lab}",
            (side * 0.117, -0.055, 1.748),
            (0.026, 0.030, 0.060),
            mat_hair,
            32,
            16,
            rot=(0.0, math.radians(side * 8.0), math.radians(side * 7.0)),
        )


def main():
    # Reuse the tested v8 anatomy/armor/export pipeline and replace only the
    # hairstyle implementation. This avoids regressing the body proportions.
    v8.hair = hair_v9
    parsed = v8.parse_args()
    v8.main()

    out = Path(parsed.output).resolve()
    meta = out / "metadata.json"
    if meta.exists():
        data = json.loads(meta.read_text(encoding="utf-8"))
        data["pass"] = "v9-clean-short-hair"
        data["goal"] = "human-proportion majestic Guardian with neat full-coverage short hair"
        data["hair"] = "continuous cap + swept locks; no center scalp gap"
        meta.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print("GUARDIAN_L1_V9_COMPLETE")


if __name__ == "__main__":
    main()
