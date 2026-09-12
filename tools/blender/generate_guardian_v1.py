#!/usr/bin/env python3
"""Dedicated Guardian generator for Emberfall Kingdoms.

This file intentionally generates ONE troop family only: Guardian, levels 1..15.
Each level keeps the same character identity while adding structural progression
(armor, shield, sword, helmet, cape, runes) rather than simple recolors.

Outputs per level: GLB, transparent PNG, metadata.json and optional .blend.
Designed for headless Blender in GitHub Actions.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
V3_PATH = Path(__file__).resolve().with_name("generate_army_v3.py")
SPECS_PATH = ROOT / "art" / "blender" / "unit_specs.json"

_modspec = importlib.util.spec_from_file_location("emberfall_army_v3_guardian", V3_PATH)
v3 = importlib.util.module_from_spec(_modspec)
_modspec.loader.exec_module(v3)

MAX_LEVEL = 15


def cli():
    raw = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--levels", default="1-15")
    p.add_argument("--output", default=str(ROOT / "generated" / "guardian-v1"))
    p.add_argument("--preview-size", type=int, default=512)
    p.add_argument("--save-blend", action="store_true")
    return p.parse_args(raw)


def parse_levels(text):
    out = set()
    for chunk in text.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            a, b = map(int, chunk.split("-", 1))
            out.update(range(min(a, b), max(a, b) + 1))
        else:
            out.add(int(chunk))
    levels = sorted(x for x in out if 1 <= x <= MAX_LEVEL)
    if not levels:
        raise SystemExit("Guardian supports levels 1-15")
    return levels


def guardian_palette(spec, level):
    p = v3.palette(spec, level)
    r = (level - 1) / 14
    p["silver"] = v3.material("GuardianSilver", (.46 + .12*r, .50 + .12*r, .53 + .12*r), .90, .18)
    p["bluecloth"] = v3.material("GuardianCloth", (.055, .16 + .04*r, .27 + .05*r), 0, .62)
    p["leather2"] = v3.material("GuardianLeather", (.25, .105, .035), 0, .68)
    p["darkcloth"] = v3.material("GuardianDarkCloth", (.025, .065, .11), 0, .70)
    return p


def limb(root, p, side, level):
    label = "L" if side < 0 else "R"
    heavy = 1.0 + .025 * max(0, level - 5)
    hip = (side*.175, 0, .87)
    knee = (side*.225, -.015, .52)
    ankle = (side*.23, -.025, .20)
    v3.rod(f"Thigh.{label}", hip, knee, .115*heavy, p["darkcloth"], root, 14)
    v3.rod(f"Shin.{label}", knee, ankle, .105*heavy, p["primary_dark"], root, 14)
    v3.cube(f"Boot.{label}", (side*.23, -.085, .105), (.155, .205, .11), p["leather2"], root, bevel=.05)
    if level >= 7:
        v3.cube(f"Greave.{label}", (side*.23, -.12, .36), (.125, .075, .20), p["silver"], root, bevel=.04)
        v3.cube(f"KneePlate.{label}", (side*.225, -.17, .54), (.13, .055, .095), p["steel"], root, bevel=.04)
    if level >= 13:
        v3.ico(f"KneeRune.{label}", (side*.225, -.23, .54), (.038, .018, .044), p["glow"], root)


def arm(root, p, side, level):
    label = "L" if side < 0 else "R"
    shoulder = (side*.45, 0, 1.49)
    if side < 0:
        elbow = (-.53, -.08, 1.25)
        hand = (-.50, -.28, 1.10)
    else:
        elbow = (.55, -.07, 1.22)
        hand = (.56, -.13, 1.00)
    v3.rod(f"UpperArm.{label}", shoulder, elbow, .105, p["bluecloth"], root, 14)
    v3.rod(f"Forearm.{label}", elbow, hand, .082, p["skin"], root, 14)
    v3.sphere(f"Hand.{label}", hand, (.085, .073, .086), p["skin"], root, 16, 9)
    if level >= 6:
        mid = ((elbow[0]+hand[0])*.5, (elbow[1]+hand[1])*.5, (elbow[2]+hand[2])*.5)
        v3.rod(f"Bracer.{label}", elbow, mid, .105, p["darksteel"], root, 14)
    if level >= 11:
        v3.torus(f"WristRing.{label}", hand, .095, .016, p["accent"], root, rot=(math.pi/2, 0, 0))


def face_and_helmet(root, p, spec, level):
    # Face remains readable through the open helmet even at high levels.
    v3.add_face(root, p, spec, helmet=level >= 3, masked=False)
    z = 1.93
    if level == 1:
        v3.torus("RecruitHeadband", (0, -.005, z+.10), .207, .018, p["leather2"], root, rot=(math.pi/2,0,0))
        return
    if level == 2:
        v3.torus("RankHeadband", (0, -.005, z+.10), .208, .020, p["accent"], root, rot=(math.pi/2,0,0))
        v3.cube("HeadbandBadge", (0, -.205, z+.11), (.045,.014,.055), p["accent"], root, bevel=.012)
        return
    # Open-face helmet: rear shell + brow + cheek guards, no face-covering sphere.
    v3.sphere("HelmetRear", (0, .075, z+.11), (.225,.16,.19), p["darksteel"], root, 20, 12)
    v3.cube("HelmetBrow", (0, -.175, z+.14), (.19,.035,.045), p["silver"], root, bevel=.018)
    if level >= 5:
        for side,label in ((-1,"L"),(1,"R")):
            v3.cube(f"CheekGuard.{label}", (side*.168,-.14,z-.015), (.045,.035,.13), p["steel"], root, rot=(0,0,side*.12), bevel=.018)
    if level >= 8:
        v3.cube("HelmetCrownBand", (0,.01,z+.235), (.16,.13,.035), p["accent"], root, bevel=.02)
    if level >= 10:
        v3.cone("HelmetCrest", (0,.05,z+.43), .065,.012,.38, p["accent"], root, vertices=9)
    if level >= 12:
        for side,label in ((-1,"L"),(1,"R")):
            v3.cone(f"HelmetWing.{label}", (side*.23,.03,z+.20), .045,.005,.25, p["silver"], root, rot=(0,side*.60,0), vertices=7)
    if level >= 15:
        v3.ico("HelmetMasterRune", (0,-.205,z+.16), (.055,.020,.070), p["glow"], root)


def torso(root, p, level):
    # Broad guardian silhouette; the cloth base remains visible between armor plates.
    v3.cone("Tunic", (0,0,1.31), .34,.405,.72, p["bluecloth"], root, vertices=12)
    v3.cube("TunicFront", (0,-.252,1.29), (.30,.028,.30), p["primary_dark"], root, bevel=.04)
    v3.cube("Belt", (0,-.015,.96), (.36,.22,.055), p["leather2"], root, bevel=.025)
    v3.cube("BeltBuckle", (0,-.242,.96), (.065,.018,.065), p["accent"], root, bevel=.012)
    v3.cone("WaistSkirt", (0,.01,.84), .34,.28,.30, p["darkcloth"], root, vertices=12)
    # Split tabard gives a strong central vertical read.
    v3.cube("Tabard", (0,-.27,.82), (.135,.022,.35), p["primary"], root, bevel=.025)

    if level >= 2:
        v3.cube("LeatherChest", (0,-.275,1.34), (.28,.025,.24), p["leather2"], root, bevel=.045)
        v3.beam("CrossStrap", (-.25,-.305,1.52), (.21,-.305,1.10), .032,.010, p["accent"], root, .008)
    if level >= 3:
        v3.ico("RankBadge", (0,-.315,1.34), (.055,.020,.065), p["accent"], root)
    if level >= 4:
        v3.cone("Cuirass", (0,-.04,1.32), .325,.37,.54, p["steel"], root, vertices=12)
        v3.cube("Breastplate", (0,-.285,1.34), (.295,.040,.245), p["silver"], root, bevel=.055)
        v3.cube("SternumPlate", (0,-.335,1.35), (.075,.018,.215), p["darksteel"], root, bevel=.025)
    if level >= 5:
        for side,label in ((-1,"L"),(1,"R")):
            v3.sphere(f"Pauldron.{label}", (side*.455,-.015,1.52), (.205,.18,.145), p["steel"], root, 18, 10)
            v3.cube(f"PauldronPlate.{label}", (side*.455,-.16,1.52), (.135,.025,.065), p["silver"], root, bevel=.02)
    if level >= 8:
        v3.cube("UpperChestBand", (0,-.338,1.48), (.245,.014,.035), p["accent"], root, bevel=.008)
        v3.cube("LowerChestBand", (0,-.338,1.18), (.235,.014,.030), p["accent"], root, bevel=.008)
    if level >= 9:
        v3.ico("GuardianChestRune", (0,-.365,1.35), (.078,.025,.095), p["glow"], root)
    if level >= 10:
        # Layered veteran plates and gold-edged shoulders.
        v3.cube("VeteranChestLayer", (0,-.345,1.33), (.235,.018,.19), p["darksteel"], root, bevel=.035)
        for side,label in ((-1,"L"),(1,"R")):
            v3.cube(f"VeteranShoulderTrim.{label}", (side*.455,-.190,1.53), (.12,.016,.045), p["gold"], root, bevel=.008)
    if level >= 11:
        # Four articulated waist plates (faulds).
        for i,x in enumerate((-.24,-.08,.08,.24)):
            v3.cube(f"Fauld.{i}", (x,-.115,.84), (.075,.12,.16), p["steel"], root, rot=(0,0,x*.22), bevel=.03)
    if level >= 12:
        for side,label in ((-1,"L"),(1,"R")):
            v3.cone(f"ShoulderSpike.{label}", (side*.56,-.005,1.62), .052,.004,.23, p["accent"], root, rot=(0,side*.60,0), vertices=8)
    if level >= 13:
        v3.cube("ChampionChestFrameTop", (0,-.375,1.51), (.255,.012,.020), p["gold"], root, bevel=.006)
        v3.cube("ChampionChestFrameBottom", (0,-.375,1.16), (.245,.012,.020), p["gold"], root, bevel=.006)
        for side in (-1,1):
            v3.beam(f"ChampionChestFrame.{side}", (side*.25,-.375,1.49), (side*.22,-.375,1.18), .015,.008, p["gold"], root, .004)
    if level >= 15:
        v3.torus("MasteryGroundAura", (0,0,.055), .66,.025, p["glow"], root)


def sword(root, p, level):
    # Sword is physically continuous from the right hand; no floating blade pieces.
    hand = Vector((.56,-.13,1.00))
    grip_end = Vector((.62,-.14,1.20))
    guard_center = grip_end
    blade_start = guard_center + Vector((.02,0,.03))
    blade_end = Vector((.83,-.16,1.86 + .012*level))
    v3.rod("SwordGrip", hand, grip_end, .045, p["leather2"], root, 12)
    v3.beam("SwordGuard", tuple(guard_center+Vector((-.16,0,0))), tuple(guard_center+Vector((.16,0,0))), .032,.032, p["accent"], root, .012)
    v3.beam("SwordBlade", blade_start, blade_end, .075 + (.015 if level>=8 else 0) + (.012 if level>=14 else 0), .026, p["silver"], root, .018)
    # Pommel is connected below the hand.
    v3.ico("SwordPommel", tuple(hand+Vector((-.02,0,-.07))), (.055,.040,.065), p["accent"], root)
    if level >= 6:
        v3.cube("SwordRainGuard", (.64,-.165,1.23), (.055,.022,.045), p["darksteel"], root, bevel=.012)
    if level >= 8:
        v3.ico("SwordRune", (.73,-.185,1.53), (.042,.018,.055), p["glow"], root)
    if level >= 14:
        v3.rod("SwordGlowCore", (.71,-.188,1.45), (.82,-.188,1.83), .012, p["glow"], root, 8)
    if level >= 15:
        v3.torus("SwordHalo", (.80,-.16,1.75), .12,.010, p["glow"], root, rot=(math.pi/2,0,0))


def shield(root, p, level):
    # Large kite/tower shield attached to the left arm and centered on the left hand.
    x, y, z = -.52, -.35, 1.08
    # Main shield body: layered vertical plate reads clearly at RTS scale.
    v3.cube("ShieldBody", (x,y,z), (.33,.055,.48), p["darksteel"], root, bevel=.10)
    v3.cube("ShieldFace", (x,y-.060,z), (.285,.025,.42), p["steel"], root, bevel=.085)
    v3.cube("ShieldSpine", (x,y-.092,z), (.040,.018,.38), p["silver"], root, bevel=.015)
    v3.ico("ShieldBoss", (x,y-.115,z), (.09,.028,.09), p["accent"], root)
    # Arm linkage makes attachment visually obvious from the render angle.
    v3.rod("ShieldHandle", (-.50,-.28,1.10), (x,y-.01,z), .035, p["leather2"], root, 10)
    if level >= 3:
        for zz in (.78,1.38):
            v3.cube(f"ShieldBar.{zz}", (x,y-.100,zz), (.25,.015,.025), p["accent"], root, bevel=.008)
    if level >= 5:
        # Rim made from four connected plates rather than a floating ring.
        v3.cube("ShieldRimTop", (x,y-.092,1.48), (.29,.018,.025), p["silver"], root, bevel=.008)
        v3.cube("ShieldRimBottom", (x,y-.092,.68), (.29,.018,.025), p["silver"], root, bevel=.008)
        v3.cube("ShieldRimL", (x-.285,y-.092,z), (.022,.018,.39), p["silver"], root, bevel=.008)
        v3.cube("ShieldRimR", (x+.285,y-.092,z), (.022,.018,.39), p["silver"], root, bevel=.008)
    if level >= 7:
        for sx in (-.20,.20):
            for sz in (.82,1.34):
                v3.ico(f"ShieldStud.{sx}.{sz}", (x+sx,y-.125,sz), (.028,.014,.028), p["accent"], root, sub=1)
    if level >= 9:
        v3.ico("ShieldEmblem", (x,y-.145,z), (.12,.025,.15), p["glow"], root)
    if level >= 12:
        for side in (-1,1):
            v3.cone(f"ShieldHorn.{side}", (x+side*.29,y-.08,1.46), .035,.002,.18, p["accent"], root, rot=(0,side*.55,0), vertices=7)
    if level >= 14:
        v3.torus("ShieldRuneRing", (x,y-.158,z), .19,.012, p["glow"], root, rot=(math.pi/2,0,0))
    if level >= 15:
        v3.ico("ShieldMasterCore", (x,y-.175,z), (.075,.020,.095), p["glow"], root)


def cape(root, p, level):
    if level < 10:
        return
    v3.cube("Cape", (0,.24,1.18), (.38,.035,.50), p["primary_dark"], root, rot=(-.08,0,0), bevel=.045)
    v3.cube("CapeTailL", (-.15,.25,.77), (.14,.030,.30), p["primary"], root, rot=(-.12,0,-.05), bevel=.03)
    v3.cube("CapeTailR", (.15,.25,.77), (.14,.030,.30), p["primary"], root, rot=(-.12,0,.05), bevel=.03)
    if level >= 12:
        v3.cube("CapeGoldTrim", (0,.207,.66), (.35,.012,.025), p["gold"], root, bevel=.008)
    if level >= 15:
        v3.ico("CapeRune", (0,.198,1.10), (.065,.020,.080), p["glow"], root)


LEVEL_CHANGES = {
    1: "Recruit form: cloth tunic, leather belt/boots, attached tower shield and short guardian sword",
    2: "Leather chest reinforcement, cross strap, rank headband",
    3: "Open helmet, rank badge, shield reinforcement bars",
    4: "Steel cuirass and layered breastplate",
    5: "Heavy pauldrons, cheek guards and full shield rim",
    6: "Metal forearm bracers and upgraded sword guard",
    7: "Greaves, knee plates and shield studs",
    8: "Chest trim, helmet crown band and wider veteran sword",
    9: "Glowing chest rune and shield emblem",
    10: "Veteran armor layering, gold shoulder trim, helmet crest and cape",
    11: "Articulated fauld plates and wrist rank rings",
    12: "Shoulder spikes, helmet wings, cape trim and shield horns",
    13: "Champion gold chest frame and glowing knee runes",
    14: "Enchanted sword core and shield rune ring",
    15: "Master helmet rune, mastery aura, shield master core and sword halo",
}


def build_guardian(spec, level, p):
    root = v3.root_empty("GuardianRoot")
    torso(root, p, level)
    for side in (-1,1):
        limb(root,p,side,level)
        arm(root,p,side,level)
    face_and_helmet(root,p,spec,level)
    cape(root,p,level)
    shield(root,p,level)
    sword(root,p,level)
    # Slight controlled growth only; identity/proportions remain stable.
    s = float(spec.get("scale",1.0)) * (1.0 + .012*(level-1)/14)
    root.scale=(s,s,s)
    return root


def generate(spec, level, out, size, save_blend):
    v3.clear_scene()
    p = guardian_palette(spec, level)
    root = build_guardian(spec,level,p)
    root.name=f"troop_guardian_L{level:02d}"
    root["unit_id"]="guardian";root["level"]=level;root["name"]=spec["name"]
    v3.stage(size)
    folder=out/"guardian"/f"level-{level:02d}"
    folder.mkdir(parents=True,exist_ok=True)
    glb=folder/f"guardian-level-{level:02d}.glb"
    png=folder/f"guardian-level-{level:02d}.png"
    v3.export_glb(glb)
    bpy.context.scene.render.filepath=str(png)
    bpy.ops.render.render(write_still=True)
    blend=None
    if save_blend:
        blend=folder/f"guardian-level-{level:02d}.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    meta={
        "generator":"guardian-v1",
        "id":"guardian",
        "name":spec["name"],
        "level":level,
        "max_level":15,
        "role":"frontline defensive melee",
        "progression_change":LEVEL_CHANGES[level],
        "glb":glb.name,
        "preview":png.name,
        "blend":blend.name if blend else None,
    }
    (folder/"metadata.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    return meta


def main():
    a=cli()
    specs=json.loads(SPECS_PATH.read_text(encoding="utf-8"))["troops"]
    spec=dict(specs["guardian"])
    levels=parse_levels(a.levels)
    out=Path(a.output).resolve()
    assets=[]
    for level in levels:
        print(f"[Guardian v1] Level {level}/15 - {LEVEL_CHANGES[level]}",flush=True)
        assets.append(generate(spec,level,out,a.preview_size,a.save_blend))
    manifest={"generator":"tools/blender/generate_guardian_v1.py","unit":"guardian","assets":assets}
    out.mkdir(parents=True,exist_ok=True)
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(f"Generated {len(assets)} detailed Guardian levels -> {out}",flush=True)


if __name__ == "__main__":
    main()
