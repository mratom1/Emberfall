#!/usr/bin/env python3
"""Polished native-Z-up procedural characters for Emberfall.

This generator is intentionally original.  It creates stylized game-ready meshes from
local design specs, with one export per actual progression level.  Humanoid characters
use posed, named rigid pieces so the browser game can later animate the same nodes.

Example:
  blender -b --python-exit-code 1 --python tools/blender/generate_character_v2.py -- \
    --kind troop --unit guardian --levels 1-15 --output generated/blender --save-blend
"""
from __future__ import annotations

import argparse
import colorsys
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
SPECS = ROOT / "art" / "blender" / "unit_specs.json"
TAG = "emberfall_export"

# -----------------------------------------------------------------------------
# CLI / progression
# -----------------------------------------------------------------------------

def args():
    raw = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--kind", choices=("troop", "hero"), default="troop")
    p.add_argument("--unit", default="guardian")
    p.add_argument("--levels", default="1")
    p.add_argument("--all-troops", action="store_true")
    p.add_argument("--all-heroes", action="store_true")
    p.add_argument("--all", action="store_true")
    p.add_argument("--output", default=str(ROOT / "generated" / "blender"))
    p.add_argument("--preview-size", type=int, default=512)
    p.add_argument("--save-blend", action="store_true")
    return p.parse_args(raw)


def level_list(text, maximum):
    out = set()
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = [int(x) for x in part.split("-", 1)]
            out.update(range(min(a, b), max(a, b) + 1))
        else:
            out.add(int(part))
    out = sorted(x for x in out if 1 <= x <= maximum)
    if not out:
        raise SystemExit(f"No levels in {text!r}; valid range is 1-{maximum}")
    return out


def tier(level, maximum):
    """0..5 progression tier while preserving exact per-level material/scale changes."""
    if maximum <= 15:
        return min(5, (level - 1) // 3)
    return min(5, (level - 1) // 10)

# -----------------------------------------------------------------------------
# Scene / material utilities
# -----------------------------------------------------------------------------

def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i+2], 16) / 255 for i in (0, 2, 4))


def shift(col, value=0.0, sat=0.0):
    h, s, v = colorsys.rgb_to_hsv(*col)
    return colorsys.hsv_to_rgb(h, max(0, min(1, s + sat)), max(0, min(1, v + value)))


def mat(name, col, metallic=0.0, rough=.5, emission=None, power=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*col, 1)
    bs.inputs["Metallic"].default_value = metallic
    bs.inputs["Roughness"].default_value = rough
    if emission:
        socket = bs.inputs.get("Emission Color") or bs.inputs.get("Emission")
        if socket:
            socket.default_value = (*emission, 1)
        strength = bs.inputs.get("Emission Strength")
        if strength:
            strength.default_value = power
    return m


def palette(spec, level, maximum):
    r = (level - 1) / max(1, maximum - 1)
    primary = shift(rgb(spec["primary"]), .04 + .08*r, .02*r)
    secondary = shift(rgb(spec["secondary"]), .02 + .05*r)
    accent = shift(rgb(spec["accent"]), .08*r, .04)
    female = spec.get("gender") == "female"
    skin = (0.78, .54, .40) if female else (.69, .44, .31)
    if spec.get("archetype") in ("giant", "construct", "drake", "wyvern", "phoenix"):
        skin = primary
    glow = shift(accent, .18, .10)
    return {
        "primary": mat("Primary", primary, .06, .42),
        "secondary": mat("Secondary", secondary, .10, .54),
        "accent": mat("Accent", accent, .62, .25),
        "metal": mat("Steel", shift(secondary, .25), .86, .20),
        "darkmetal": mat("DarkSteel", shift(secondary, .06), .78, .25),
        "leather": mat("Leather", (.18,.075,.038), .0, .72),
        "wood": mat("Wood", (.25,.10,.035), .0, .69),
        "skin": mat("Skin", skin, 0, .48),
        "hair": mat("Hair", (.075,.035,.018), 0, .67),
        "white": mat("EyeWhite", (.82,.86,.82), 0, .24),
        "eye": mat("Iris", (.035,.075,.065), .0, .20),
        "black": mat("Black", (.014,.017,.019), .0, .38),
        "glow": mat("Magic", glow, .16, .16, glow, .65 + 1.25*r),
        "clothlight": mat("ClothLight", shift(primary, .20), 0, .64),
    }


def parent(obj, root):
    obj.parent = root
    obj[TAG] = True
    return obj


