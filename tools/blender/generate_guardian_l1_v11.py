#!/usr/bin/env python3
"""Guardian L1 v11 — unified final-polish pass.

Keeps the complete v10 body/armor/equipment rebuild, but replaces the visibly
segmented/bald-looking hairstyle with ONE continuous fitted hair shell plus ONE
continuous swept-front quiff. The goal is a neat short heroic haircut with no
scalp gaps from front, three-quarter, side, or top-facing camera angles.
"""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import bpy

V10_PATH = Path(__file__).with_name("generate_guardian_l1_v10.py")
spec = importlib.util.spec_from_file_location("guardian_v10", V10_PATH)
v10 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(v10)


def _continuous_short_hair(mat_hair):
    """Single clean short-hair shell with a natural closed hairline."""
    cx, cy, cz = 0.0, 0.014, 1.758
    rx, ry, rz = 0.146, 0.125, 0.158
    rings, sides = 20, 96
    verts, faces = [], []

    for r in range(rings + 1):
        t = r / rings
        for i in range(sides):
            phi = 2.0 * math.pi * i / sides
            front = max(0.0, -math.sin(phi))
            back = max(0.0, math.sin(phi))
            side = abs(math.cos(phi))

            # Front hairline ends higher; sides/back descend lower around the head.
            theta_max = math.radians(105.0 - 12.0 * front + 3.0 * side + 7.0 * back)
            theta = math.radians(1.0) + (theta_max - math.radians(1.0)) * t
            st, ct = math.sin(theta), math.cos(theta)

            x = cx + rx * st * math.cos(phi)
            y = cy + ry * st * math.sin(phi)
            z = cz + rz * ct

            # Gentle side-swept crown shape, encoded in the single mesh itself.
            crown_weight = max(0.0, 1.0 - t / 0.72)
            if front > 0.15:
                z += 0.014 * crown_weight * (0.72 + 0.28 * (-math.cos(phi)))
                x -= 0.008 * crown_weight

            # Subtle sculpted hair flow so the cap reads as hair, not a helmet.
            flow = math.sin(phi * 5.0 + t * 4.0) * 0.0025 * (1.0 - 0.35 * t)
            z += flow
            verts.append((x, y, z))

    for r in range(rings):
        for i in range(sides):
            a = r * sides + i
            b = r * sides + (i + 1) % sides
            c = (r + 1) * sides + (i + 1) % sides
            d = (r + 1) * sides + i
            faces.append((a, b, c, d))

    me = bpy.data.meshes.new("GuardianHairUnifiedMesh")
    me.from_pydata(verts, [], faces)
    me.update()
    hair = bpy.data.objects.new("GuardianHairUnified", me)
    bpy.context.collection.objects.link(hair)
    hair.data.materials.append(mat_hair)
    v10.v8.smooth(hair, 2)
    solid = hair.modifiers.new("HairThickness", "SOLIDIFY")
    solid.thickness = 0.010

    # ONE continuous front quiff strip, not separate blobs or tiles.
    sections = [
        (-0.118, -0.098, 1.790, 0.020),
        (-0.078, -0.112, 1.830, 0.026),
        (-0.030, -0.118, 1.854, 0.028),
        ( 0.020, -0.116, 1.850, 0.027),
        ( 0.068, -0.106, 1.830, 0.024),
        ( 0.110, -0.088, 1.800, 0.018),
    ]
    qverts = []
    for x, y, z, half in sections:
        # rear edge embedded into cap, front edge slightly outward/upward
        qverts.append((x - half, y + 0.010, z - 0.010))
        qverts.append((x + half, y + 0.010, z - 0.010))
        qverts.append((x + half * 0.88, y - 0.018, z + 0.012))
        qverts.append((x - half * 0.88, y - 0.018, z + 0.012))
    qfaces = []
    for s in range(len(sections) - 1):
        a = s * 4
        b = (s + 1) * 4
        qfaces += [
            (a, a+1, b+1, b),
            (a+3, b+3, b+2, a+2),
            (a, b, b+3, a+3),
            (a+1, a+2, b+2, b+1),
            (a+3, a+2, a+1, a),
        ]
    last = (len(sections) - 1) * 4
    qfaces.append((last, last+1, last+2, last+3))
    qme = bpy.data.meshes.new("GuardianHairQuiffMesh")
    qme.from_pydata(qverts, [], qfaces)
    qme.update()
    quiff = bpy.data.objects.new("GuardianHairQuiff", qme)
    bpy.context.collection.objects.link(quiff)
    quiff.data.materials.append(mat_hair)
    v10.v8.smooth(quiff, 2)
    qsolid = quiff.modifiers.new("QuiffThickness", "SOLIDIFY")
    qsolid.thickness = 0.006

    # Clean connected temple pieces only; no crown patches.
    for side, lab in ((-1, "L"), (1, "R")):
        v10.v8.uv(
            f"GuardianSideburn.{lab}",
            (side * 0.120, -0.050, 1.737),
            (0.020, 0.020, 0.050),
            mat_hair,
            32,
            16,
            rot=(0.0, math.radians(side * 7.0), math.radians(side * 4.0)),
        )

    return hair


def main():
    # Preserve the whole v10 full-character overhaul, replacing only the bad
    # segmented hair implementation with the unified final hairstyle.
    v10._hair_cap = _continuous_short_hair
    parsed = v10.v8.parse_args()
    v10.main()

    out = Path(parsed.output).resolve()
    meta = out / "metadata.json"
    if meta.exists():
        data = json.loads(meta.read_text(encoding="utf-8"))
        data["pass"] = "v11-unified-final-polish"
        data["goal"] = "complete Guardian L1 with clean continuous heroic short hair and full v10 visual polish"
        data["hair"] = "single fitted shell + single swept quiff; no crown patches; no bald center"
        data["kept_from_v10"] = [
            "human proportions",
            "curved breastplate",
            "fitted sleeves and trousers",
            "layered shoulders and bracers",
            "greaves and proper boots",
            "proportional shield",
            "rescaled sword",
            "compact scarf and tabard",
        ]
        meta.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print("GUARDIAN_L1_V11_COMPLETE")


if __name__ == "__main__":
    main()
