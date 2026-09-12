#!/usr/bin/env python3
"""Generate original Emberfall troop/hero level variants with Blender.

Run through Blender, for example:
  blender -b --python tools/blender/generate_unit.py -- --kind troop --unit guardian --levels 1-15 --output generated/blender --save-blend

The generator deliberately creates original stylized fantasy designs from the local
unit_specs.json file. It does not download or copy third-party character models.
"""
from __future__ import annotations

import argparse
import colorsys
import json
import math
import os
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
SPECS_PATH = ROOT / "art" / "blender" / "unit_specs.json"
UNIT_TAG = "emberfall_unit_asset"


def cli_args():
    raw = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--kind", choices=["troop", "hero"], default="troop")
    p.add_argument("--unit", default="guardian")
    p.add_argument("--levels", default="1")
    p.add_argument("--output", default=str(ROOT / "generated" / "blender"))
    p.add_argument("--all-troops", action="store_true")
    p.add_argument("--all-heroes", action="store_true")
    p.add_argument("--all", action="store_true")
    p.add_argument("--save-blend", action="store_true")
    p.add_argument("--preview-size", type=int, default=512)
    return p.parse_args(raw)


def parse_levels(text: str, maximum: int):
    values = set()
    for token in text.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            a, b = token.split("-", 1)
            a, b = int(a), int(b)
            values.update(range(min(a, b), max(a, b) + 1))
        else:
            values.add(int(token))
    levels = sorted(v for v in values if 1 <= v <= maximum)
    if not levels:
        raise SystemExit(f"No valid levels in {text!r}; allowed 1-{maximum}.")
    return levels