def apply_scale(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.select_set(False)


def smooth(obj, bevel=0.0):
    if obj.type == "MESH":
        for p in obj.data.polygons:
            p.use_smooth = True
        if bevel:
            b = obj.modifiers.new("EdgeSoftening", "BEVEL")
            b.width = bevel
            b.segments = 2
    return obj


def add_mat(obj, material):
    if obj.type == "MESH":
        obj.data.materials.append(material)
    return obj


def sphere(name, loc, scale, material, root, segments=24, rings=16, bevel=0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; apply_scale(o)
    add_mat(o, material); smooth(o, bevel); return parent(o, root)


def ico(name, loc, scale, material, root, subdivisions=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale;apply_scale(o);add_mat(o,material);smooth(o,.012);return parent(o,root)


def cube(name, loc, scale, material, root, rot=(0,0,0), bevel=.035):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o=bpy.context.object;o.name=name;o.scale=scale;apply_scale(o);add_mat(o,material)
    if bevel: smooth(o,bevel)
    return parent(o,root)


def cyl(name, loc, radius, depth, material, root, rot=(0,0,0), vertices=16, bevel=.018):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    o=bpy.context.object;o.name=name;add_mat(o,material);smooth(o,bevel);return parent(o,root)


def cone(name, loc, r1, r2, depth, material, root, rot=(0,0,0), vertices=12):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot)
    o=bpy.context.object;o.name=name;add_mat(o,material);smooth(o,.012);return parent(o,root)


def torus(name, loc, major, minor, material, root, rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=28,
                                    minor_segments=8, location=loc, rotation=rot)
    o=bpy.context.object;o.name=name;add_mat(o,material);smooth(o,.008);return parent(o,root)


def segment(name, a, b, radius, material, root, vertices=14):
    """Cylinder between arbitrary Z-up points."""
    a,b=Vector(a),Vector(b); mid=(a+b)*.5; vec=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=vec.length, location=mid)
    o=bpy.context.object;o.name=name;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector((0,0,1)).rotation_difference(vec.normalized())
    add_mat(o,material);smooth(o,.014);return parent(o,root)


def empty(name):
    o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o[TAG]=True;return o

# -----------------------------------------------------------------------------
# Humanoid body / face
# -----------------------------------------------------------------------------

def face(root, p, female=False, beard=False, level=1):
    z=1.92
    head=sphere("Head",(0,-.015,z),(.205,.19,.245),p["skin"],root)
    # Ears
    sphere("Ear.L",(-.205,-.005,z),(.035,.025,.052),p["skin"],root,16,10)
    sphere("Ear.R",(.205,-.005,z),(.035,.025,.052),p["skin"],root,16,10)
    # Stylized face points toward -Y.
    sphere("Eye.L",(-.073,-.188,z+.045),(.040,.020,.032),p["white"],root,16,10)
    sphere("Eye.R",(.073,-.188,z+.045),(.040,.020,.032),p["white"],root,16,10)
    sphere("Iris.L",(-.073,-.207,z+.045),(.018,.009,.020),p["eye"],root,12,8)
    sphere("Iris.R",(.073,-.207,z+.045),(.018,.009,.020),p["eye"],root,12,8)
    sphere("Brow.L",(-.073,-.211,z+.103),(.052,.010,.012),p["hair"],root,12,8)
    sphere("Brow.R",(.073,-.211,z+.103),(.052,.010,.012),p["hair"],root,12,8)
    cone("Nose",(0,-.225,z-.005),.036,.012,.10,p["skin"],root,rot=(math.pi/2,0,0),vertices=10)
    cube("Mouth",(0,-.212,z-.105),(.055,.008,.009),p["black"],root,bevel=.006)
    # Hair cap + readable tufts.
    sphere("HairCap",(0,.006,z+.105),(.216,.194,.166),p["hair"],root)
    for i,x in enumerate((-.14,-.07,0,.07,.14)):
        cone(f"HairTuft.{i}",(x,-.135,z+.245),.052,.010,.17,p["hair"],root,rot=(0.08,0,(i-2)*.08),vertices=8)
    if beard and not female:
        sphere("Beard",(0,-.184,z-.145),(.155,.055,.135),p["hair"],root,20,12)


def legs(root,p,scale=1.0,heavy=False):
    hips_z=.91
    stance=.19 if not heavy else .235
    for side,label in ((-1,"L"),(1,"R")):
        hip=(side*.17,0,hips_z)
        knee=(side*stance,-.015,.55)
        ankle=(side*stance,-.005,.20)
        segment(f"Thigh.{label}",hip,knee,.105*scale,p["secondary"],root)
        segment(f"Shin.{label}",knee,ankle,.092*scale,p["primary"],root)
        cube(f"Boot.{label}",(side*stance,-.075,.10),(.13,.22,.10),p["leather"],root,bevel=.05)
    sphere("Pelvis",(0,0,.92),(.29,.20,.20),p["secondary"],root)


def arms(root,p,weapon_type,offhand_type,heavy=False):
    sw=.40 if not heavy else .45
    for side,label in ((-1,"L"),(1,"R")):
        shoulder=(side*sw,0,1.48)
        # Right/weapon arm relaxed outward; left arm is bent forward for shield/offhand.
        if side>0:
            elbow=(side*.53,-.015,1.18); hand=(side*.55,-.045,.91)
        else:
            elbow=(side*.51,-.045,1.22); hand=(side*.46,-.26,1.09)
        segment(f"UpperArm.{label}",shoulder,elbow,.085,p["primary"],root)
        segment(f"Forearm.{label}",elbow,hand,.078,p["skin"],root)
        sphere(f"Hand.{label}",hand,(.085,.075,.085),p["skin"],root,18,12)


def torso(root,p,spec,t,hero=False):
    # Layered trapezoid-like torso via overlapping shapes, stronger than a single cube.
    sphere("TorsoBase",(0,0,1.27),(.34,.22,.43),p["primary"],root)
    cube("TunicFront",(0,-.205,1.24),(.285,.035,.31),p["clothlight"],root,bevel=.055)
    cube("Belt",(0,-.015,.94),(.325,.205,.045),p["leather"],root,bevel=.025)
    if t>=1:
        cube("Breastplate",(0,-.225,1.31),(.30,.045,.28),p["metal"],root,bevel=.055)
    if t>=2:
        for side,label in ((-1,"L"),(1,"R")):
            sphere(f"Pauldron.{label}",(side*.405,-.005,1.49),(.17,.19,.145),p["metal"],root)
            cube(f"Bracer.{label}",(side*.51,-.03,1.05),(.085,.09,.17),p["darkmetal"],root,bevel=.035)
    if t>=3:
        for side,label in ((-1,"L"),(1,"R")):
            cube(f"Greave.{label}",(side*.19,-.04,.39),(.12,.095,.20),p["metal"],root,bevel=.045)
        ico("ChestGem",(0,-.277,1.34),(.07,.035,.09),p["glow"],root)
    if t>=4:
        for side,label in ((-1,"L"),(1,"R")):
            cone(f"PauldronSpike.{label}",(side*.52,-.01,1.57),.065,.0,.23,p["accent"],root,
                 rot=(0,side*.60,0),vertices=8)
        torus("WaistRune",(0,-.08,.91),.34,.018,p["glow"],root,rot=(math.pi/2,0,0))
    if t>=5:
        torus("HeroicAura",(0,0,.055),.62,.025,p["glow"],root)
        for i in range(3 if not hero else 5):
            a=i*math.tau/(3 if not hero else 5)
            ico(f"OrbitRune.{i}",(math.sin(a)*.43,.02,1.26+math.cos(a)*.32),(.035,.035,.055),p["glow"],root)


def headgear(root,p,kind,t):
    k=(kind or "").lower(); z=1.92
    if "hood" in k or "veil" in k or "bandana" in k:
        sphere("Hood",(0,.02,z+.06),(.23,.205,.25),p["secondary"],root)
        # keep face visible: front mask only for assassin-style gear
        if "mask" in k or "veil" in k:
            cube("FaceMask",(0,-.215,z-.06),(.15,.018,.07),p["darkmetal"],root,bevel=.02)
        return
    if "circlet" in k or "crown" in k or "halo" in k:
        torus("Circlet",(0,-.005,z+.12),.215,.022,p["accent"],root,rot=(math.pi/2,0,0))
        count=5 if "crown" in k else 3
        for i in range(count):
            x=(i-(count-1)/2)*.075
            cone(f"CrownPoint.{i}",(x,-.02,z+.27+abs(x)*.05),.035,.006,.20,p["accent"],root,vertices=7)
        if t>=3:
            ico("CrownGem",(0,-.205,z+.12),(.05,.025,.065),p["glow"],root)
        return
    if "goggles" in k:
        for side,label in ((-1,"L"),(1,"R")):
            torus(f"Goggle.{label}",(side*.085,-.205,z+.055),.055,.013,p["accent"],root,rot=(math.pi/2,0,0))
            sphere(f"Lens.{label}",(side*.085,-.220,z+.055),(.036,.012,.036),p["glow"],root,12,8)
        return
    if "hat" in k or "tricorn" in k:
        cyl("HatBrim",(0,0,z+.21),.30,.035,p["primary"],root,vertices=24)
        cone("HatCrown",(0,0,z+.34),.20,.13,.28,p["secondary"],root,vertices=16)
        cone("HatFeather",(.18,-.02,z+.52),.035,.008,.45,p["accent"],root,rot=(0,-.35,-.4),vertices=8)
        return
    # Armor helmet as a rear/top shell, leaving eyes and mouth readable.
    sphere("HelmetShell",(0,.045,z+.09),(.225,.19,.19),p["metal"],root)
    cube("BrowGuard",(0,-.19,z+.11),(.19,.025,.045),p["darkmetal"],root,bevel=.02)
    if any(x in k for x in ("sun","winged","crest","heavy","bastion","frost","forge")) or t>=4:
        cone("HelmetCrest",(0,.03,z+.39),.065,.012,.36,p["accent"],root,vertices=8)


def cape(root,p,kind,t):
    k=(kind or "none").lower()
    if k=="none": return
    long = any(x in k for x in ("long","flowing","cloak","coat"))
    length=.83 if long else .58
    width=.39 if long else .33
    z=1.18 if long else 1.28
    cube("Cape",(0,.22,z),(width,.035,length/2),p["secondary"],root,rot=(-.08,0,0),bevel=.045)
    if "split" in k or "coat" in k:
        cube("CapeTail.L",(-.16,.23,.88),(.16,.03,.37),p["primary"],root,rot=(-.12,0,-.06),bevel=.03)
        cube("CapeTail.R",(.16,.23,.88),(.16,.03,.37),p["primary"],root,rot=(-.12,0,.06),bevel=.03)
    if t>=4:
        cube("CapeTrim",(0,.178,z-length/2+.06),(width,.012,.035),p["accent"],root,bevel=.012)

# -----------------------------------------------------------------------------
# Weapons / offhands
# -----------------------------------------------------------------------------

def blade(root,p,kind,level,maximum):
    r=(level-1)/max(1,maximum-1); hand=Vector((.55,-.045,.91))
    big="great" in kind or "glaive" in kind
    length=(1.03 if not big else 1.36)*(1+.10*r)
    # Diagonal outward sword gives a clean silhouette from the game camera.
    a=hand+Vector((.00,0,-.09)); b=a+Vector((.28,-.02,length))
    segment("WeaponGrip",a,a+Vector((.06,0,.26)),.045,p["leather"],root,10)
    segment("Blade",a+Vector((.05,0,.22)),b,.075 if big else .055,p["metal"],root,10)
    cone("BladeTip",b,(.09 if big else .07),0,.23,p["metal"],root,rot=(0,.27,0),vertices=8)
    segment("Crossguard",(.43,-.06,1.08),(.76,-.06,1.08),.035,p["accent"],root,10)
    if level>maximum*.55:
        ico("BladeRune",(.72,-.08,1.69),(.045,.025,.075),p["glow"],root)


def axe(root,p,kind,level,maximum,side=1):
    x=.55*side; hand=Vector((x,-.04,.92)); top=hand+Vector((.12*side,0,1.0))
    segment(f"AxeHandle.{side}",hand,top,.045,p["wood"],root,10)
    cube(f"AxeHead.{side}",(top.x+.11*side,-.04,top.z),(.18,.07,.16),p["metal"],root,rot=(0,.15*side,0),bevel=.035)
    cone(f"AxeEdge.{side}",(top.x+.27*side,-.04,top.z),.16,.02,.30,p["metal"],root,rot=(0,math.pi/2,0),vertices=8)


def spear(root,p,kind,level,maximum):
    hand=Vector((.55,-.04,.92)); bottom=hand+Vector((.12,0,-.55)); top=hand+Vector((-.16,0,1.30))
    segment("SpearShaft",bottom,top,.038,p["wood"],root,10)
    cone("SpearHead",top+Vector((-.035,0,.17)),.105,.0,.34,p["metal"],root,rot=(0,-.12,0),vertices=8)
    torus("SpearRune",tuple(top-Vector((0,0,.04))),.09,.014,p["glow"],root,rot=(math.pi/2,0,0))


def hammer(root,p,kind,level,maximum):
    hand=Vector((.55,-.04,.92)); top=hand+Vector((.12,0,1.0))
    segment("HammerHandle",hand,top,.055,p["wood"],root,10)
    cube("HammerHead",(top.x,-.04,top.z),(.31,.14,.18),p["metal"],root,bevel=.06)
    cube("HammerCap.L",(top.x-.32,-.04,top.z),(.10,.17,.21),p["accent"],root,bevel=.04)
    cube("HammerCap.R",(top.x+.32,-.04,top.z),(.10,.17,.21),p["accent"],root,bevel=.04)
    if "rune" in kind or "shock" in kind or level>maximum*.5:
        ico("HammerCore",(top.x,-.19,top.z),(.08,.035,.08),p["glow"],root)


def staff(root,p,kind,level,maximum):
    hand=Vector((.55,-.04,.92)); bottom=Vector((.66,.00,.12)); top=Vector((.48,-.02,2.18))
    segment("Staff",bottom,top,.038,p["wood"],root,10)
    ico("StaffFocus",(top.x,top.y,top.z+.12),(.15,.11,.15),p["glow"],root)
    for i in range(2 + (1 if level>maximum*.65 else 0)):
        torus(f"FocusRing.{i}",(top.x,top.y,top.z+.12),.20+i*.04,.012,p["accent"],root,rot=(math.pi/2,i*.4,0))


def bow(root,p,kind,level,maximum):
    # Bow is held left of the body but remains a weapon-defining silhouette.
    x=.61; z=1.25
    segment("BowTop",(x,-.08,z),(x+.16,-.08,z+.62),.026,p["wood"],root,10)
    segment("BowBottom",(x,-.08,z),(x+.16,-.08,z-.62),.026,p["wood"],root,10)
    segment("BowString",(x+.16,-.095,z+.62),(x+.16,-.095,z-.62),.006,p["glow"] if "moon" in kind else p["accent"],root,8)
    cube("BowGrip",(x,-.08,z),(.04,.035,.13),p["leather"],root,bevel=.015)


def rifle(root,p,kind,level,maximum):
    segment("RifleStock",(.46,-.13,.97),(.77,-.13,1.32),.075,p["wood"],root,12)
    segment("RifleBarrel",(.67,-.14,1.22),(.93,-.14,1.74),.040,p["metal"],root,12)
    cube("RifleReceiver",(.65,-.14,1.26),(.10,.07,.13),p["accent"],root,bevel=.025)
    if "alchemist" in kind:
        sphere("PotionChamber",(.62,-.22,1.31),(.10,.07,.12),p["glow"],root,18,12)


def magic_weapon(root,p,kind,level,maximum):
    ico("HandFocus",(.62,-.12,1.12),(.16,.10,.16),p["glow"],root)
    torus("FocusHalo",(.62,-.12,1.12),.24,.018,p["accent"],root,rot=(math.pi/2,0,0))


def weapon(root,p,kind,level,maximum):
    k=(kind or "sword").lower()
    if any(x in k for x in ("sword","saber","rapier","glaive","scimitar","blade")):
        return blade(root,p,k,level,maximum)
    if "axe" in k:
        axe(root,p,k,level,maximum,1)
        if "twin" in k or "rift" in k: axe(root,p,k,level,maximum,-1)
        return
    if any(x in k for x in ("spear","lance")):
        return spear(root,p,k,level,maximum)
    if any(x in k for x in ("hammer","mace")):
        return hammer(root,p,k,level,maximum)
    if "bow" in k:
        return bow(root,p,k,level,maximum)
    if any(x in k for x in ("staff",)):
        return staff(root,p,k,level,maximum)
    if any(x in k for x in ("rifle","launcher")):
        return rifle(root,p,k,level,maximum)
    if "dagger" in k:
        blade(root,p,k,level,maximum); axe(root,p,"dagger",level,maximum,-1); return
    return magic_weapon(root,p,k,level,maximum)


def offhand(root,p,kind,t):
    k=(kind or "none").lower()
    if k=="none": return
    if "shield" in k or "buckler" in k:
        large="tower" in k or "fortress" in k
        if large:
            cube("Shield",(-.47,-.34,1.10),(.31,.055,.53),p["metal"],root,bevel=.10)
        else:
            cyl("Shield",(-.47,-.33,1.10),.31,.08,p["metal"],root,rot=(math.pi/2,0,0),vertices=28,bevel=.025)
        ico("ShieldBoss",(-.47,-.385,1.10),(.09,.045,.09),p["accent"],root)
        if t>=3: torus("ShieldRune",(-.47,-.39,1.10),.20,.014,p["glow"],root,rot=(math.pi/2,0,0))
        return
    if any(x in k for x in ("quiver","satchel","pack","rack","roll")):
        cube("BackPack",(-.18,.22,1.17),(.18,.11,.30),p["leather"],root,bevel=.055)
        if "quiver" in k:
            for i in range(4): segment(f"Arrow.{i}",(-.30+i*.06,.24,1.22),(-.30+i*.06,.24,1.78),.012,p["accent"],root,8)
        if "potion" in k or "rack" in k:
            for i in range(3): sphere(f"Potion.{i}",(-.29+i*.11,.105,1.16),(.055,.035,.085),p["glow"],root,12,8)
        return
    ico("OffhandFocus",(-.47,-.30,1.10),(.14,.07,.14),p["glow"],root)


def wings(root,p,t,feather=True):
    for side,label in ((-1,"L"),(1,"R")):
        # Layered wing plates/feathers fan outward from shoulder blades.
        for i in range(6 + (2 if t>=4 else 0)):
            start=(side*.22,.18,1.50-i*.015)
            end=(side*(.62+i*.16),.22,1.55-i*.11)
            material=p["clothlight"] if feather and i%2 else p["primary"]
            segment(f"Wing.{label}.{i}",start,end,.055-i*.003,material,root,10)
            sphere(f"WingTip.{label}.{i}",end,(.10,.045,.17),material,root,12,8)
        if t>=3:
            ico(f"WingRune.{label}",(side*.48,.17,1.52),(.07,.04,.10),p["glow"],root)


def humanoid(spec,level,maximum,kind,p):
    root=empty("ROOT")
    hero=kind=="hero"; t=tier(level,maximum)
    heavy = spec.get("role")=="tank" or spec.get("silhouette") in ("broad_frontline","shield_wall","hammer_mass","armored_wedge","fortress_guard","ice_paladin")
    legs(root,p,1.0,heavy)
    torso(root,p,spec,t,hero)
    arms(root,p,spec.get("weapon"),spec.get("offhand"),heavy)
    female=spec.get("gender")=="female"
    face(root,p,female,beard=(hero and not female and t>=2),level=level)
    headgear(root,p,spec.get("helmet"),t)
    cape(root,p,spec.get("cape"),t)
    if spec.get("flying") or spec.get("archetype")=="winged_humanoid": wings(root,p,t,True)
    weapon(root,p,spec.get("weapon"),level,maximum)
    offhand(root,p,spec.get("offhand"),t)
    # Persistent unit motif, upgraded exactly each level.
    r=(level-1)/max(1,maximum-1)
    ico("IdentityRune",(0,-.276,1.32),(.045+.018*r,.025,.065+.020*r),p["glow"],root)
    scale=float(spec.get("scale",1.0))*(1+.025*r)
    root.scale=(scale,scale,scale)
    return root

# -----------------------------------------------------------------------------
# Creature / construct archetypes
# -----------------------------------------------------------------------------

def giant(spec,level,maximum,kind,p):
    root=empty("ROOT");t=tier(level,maximum)
    sphere("StoneTorso",(0,0,1.18),(.55,.38,.66),p["primary"],root)
    sphere("StoneHead",(0,-.04,1.92),(.34,.29,.32),p["secondary"],root)
    for side,label in ((-1,"L"),(1,"R")):
        segment(f"Arm.{label}",(side*.47,0,1.44),(side*.68,-.02,.72),.22,p["primary"],root,12)
        sphere(f"Fist.{label}",(side*.70,-.05,.58),(.27,.22,.25),p["secondary"],root)
        segment(f"Leg.{label}",(side*.25,0,.72),(side*.28,0,.22),.22,p["primary"],root,12)
        cube(f"Foot.{label}",(side*.29,-.07,.10),(.28,.30,.12),p["secondary"],root,bevel=.09)
    # Crystalline/rune growth by tier.
    for i in range(3+t*2):
        a=i*math.tau/(3+t*2)
        x=math.sin(a)*.46; y=.22; z=1.28+math.cos(a)*.32
        cone(f"RuneSpike.{i}",(x,y,z),.06,.0,.24+.025*t,p["glow"],root,rot=(.4*math.cos(a),.4*math.sin(a),0),vertices=7)
    if t>=4: torus("StoneAura",(0,0,.05),.70,.026,p["glow"],root)
    s=float(spec.get("scale",1.35))*(1+.02*(level-1)/maximum);root.scale=(s,s,s);return root


def construct(spec,level,maximum,kind,p):
    root=empty("ROOT");t=tier(level,maximum);hero=kind=="hero"
    cube("CoreBody",(0,0,1.12),(.46,.34,.52),p["darkmetal"],root,bevel=.12)
    ico("PowerCore",(0,-.35,1.15),(.16,.055,.16),p["glow"],root)
    cube("MachineHead",(0,-.02,1.79),(.28,.25,.25),p["metal"],root,bevel=.09)
    for side,label in ((-1,"L"),(1,"R")):
        sphere(f"Shoulder.{label}",(side*.56,0,1.42),(.22,.22,.22),p["metal"],root)
        segment(f"Arm.{label}",(side*.56,0,1.38),(side*.66,-.03,.74),.16,p["darkmetal"],root,12)
        cube(f"Fist.{label}",(side*.67,-.05,.58),(.20,.18,.20),p["metal"],root,bevel=.07)
        segment(f"Leg.{label}",(side*.22,0,.66),(side*.24,0,.22),.16,p["darkmetal"],root,12)
        cube(f"Foot.{label}",(side*.24,-.08,.10),(.22,.29,.11),p["metal"],root,bevel=.06)
    for i in range(2+t*2):
        a=i*math.tau/(2+t*2)
        cube(f"ArmorPlate.{i}",(math.sin(a)*.43,-.34,1.12+math.cos(a)*.31),(.09,.035,.11),p["accent"],root,rot=(0,0,a),bevel=.025)
    if hero or t>=3: hammer(root,p,spec.get("weapon","shock_hammer"),level,maximum)
    if t>=4: torus("CoreAura",(0,0,.05),.66,.028,p["glow"],root)
    s=float(spec.get("scale",1.3))*(1+.02*(level-1)/maximum);root.scale=(s,s,s);return root


def flying_beast(spec,level,maximum,kind,p):
    root=empty("ROOT");t=tier(level,maximum);ar=spec.get("archetype")
    # Upright chest + forward head reads clearly at RTS zoom while preserving dragon/bird silhouette.
    sphere("Body",(0,.03,1.12),(.38,.48,.52),p["primary"],root)
    sphere("Chest",(0,-.35,1.16),(.28,.18,.34),p["secondary"],root)
    segment("Neck",(0,-.18,1.48),(0,-.38,1.70),.18,p["primary"],root,12)
    sphere("Head",(0,-.46,1.82),(.26,.30,.24),p["primary"],root)
    cone("Snout",(0,-.73,1.80),.12,.03,.42,p["accent"],root,rot=(math.pi/2,0,0),vertices=10)
    for side,label in ((-1,"L"),(1,"R")):
        sphere(f"Eye.{label}",(side*.09,-.685,1.88),(.035,.025,.035),p["glow"],root,12,8)
        segment(f"Leg.{label}",(side*.16,0,.82),(side*.20,-.06,.42),.055,p["secondary"],root,10)
        for j in (-1,0,1):
            segment(f"Talon.{label}.{j}",(side*.20,-.06,.42),(side*.20+j*.055,-.18,.28),.016,p["accent"],root,7)
    wings(root,p,t,feather=(ar=="phoenix"))
    for i in range(4+t):
        x=(i-(3+t)/2)*.055
        segment(f"Tail.{i}",(x,.28,.92),(x*2,.68,.34-i*.025),.045,p["accent"] if ar=="phoenix" else p["primary"],root,8)
    if ar in ("drake","wyvern"):
        for i in range(4+t): cone(f"BackSpine.{i}",(0,.27,1.05+i*.11),.045,.0,.18,p["glow"],root,rot=(math.pi/2,0,0),vertices=7)
    if t>=4: torus("FlightAura",(0,0,.23),.68,.025,p["glow"],root)
    s=float(spec.get("scale",1.25))*(1+.02*(level-1)/maximum);root.scale=(s,s,s);return root


def build(spec,level,maximum,kind,p):
    ar=spec.get("archetype","humanoid")
    if ar=="giant": return giant(spec,level,maximum,kind,p)
    if ar=="construct": return construct(spec,level,maximum,kind,p)
    if ar in ("wyvern","drake","phoenix"): return flying_beast(spec,level,maximum,kind,p)
    return humanoid(spec,level,maximum,kind,p)

# -----------------------------------------------------------------------------
# Rendering / export
# -----------------------------------------------------------------------------

def bounds(root):
    pts=[]
    for o in bpy.context.scene.objects:
        if not o.get(TAG) or o.type!="MESH": continue
        for c in o.bound_box: pts.append(o.matrix_world @ Vector(c))
    if not pts: return Vector((-1,-1,0)),Vector((1,1,2))
    mn=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)))
    mx=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
    return mn,mx


def aim(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()


def stage(root,size):
    mn,mx=bounds(root);center=(mn+mx)*.5;height=max(.5,mx.z-mn.z);width=max(mx.x-mn.x,mx.y-mn.y)
    # Camera uses a consistent 3/4 mobile-game portrait angle.
    bpy.ops.object.camera_add(location=(4.3,-7.4,3.35));cam=bpy.context.object;aim(cam,(center.x,center.y,center.z+.02))
    cam.data.type='ORTHO';cam.data.ortho_scale=max(height*1.22,width*1.30,2.65)
    scene=bpy.context.scene;scene.camera=cam
    try: scene.render.engine='BLENDER_EEVEE_NEXT'
    except Exception: scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=size;scene.render.resolution_y=size;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
    scene.render.image_settings.color_mode='RGBA'
    scene.view_settings.look='AgX - Medium High Contrast' if 'AgX - Medium High Contrast' else scene.view_settings.look
    # warm key, cool fill, bright rim
    for name,loc,energy,sz in (
        ("Key",(4,-5,6),1050,4.0),
        ("Fill",(-4,-2.5,3),600,3.5),
        ("Rim",(1.5,4,5),1000,3.0),):
        bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.name=name;light.data.energy=energy;light.data.shape='DISK';light.data.size=sz;aim(light,center)
    scene.world.color=(.012,.016,.020)


def export_glb(path):
    bpy.ops.object.select_all(action='DESELECT'); selected=[]
    for o in bpy.context.scene.objects:
        if o.get(TAG): o.select_set(True);selected.append(o)
    if selected: bpy.context.view_layer.objects.active=selected[0]
    kw=dict(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
    try: bpy.ops.export_scene.gltf(**kw,export_lights=False,export_cameras=False)
    except TypeError: bpy.ops.export_scene.gltf(**kw)


def one(kind,uid,spec,level,maximum,out,save_blend,preview):
    clear();p=palette(spec,level,maximum);root=build(spec,level,maximum,kind,p)
    root.name=f"{kind}_{uid}_L{level:02d}";root["emberfall_kind"]=kind;root["emberfall_id"]=uid;root["emberfall_level"]=level;root["emberfall_name"]=spec["name"]
    stage(root,preview)
    folder=out/("troops" if kind=="troop" else "heroes")/uid/f"level-{level:02d}";folder.mkdir(parents=True,exist_ok=True)
    glb=folder/f"{uid}-level-{level:02d}.glb";png=folder/f"{uid}-level-{level:02d}.png"
    export_glb(glb);bpy.context.scene.render.filepath=str(png);bpy.ops.render.render(write_still=True)
    blend=None
    if save_blend:
        blend=folder/f"{uid}-level-{level:02d}.blend";bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    meta={"generator":"v2","kind":kind,"id":uid,"name":spec["name"],"level":level,"max_level":maximum,
          "archetype":spec.get("archetype"),"weapon":spec.get("weapon"),"silhouette":spec.get("silhouette"),"motif":spec.get("motif"),
          "glb":glb.name,"preview":png.name,"blend":blend.name if blend else None}
    (folder/"metadata.json").write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return meta


def manifest(out,items):
    path=out/'manifest.json';data={"generator":"tools/blender/generate_character_v2.py","assets":[]}
    if path.exists():
        try:data=json.loads(path.read_text(encoding='utf-8'))
        except Exception:pass
    index={(x['kind'],x['id'],x['level']):x for x in data.get('assets',[])}
    for x in items:index[(x['kind'],x['id'],x['level'])]=x
    data['generator']='tools/blender/generate_character_v2.py';data['assets']=sorted(index.values(),key=lambda x:(x['kind'],x['id'],x['level']))
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2),encoding='utf-8')


def main():
    a=args();specs=json.loads(SPECS.read_text(encoding='utf-8'));out=Path(a.output).resolve();work=[]
    if a.all or a.all_troops: work += [("troop",k,v) for k,v in specs['troops'].items()]
    if a.all or a.all_heroes: work += [("hero",k,v) for k,v in specs['heroes'].items()]
    if not work:
        group=specs['troops' if a.kind=='troop' else 'heroes']
        if a.unit not in group: raise SystemExit(f"Unknown {a.kind} {a.unit}; choose from: {', '.join(group)}")
        work=[(a.kind,a.unit,group[a.unit])]
    items=[]
    for kind,uid,spec in work:
        maximum=specs['troop_max_level'] if kind=='troop' else specs['hero_max_level']
        for lvl in level_list(a.levels,maximum):
            print(f"[Emberfall v2] {kind} {uid} L{lvl}/{maximum}",flush=True)
            items.append(one(kind,uid,spec,lvl,maximum,out,a.save_blend,a.preview_size))
    manifest(out,items);print(f"Generated {len(items)} level assets -> {out}",flush=True)

if __name__=='__main__': main()