def hex_rgb(value: str):
    value = value.lstrip("#")
    return tuple(int(value[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def adjust(rgb, light=0.0, saturation=0.0):
    h, s, v = colorsys.rgb_to_hsv(*rgb)
    s = max(0.0, min(1.0, s + saturation))
    v = max(0.0, min(1.0, v + light))
    return colorsys.hsv_to_rgb(h, s, v)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def mark(obj):
    obj[UNIT_TAG] = True
    return obj


def material(name, color, metallic=0.0, roughness=0.55, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    rgba = (*color, 1.0)
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
        if emission:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
            elif "Emission" in bsdf.inputs:
                bsdf.inputs["Emission"].default_value = (*emission, 1.0)
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def finish_obj(obj, name, mat=None, parent=None, bevel=0.04, smooth=True):
    obj.name = name
    mark(obj)
    if parent is not None:
        obj.parent = parent
    if mat is not None and hasattr(obj.data, "materials"):
        obj.data.materials.append(mat)
    if smooth and obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True
    if bevel and obj.type == "MESH":
        mod = obj.modifiers.new("Soft bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return obj


def cube(name, loc, scale, mat, parent=None, rot=(0,0,0), bevel=0.05):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish_obj(o, name, mat, parent, bevel, False)


def sphere(name, loc, scale, mat, parent=None, segments=24, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish_obj(o, name, mat, parent, 0.025, True)


def ico(name, loc, scale, mat, parent=None, subdivision=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivision, radius=1, location=loc)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish_obj(o, name, mat, parent, 0.025, True)


def cyl(name, loc, radius, depth, mat, parent=None, rot=(0,0,0), vertices=16, bevel=0.035):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    return finish_obj(bpy.context.object, name, mat, parent, bevel, True)


def cone(name, loc, radius1, radius2, depth, mat, parent=None, rot=(0,0,0), vertices=12):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=loc, rotation=rot)
    return finish_obj(bpy.context.object, name, mat, parent, 0.025, True)


def torus(name, loc, major, minor, mat, parent=None, rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=28, minor_segments=8, location=loc, rotation=rot)
    return finish_obj(bpy.context.object, name, mat, parent, 0.015, True)


def empty(name, loc=(0,0,0), parent=None):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.location = loc
    if parent is not None:
        o.parent = parent
    mark(o)
    return o


def weapon(parent, kind, mats, level, side=1, hero=False):
    metal, accent, wood, magic = mats["metal"], mats["accent"], mats["wood"], mats["magic"]
    x = 0.48 * side
    y = -0.02
    z = 1.05
    gain = 1 + (level - 1) * (0.007 if hero else 0.012)
    node = empty("weapon.R" if side > 0 else "weapon.L", parent=parent)
    if kind in {"sword","greatsword","curved_saber","rapier","wind_rapier","glaive","scimitar","signal_blade","parrying_dagger"}:
        length = {"greatsword":1.45,"glaive":1.50,"rapier":1.10,"wind_rapier":1.20,"scimitar":1.18,"parrying_dagger":0.65}.get(kind,1.0) * gain
        cyl("grip", (x,z-0.42,y), .055, .35, wood, node, rot=(math.pi/2,0,0), vertices=10)
        cube("blade", (x,z+length*.15,y), (.045, length*.48, .10 if kind!="rapier" else .055), metal, node, bevel=.025)
        cone("tip", (x,z+length*.66,y), .11, 0, .28, metal, node)
        cube("guard", (x,z-.18,y), (.24,.035,.07), accent, node, bevel=.02)
        if kind in {"curved_saber","scimitar"}:
            cube("curve_back", (x+.08*side,z+.23,y), (.08,.34,.08), metal, node, rot=(0,0,-.18*side), bevel=.02)
    elif kind in {"spear","sun_spear","solar_lance","wing_spear","sky_lance"}:
        length = 1.75 * gain
        cyl("shaft", (x,z+.10,y), .045, length, wood, node, rot=(0,0,0), vertices=10)
        cone("spearhead", (x,z+length*.62,y), .15, 0, .42, metal, node)
        torus("spear_ring", (x,z+length*.39,y), .10, .025, accent, node)
    elif kind in {"heavy_axe","twin_axes","rift_axes"}:
        cyl("axe_handle", (x,z,y), .055, 1.1*gain, wood, node, vertices=10)
        cube("axe_head", (x+.16*side,z+.52,y), (.25,.17,.08), metal, node, rot=(0,0,.28*side), bevel=.035)
        cone("axe_edge", (x+.36*side,z+.52,y), .19, .02, .35, metal, node, rot=(0,math.pi/2,0))
    elif kind in {"rune_hammer","forge_hammer","warhammer","shock_hammer"}:
        cyl("hammer_handle", (x,z-.02,y), .065, 1.15*gain, wood, node, vertices=10)
        cube("hammer_head", (x,z+.58,y), (.36,.20,.22), metal, node, bevel=.06)
        for sx in (-1,1):
            cube("hammer_cap", (x+sx*.33,z+.58,y), (.11,.24,.27), accent, node, bevel=.04)
        if "rune" in kind or "shock" in kind:
            ico("hammer_core", (x,z+.58,y-.24), (.10,.10,.10), magic, node)
    elif kind in {"bow","moon_bow","grove_bow"}:
        for sy in (-1,1):
            seg = cyl("bow_limb", (x,z+sy*.35,y), .035, .72*gain, wood, node, rot=(0,0,.42*sy*side), vertices=10)
        cube("bow_grip", (x,z,y), (.05,.18,.05), accent, node)
        cube("bow_string", (x+.01*side,z,y-.06), (.008,.72,.008), magic if "moon" in kind else metal, node, bevel=0)
    elif kind in {"rifle","alchemist_launcher"}:
        cube("stock", (x,z-.15,y), (.08,.34,.10), wood, node, rot=(0,0,.08*side))
        cyl("barrel", (x,z+.28,y), .05, 1.05*gain, metal, node, vertices=12)
        torus("sight", (x,z+.62,y), .07,.015,accent,node,rot=(math.pi/2,0,0))
        if kind == "alchemist_launcher":
            sphere("flask_chamber", (x,z+.08,y-.12), (.13,.18,.13), magic, node)
    elif kind in {"staff","healing_staff","ice_staff","storm_staff","tide_staff","fire_staff","thorn_staff"}:
        cyl("staff", (x,z,y), .045, 1.65*gain, wood, node, vertices=10)
        orbmat = magic
        ico("focus", (x,z+.86,y), (.18,.18,.18), orbmat, node)
        for a in range(3):
            torus("focus_ring", (x,z+.86,y), .23+.04*a,.015,accent,node,rot=(math.pi/2,a*.5,0))
    elif kind in {"storm_orb","astral_orb","fire_wings","crystal_breath","fangs","fists","maul_fists"}:
        ico("power_focus", (x,z+.12,y-.10), (.22,.22,.22), magic, node)
        torus("power_ring", (x,z+.12,y-.10), .31,.025,accent,node,rot=(math.pi/2,0,0))
    elif kind in {"twin_daggers","shadow_daggers"}:
        cube("dagger_blade", (x,z+.08,y), (.035,.32,.07), metal, node, bevel=.02)
        cone("dagger_tip", (x,z+.43,y), .08,0,.18,metal,node)
        cube("dagger_grip", (x,z-.22,y), (.05,.14,.05), accent, node)
    elif kind == "bomb":
        sphere("bomb", (x,z,y), (.23,.23,.23), metal, node)
        cyl("fuse", (x,z+.26,y), .025,.20,wood,node,rot=(0,0,.4),vertices=8)
    else:
        ico("weapon_focus", (x,z,y), (.18,.18,.18), magic, node)
    return node


def offhand(parent, kind, mats, level, side=-1):
    if not kind or kind == "none":
        return
    x, z, y = .48*side, 1.02, -.02
    node = empty("offhand.L", parent=parent)
    metal, accent, wood, magic = mats["metal"], mats["accent"], mats["wood"], mats["magic"]
    if "shield" in kind or kind in {"buckler","sun_buckler"}:
        if "tower" in kind or "fortress" in kind:
            cube("shield", (x,z,y-.18), (.37,.62,.09), metal, node, bevel=.08)
        elif "kite" in kind or "ice" in kind:
            cube("shield", (x,z,y-.18), (.36,.48,.09), metal, node, rot=(0,0,.10*side), bevel=.10)
            cone("shield_point", (x,z-.48,y-.18), .34,0,.40,metal,node)
        else:
            cyl("shield", (x,z,y-.18), .33,.10,metal,node,rot=(math.pi/2,0,0),vertices=24)
        ico("shield_emblem", (x,z,y-.30), (.10,.10,.05), accent, node)
    elif kind in {"quiver","ammo_roll","medical_satchel","loot_satchel","potion_rack","bomb_pack"}:
        cube("pack", (x*.55,1.05,.28), (.18,.32,.16), wood if kind!="potion_rack" else metal, node, bevel=.06)
        if kind in {"quiver","ammo_roll"}:
            for i in range(4):
                cyl("ammo", (x*.55+(i-1.5)*.045,1.34,.28), .018,.40,metal,node,vertices=8)
        elif kind in {"bomb_pack","potion_rack"}:
            for i in range(3):
                sphere("payload", (x*.55+(i-1)*.10,1.10,.12), (.07,.10,.07), magic if kind=="potion_rack" else metal, node)
    else:
        ico("offhand_focus", (x,z,y-.10), (.16,.16,.16), magic, node)
        torus("offhand_ring", (x,z,y-.10), .23,.018,accent,node,rot=(math.pi/2,0,0))


def add_wings(root, mats, scale=1.0, feathered=True, level=1):
    for side in (-1,1):
        wing = empty("wing.L" if side < 0 else "wing.R", loc=(0,1.15,0), parent=root)
        for i in range(5 + min(3, level//12)):
            length = (.68 + i*.11) * scale
            x = side * (.38 + i*.18)
            z = 1.18 - i*.04
            m = mats["accent"] if feathered and i%2 else mats["primary"]
            part = cone(f"wing_feather_{i}", (x,z,.05), .13, .025, length, m, wing, rot=(math.pi/2,0,-side*(.25+i*.08)), vertices=8)
            part.scale.z = 1.15


def add_cape(root, cape, mats, scale=1.0):
    if not cape or cape == "none":
        return
    length = {"short":.55,"split":.75,"scarf":.38,"shawl":.48,"fur":.48,"coat_tail":.72,"half_cape":.72,"back_banner":.78,"long":.95,"royal_long":1.10,"royal_short":.70,"flowing":1.0,"leaf_cloak":.92,"ash_cloak":.98,"sand_cloak":1.0,"cosmic_long":1.12,"officer_coat":.82,"apron":.62,"long_scarf":.82,"split_scarf":.72}.get(cape,.72)
    width = .55 if "long" in cape or cape in {"flowing","leaf_cloak","sand_cloak"} else .44
    m = mats["secondary"]
    if cape in {"fur","leaf_cloak"}:
        m = mats["accent"]
    cube("cape", (0,1.02,-.22), (width*scale,length*.50*scale,.035), m, root, rot=(.10,0,0), bevel=.04)
    if "split" in cape or cape in {"coat_tail","officer_coat"}:
        cube("cape_split", (.18, .73,-.24), (.17,length*.38,.03), mats["primary"], root, rot=(.13,0,.05), bevel=.03)


def helmet(root, kind, mats, level, head_z=1.66, scale=1.0):
    if not kind or kind == "none":
        return
    primary, metal, accent, magic = mats["primary"], mats["metal"], mats["accent"], mats["magic"]
    k = kind.lower()
    if "hood" in k or "veil" in k or "bandana" in k:
        sphere("hood", (0,head_z+.03,0), (.25*scale,.27*scale,.24*scale), primary, root)
        if "mask" in k or "veil" in k:
            cube("mask", (0,head_z-.03,-.22), (.18,.10,.035), mats["secondary"], root, bevel=.02)
    elif "circlet" in k or "crown" in k or "halo" in k:
        torus("circlet", (0,head_z+.10,0), .24*scale,.025,accent,root,rot=(math.pi/2,0,0))
        spikes = 7 if "crown" in k else 4
        for i in range(spikes):
            a = (i/(spikes-1)-.5)*1.35 if spikes>1 else 0
            cone("crown_spike", (math.sin(a)*.20,head_z+.22,math.cos(a)*-.08), .04,.0,.19+level*.0015, accent, root, rot=(0,0,-a*.2), vertices=6)
        if "crystal" in k or "storm" in k or "astral" in k:
            ico("crown_gem", (0,head_z+.19,-.23), (.07,.10,.05), magic, root)
    elif "hat" in k or "tricorn" in k:
        cyl("hat_brim", (0,head_z+.15,0), .31,.045,primary,root,vertices=24)
        cone("hat_crown", (0,head_z+.30,0), .22,.15,.30, mats["secondary"], root, vertices=16)
        cone("hat_feather", (.18,head_z+.50,.02), .045,.01,.55,accent,root,rot=(0,0,-.5),vertices=8)
    elif "goggles" in k:
        for side in (-1,1):
            torus("goggle", (side*.10,head_z+.05,-.22), .075,.018,metal,root,rot=(math.pi/2,0,0))
            sphere("lens", (side*.10,head_z+.05,-.235), (.055,.055,.015), magic, root)
        cube("strap", (0,head_z+.05,.02), (.25,.025,.02),mats["secondary"],root,bevel=.01)
    else:
        sphere("helmet", (0,head_z+.05,0), (.25*scale,.25*scale,.24*scale), metal, root)
        cube("visor", (0,head_z+.02,-.23), (.18,.075,.04), mats["secondary"], root, bevel=.02)
        if any(s in k for s in ["sun","winged","crest","heavy","bastion","frost","forge"]):
            cone("helm_crest", (0,head_z+.34,.02), .075,.02,.42,accent,root,rot=(0,0,.03),vertices=8)


def level_armor(root, mats, level, maximum, hero=False, scale=1.0):
    ratio = (level-1) / max(1, maximum-1)
    stages = 9 if hero else 4
    tier = min(stages, int(ratio*(stages+1)))
    # Every level changes dimensions/material intensity; milestone tiers add real geometry.
    chest_w = (.32 + .035*tier + .025*ratio) * scale
    cube("level_chest", (0,1.08,-.09), (chest_w,.25+.015*tier,.12+.01*tier), mats["metal"], root, bevel=.07)
    cube("level_belt", (0,.79,0), (.33+.02*tier,.055,.12), mats["accent"], root, bevel=.025)
    if tier >= 1:
        for side in (-1,1):
            sphere("pauldron", (side*.39*scale,1.24,.01), (.16+.012*tier,.11+.008*tier,.16), mats["metal"], root)
    if tier >= 2:
        for side in (-1,1):
            cube("greave", (side*.17,.38,-.02), (.11,.24,.10), mats["metal"], root, bevel=.04)
    if tier >= 3:
        for side in (-1,1):
            cone("shoulder_spike", (side*.49*scale,1.33,.01), .06,.0,.25+.015*tier,mats["accent"],root,rot=(0,0,-side*.55),vertices=6)
    if tier >= 4:
        ico("chest_gem", (0,1.13,-.225), (.07+.005*tier,.09+.005*tier,.04), mats["magic"], root)
    if tier >= 5:
        for side in (-1,1):
            cube("arm_bracer", (side*.43,.88,-.03), (.08,.18,.09), mats["accent"], root, bevel=.03)
    if tier >= 6:
        torus("waist_aura", (0,.72,0), .43+.02*tier,.018,mats["magic"],root,rot=(0,0,0))
    if tier >= 7:
        for side in (-1,1):
            ico("shoulder_gem", (side*.40,1.30,-.13), (.07,.07,.05), mats["magic"], root)
    if tier >= 8:
        torus("ground_aura", (0,.07,0), .58+.025*tier,.025,mats["magic"],root)
    if tier >= 9:
        for i in range(5):
            a = i*math.tau/5
            ico("orbit_gem", (math.sin(a)*.52,1.18+math.cos(a)*.12,-.05), (.045,.045,.045), mats["magic"], root)


def build_humanoid(spec, level, kind, mats):
    hero = kind == "hero"
    max_level = 50 if hero else 15
    scale = float(spec.get("scale",1.0)) * (1 + (level-1)*(0.0018 if hero else 0.004))
    dwarf = spec.get("archetype") == "dwarf"
    root = empty("root")
    body = empty("body", parent=root)
    leg_len = .48 if not dwarf else .34
    torso_z = .98 if not dwarf else .86
    shoulder_z = 1.23 if not dwarf else 1.10
    head_z = 1.62 if not dwarf else 1.42
    skin = mats["skin"]
    # Boots and legs use separate named nodes so the game can later animate rigid limbs.
    for side in (-1,1):
        leg = empty("leg.L" if side<0 else "leg.R", parent=body)
        cyl("leg", (side*.16,leg_len*.62,.02), .105*scale, leg_len, mats["secondary"], leg, vertices=12)
        cube("boot", (side*.16,.14,-.10), (.13,.14,.20), mats["leather"], leg, bevel=.045)
        arm = empty("arm.L" if side<0 else "arm.R", parent=body)
        cyl("upper_arm", (side*.40,1.00,.0), .09*scale,.48,mats["primary"],arm,vertices=12)
        sphere("hand", (side*.42,.77,-.02), (.09,.09,.09),skin,arm)
    cube("torso", (0,torso_z,0), (.30*scale,.35*scale,.20*scale), mats["primary"], body, bevel=.09)
    cube("chest_layer", (0,torso_z+.08,-.18), (.27*scale,.24*scale,.06), mats["secondary"], body, bevel=.055)
    cyl("neck", (0,1.38 if not dwarf else 1.23,0), .09,.18,skin,body,vertices=12)
    face_scale = .20 if spec.get("gender") == "female" else .22
    sphere("head", (0,head_z,0), (face_scale*scale,.24*scale,.21*scale), skin, body)
    # Nose, ears and eyes keep close-up portrait renders from looking blank.
    cone("nose", (0,head_z-.01,-.21*scale), .035,.015,.10,skin,body,rot=(math.pi/2,0,0),vertices=8)
    for side in (-1,1):
        sphere("ear", (side*.21*scale,head_z,.0), (.045,.065,.035),skin,body)
        sphere("eye", (side*.075,head_z+.04,-.195*scale), (.027,.021,.018),mats["eye"],body,segments=16,rings=10)
    # Hair geometry is intentionally blocky/stylized for phone readability.
    if "helm" not in spec.get("helmet","") and "hood" not in spec.get("helmet",""):
        for side in (-1,0,1):
            cone("hair", (side*.09,head_z+.20,.07), .09,.02,.28,mats["hair"],body,rot=(0,0,side*.20),vertices=8)
    helmet(body, spec.get("helmet"), mats, level, head_z, scale)
    add_cape(body, spec.get("cape"), mats, scale)
    if spec.get("flying") or spec.get("archetype") == "winged_humanoid":
        add_wings(body,mats,scale=1.0+level/max_level*.12,feathered=True,level=level)
    weapon(body,spec.get("weapon","sword"),mats,level,1,hero)
    # Paired weapons get explicit second-hand geometry.
    if spec.get("weapon") in {"twin_axes","rift_axes","twin_daggers","shadow_daggers"}:
        weapon(body,spec.get("weapon"),mats,level,-1,hero)
    else:
        offhand(body,spec.get("offhand"),mats,level,-1)
    level_armor(body,mats,level,max_level,hero,scale)
    # Motif token gives each design a persistent identity across all levels.
    ico("motif_token", (0,.88,-.26), (.055,.07,.035), mats["magic"], body)
    root.scale = (scale,scale,scale)
    return root


def build_giant(spec, level, kind, mats):
    root = empty("root")
    scale = float(spec.get("scale",1.3))*(1+(level-1)*.004)
    rockmat=mats["primary"]
    sphere("torso",(0,1.15,0),(.58,.72,.48),rockmat,root)
    sphere("head",(0,1.90,-.04),(.36,.34,.33),rockmat,root)
    for side in (-1,1):
        arm=empty("arm.L" if side<0 else "arm.R",parent=root)
        sphere("shoulder",(side*.64,1.40,0),(.30,.31,.30),mats["secondary"],arm)
        sphere("forearm",(side*.76,.92,0),(.27,.42,.27),rockmat,arm)
        sphere("fist",(side*.78,.48,-.03),(.30,.27,.30),mats["secondary"],arm)
        leg=empty("leg.L" if side<0 else "leg.R",parent=root)
        sphere("thigh",(side*.28,.50,0),(.30,.45,.32),rockmat,leg)
        cube("foot",(side*.29,.11,-.14),(.31,.16,.37),mats["secondary"],leg,bevel=.09)
    for i in range(5+level//4):
        a=i*math.tau/(5+level//4)
        ico("rune_stone",(math.sin(a)*.48,1.28+math.cos(a)*.34,-.42),(.07,.10,.05),mats["magic"],root)
    level_armor(root,mats,level,15,False,scale=.9)
    root.scale=(scale,scale,scale)
    return root


def build_construct(spec, level, kind, mats):
    hero=kind=="hero";max_level=50 if hero else 15
    root=empty("root");scale=float(spec.get("scale",1.3))*(1+(level-1)*(0.002 if hero else .004))
    cube("core_body",(0,1.0,0),(.48,.55,.39),mats["metal"],root,bevel=.12)
    ico("power_core",(0,1.05,-.42),(.16,.16,.08),mats["magic"],root)
    cube("head",(0,1.68,0),(.30,.27,.28),mats["secondary"],root,bevel=.08)
    for side in (-1,1):
        arm=empty("arm.L" if side<0 else "arm.R",parent=root)
        sphere("shoulder",(side*.62,1.25,0),(.25,.23,.25),mats["metal"],arm)
        cube("forearm",(side*.66,.86,0),(.19,.34,.20),mats["secondary"],arm,bevel=.07)
        sphere("fist",(side*.68,.50,-.02),(.22,.20,.22),mats["metal"],arm)
        leg=empty("leg.L" if side<0 else "leg.R",parent=root)
        cube("leg",(side*.25,.42,0),(.19,.35,.20),mats["metal"],leg,bevel=.07)
        cube("foot",(side*.25,.10,-.15),(.24,.12,.34),mats["secondary"],leg,bevel=.06)
    weapon(root,spec.get("weapon","maul_fists"),mats,level,1,hero)
    offhand(root,spec.get("offhand"),mats,level,-1)
    # Mechanical plates visibly multiply with level.
    count=2+int((level-1)/max_level*8)
    for i in range(count):
        a=i*math.tau/count
        cube("plate",(math.sin(a)*.48,1.0+math.cos(a)*.25,-.40),(.10,.12,.04),mats["accent"],root,rot=(0,0,a),bevel=.02)
    level_armor(root,mats,level,max_level,hero,scale=.95)
    root.scale=(scale,scale,scale)
    return root


def build_flying_beast(spec, level, kind, mats):
    root=empty("root");scale=float(spec.get("scale",1.25))*(1+(level-1)*.004)
    phoenix=spec.get("archetype")=="phoenix";drake=spec.get("archetype")=="drake"
    sphere("torso",(0,1.05,0),(.38,.48,.62),mats["primary"],root)
    sphere("chest",(0,1.13,-.43),(.28,.34,.27),mats["secondary"],root)
    sphere("head",(0,1.58,-.58),(.25,.24,.30),mats["primary"],root)
    cone("beak_muzzle",(0,1.55,-.90),.13,.02,.40,mats["accent"],root,rot=(math.pi/2,0,0),vertices=8)
    for side in (-1,1):
        sphere("eye",(side*.09,1.64,-.82),(.035,.03,.025),mats["eye"],root)
        leg=empty("leg.L" if side<0 else "leg.R",parent=root)
        cyl("leg",(side*.18,.55,-.10),.055,.48,mats["secondary"],leg,vertices=10)
        for t in (-1,0,1):
            cone("talon",(side*.18+t*.06,.30,-.27),.028,.005,.22,mats["accent"],leg,rot=(math.pi/2,0,0),vertices=6)
    # Wings are broad enough to remain readable in zoomed-out battle scenes.
    add_wings(root,mats,scale=1.35 if drake else 1.20,feathered=phoenix,level=level)
    tail_count=5+min(4,level//4)
    for i in range(tail_count):
        m=mats["accent"] if phoenix and i%2 else mats["primary"]
        cone("tail",((i-tail_count/2)*.08,.92,.45+i*.17),.11,.02,.48,m,root,rot=(math.pi/2,0,0),vertices=8)
    if drake or spec.get("archetype")=="wyvern":
        for i in range(3+level//4):
            ico("spine",(0,1.35+i*.02,.18+i*.12),(.07,.14,.06),mats["magic"],root)
    if level>=5:
        torus("beast_aura",(0,.25,0),.62+.015*level,.025,mats["magic"],root)
    root.scale=(scale,scale,scale)
    return root


def build_unit(spec, level, kind, mats):
    archetype=spec.get("archetype","humanoid")
    if archetype=="giant": return build_giant(spec,level,kind,mats)
    if archetype=="construct": return build_construct(spec,level,kind,mats)
    if archetype in {"wyvern","drake","phoenix"}: return build_flying_beast(spec,level,kind,mats)
    return build_humanoid(spec,level,kind,mats)


def create_materials(spec, level, kind):
    maximum=50 if kind=="hero" else 15
    ratio=(level-1)/max(1,maximum-1)
    p=adjust(hex_rgb(spec["primary"]), light=.10*ratio, saturation=.05*ratio)
    s=adjust(hex_rgb(spec["secondary"]), light=.06*ratio)
    a=adjust(hex_rgb(spec["accent"]), light=.10*ratio, saturation=.03)
    skin=(0.72,0.48,0.34) if spec.get("gender")!="female" else (0.78,0.56,0.43)
    if spec.get("archetype") in {"giant","construct","drake","wyvern","phoenix"}: skin=p
    magic=adjust(a,light=.16,saturation=.08)
    return {
      "primary":material("Primary",p,metallic=.08 if kind=="hero" else .04,roughness=.48),
      "secondary":material("Secondary",s,metallic=.08,roughness=.58),
      "accent":material("Accent",a,metallic=.62,roughness=.28),
      "metal":material("Metal",adjust(s,.18),metallic=.82,roughness=.24),
      "wood":material("Wood",(0.24,0.12,0.07),metallic=.0,roughness=.72),
      "leather":material("Leather",(0.18,0.10,0.07),metallic=.0,roughness=.68),
      "skin":material("Skin",skin,metallic=.0,roughness=.52),
      "hair":material("Hair",(0.10,0.065,0.045),metallic=.0,roughness=.72),
      "eye":material("Eye",(0.06,0.09,0.08),metallic=.0,roughness=.25),
      "magic":material("Magic",magic,metallic=.18,roughness=.18,emission=magic,emission_strength=.9+ratio*1.3),
    }


def setup_stage(spec, root, preview_size):
    # Ground is intentionally not tagged for GLB export.
    ground_mat=material("PreviewGround",(0.055,0.07,0.065),roughness=.92)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=1.45,depth=.10,location=(0,.02,0))
    ground=bpy.context.object;ground.name="preview_ground";ground.data.materials.append(ground_mat)
    bpy.ops.object.light_add(type="AREA",location=(3.4,4.5,-4.0));key=bpy.context.object;key.data.energy=850;key.data.shape='DISK';key.data.size=4.0
    key.rotation_euler=(math.radians(42),0,math.radians(34))
    bpy.ops.object.light_add(type="AREA",location=(-3.0,2.6,-1.8));fill=bpy.context.object;fill.data.energy=500;fill.data.size=3.5
    bpy.ops.object.light_add(type="AREA",location=(0,3.6,3.4));rim=bpy.context.object;rim.data.energy=700;rim.data.size=3.0
    bpy.ops.object.camera_add(location=(4.6,3.1,-6.2));cam=bpy.context.object
    target=Vector((0,1.05,0));direction=target-cam.location;cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();cam.data.lens=58
    scene=bpy.context.scene;scene.camera=cam
    try: scene.render.engine='BLENDER_EEVEE_NEXT'
    except Exception: scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=preview_size;scene.render.resolution_y=preview_size;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
    scene.render.resolution_percentage=100
    scene.world.color=(0.018,0.024,0.028)


def export_selected_glb(path: Path):
    bpy.ops.object.select_all(action="DESELECT")
    tagged=[]
    for obj in bpy.context.scene.objects:
        if obj.get(UNIT_TAG):
            obj.select_set(True);tagged.append(obj)
    if tagged:
        bpy.context.view_layer.objects.active=tagged[0]
    kwargs=dict(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
    try:
        bpy.ops.export_scene.gltf(**kwargs,export_lights=False,export_cameras=False)
    except TypeError:
        bpy.ops.export_scene.gltf(**kwargs)


def generate_one(kind, unit_id, spec, level, output_root, save_blend, preview_size):
    clear_scene()
    mats=create_materials(spec,level,kind)
    root=build_unit(spec,level,kind,mats)
    root.name=f"{kind}_{unit_id}_level_{level:02d}"
    root["emberfall_kind"]=kind;root["emberfall_unit"]=unit_id;root["emberfall_level"]=level;root["emberfall_name"]=spec["name"]
    setup_stage(spec,root,preview_size)
    folder=output_root/("troops" if kind=="troop" else "heroes")/unit_id/f"level-{level:02d}"
    folder.mkdir(parents=True,exist_ok=True)
    glb=folder/f"{unit_id}-level-{level:02d}.glb"
    png=folder/f"{unit_id}-level-{level:02d}.png"
    export_selected_glb(glb)
    bpy.context.scene.render.filepath=str(png);bpy.ops.render.render(write_still=True)
    blend=None
    if save_blend:
        blend=folder/f"{unit_id}-level-{level:02d}.blend";bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    meta={"kind":kind,"id":unit_id,"name":spec["name"],"level":level,"archetype":spec.get("archetype"),"weapon":spec.get("weapon"),"silhouette":spec.get("silhouette"),"motif":spec.get("motif"),"glb":glb.name,"preview":png.name,"blend":blend.name if blend else None}
    (folder/"metadata.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    return meta


def update_manifest(output_root: Path, items):
    manifest_path=output_root/"manifest.json"
    existing={"generator":"tools/blender/generate_unit.py","assets":[]}
    if manifest_path.exists():
        try: existing=json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception: pass
    index={(x["kind"],x["id"],x["level"]):x for x in existing.get("assets",[])}
    for x in items:index[(x["kind"],x["id"],x["level"])]=x
    existing["assets"]=sorted(index.values(),key=lambda x:(x["kind"],x["id"],x["level"]))
    manifest_path.parent.mkdir(parents=True,exist_ok=True)
    manifest_path.write_text(json.dumps(existing,indent=2),encoding="utf-8")


def main():
    args=cli_args();specs=json.loads(SPECS_PATH.read_text(encoding="utf-8"));out=Path(args.output).resolve();items=[]
    work=[]
    if args.all or args.all_troops:
        work.extend(("troop",uid,spec) for uid,spec in specs["troops"].items())
    if args.all or args.all_heroes:
        work.extend(("hero",uid,spec) for uid,spec in specs["heroes"].items())
    if not work:
        group=specs["troops" if args.kind=="troop" else "heroes"]
        if args.unit not in group: raise SystemExit(f"Unknown {args.kind}: {args.unit}. Available: {', '.join(group)}")
        work=[(args.kind,args.unit,group[args.unit])]
    for kind,uid,spec in work:
        maximum=specs["troop_max_level"] if kind=="troop" else specs["hero_max_level"]
        levels=parse_levels(args.levels,maximum)
        for level in levels:
            print(f"[Emberfall Blender] {kind} {uid} level {level}/{maximum}")
            items.append(generate_one(kind,uid,spec,level,out,args.save_blend,args.preview_size))
    update_manifest(out,items)
    print(f"Generated {len(items)} asset level(s) in {out}")


if __name__=="__main__":
    main()
