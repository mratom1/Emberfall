#!/usr/bin/env python3
"""Detailed original Army generator for Emberfall Kingdoms.

Creates each of the 22 Army classes as a distinct stylized mobile-strategy model.
Troops have exact Level 1..15 output. Every level adds a visible progression element
or upgrades an existing element, while preserving the class silhouette.

Outputs per level: GLB, transparent PNG, metadata JSON, optional BLEND.
Designed for headless GitHub Actions Blender.
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
SPECS_PATH = ROOT / "art" / "blender" / "unit_specs.json"
TAG = "emberfall_army_export"
MAX_LEVEL = 15

# ---------- CLI ----------
def cli():
    raw = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--unit", default="guardian")
    p.add_argument("--levels", default="1-15")
    p.add_argument("--all-troops", action="store_true")
    p.add_argument("--output", default=str(ROOT / "generated" / "army-v3"))
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
        raise SystemExit("No valid Army levels. Valid range: 1-15")
    return levels

# ---------- materials ----------
def hexrgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def hsv_shift(c, v=0, s=0):
    h, sat, val = colorsys.rgb_to_hsv(*c)
    return colorsys.hsv_to_rgb(h, max(0, min(1, sat+s)), max(0, min(1, val+v)))


def material(name, color, metallic=0, rough=.48, emission=None, strength=0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Metallic"].default_value = metallic
    bs.inputs["Roughness"].default_value = rough
    if emission:
        sock = bs.inputs.get("Emission Color") or bs.inputs.get("Emission")
        if sock:
            sock.default_value = (*emission, 1)
        if bs.inputs.get("Emission Strength"):
            bs.inputs["Emission Strength"].default_value = strength
    return m


def palette(spec, level):
    r = (level-1)/14
    primary = hsv_shift(hexrgb(spec["primary"]), v=-.08+.04*r, s=.10)
    secondary = hsv_shift(hexrgb(spec["secondary"]), v=-.06+.035*r, s=.05)
    accent = hsv_shift(hexrgb(spec["accent"]), v=.02+.07*r, s=.05)
    glow = hsv_shift(accent, v=.20, s=.12)
    female = spec.get("gender") == "female"
    skin = (.72,.48,.34) if not female else (.78,.55,.41)
    return {
        "primary": material("PrimaryCloth",primary,0,.58),
        "primary_dark": material("PrimaryDark",hsv_shift(primary,-.12),0,.62),
        "secondary": material("Secondary",secondary,0,.57),
        "accent": material("Accent",accent,.62,.25),
        "steel": material("Steel",(.31+.08*r,.36+.08*r,.39+.08*r),.86,.20),
        "darksteel": material("DarkSteel",(.10,.13,.15),.82,.24),
        "gold": material("WarmMetal",accent,.80,.21),
        "leather": material("Leather",(.16,.065,.028),0,.70),
        "wood": material("Wood",(.22,.09,.025),0,.70),
        "skin": material("Skin",skin,0,.50),
        "hair": material("Hair",(.055,.025,.012),0,.68),
        "fur": material("Fur",(.22,.19,.16),0,.83),
        "white": material("EyeWhite",(.78,.82,.80),0,.25),
        "iris": material("Iris",(.025,.09,.08),0,.18),
        "black": material("Black",(.010,.012,.014),0,.38),
        "glow": material("Magic",glow,.12,.15,glow,.7+1.4*r),
        "ice": material("Ice",(.30,.72,.84),.18,.16,(.34,.82,1.0),1.0+1.2*r),
        "fire": material("Fire",(.95,.29,.06),.05,.17,(1.0,.18,.02),1.3+1.3*r),
    }

# ---------- object utilities ----------
def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for blocks in (bpy.data.meshes,bpy.data.curves,bpy.data.materials,bpy.data.cameras,bpy.data.lights):
        for b in list(blocks):
            if b.users == 0:
                blocks.remove(b)


def root_empty(name="ROOT"):
    o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o[TAG]=True;return o


def finish(o,name,matl,root,smooth=True,bevel=0):
    o.name=name;o.parent=root;o[TAG]=True
    if o.type=="MESH":
        o.data.materials.append(matl)
        if smooth:
            for poly in o.data.polygons: poly.use_smooth=True
        if bevel:
            mod=o.modifiers.new("EdgeBevel","BEVEL");mod.width=bevel;mod.segments=2
    return o


def apply_scale(o):
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.select_set(False)


def sphere(name,loc,scale,matl,root,segments=20,rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc)
    o=bpy.context.object;o.scale=scale;apply_scale(o);return finish(o,name,matl,root,True,.012)


def ico(name,loc,scale,matl,root,sub=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,location=loc)
    o=bpy.context.object;o.scale=scale;apply_scale(o);return finish(o,name,matl,root,True,.01)


def cube(name,loc,scale,matl,root,rot=(0,0,0),bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc,rotation=rot)
    o=bpy.context.object;o.scale=scale;apply_scale(o);return finish(o,name,matl,root,False,bevel)


def cylinder(name,loc,radius,depth,matl,root,rot=(0,0,0),vertices=14,bevel=.015):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc,rotation=rot)
    return finish(bpy.context.object,name,matl,root,True,bevel)


def cone(name,loc,r1,r2,depth,matl,root,rot=(0,0,0),vertices=12):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=r1,radius2=r2,depth=depth,location=loc,rotation=rot)
    return finish(bpy.context.object,name,matl,root,False,.018)


def torus(name,loc,major,minor,matl,root,rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=24,minor_segments=8,location=loc,rotation=rot)
    return finish(bpy.context.object,name,matl,root,True,.006)


def rod(name,a,b,radius,matl,root,vertices=12):
    a,b=Vector(a),Vector(b);v=b-a;mid=(a+b)*.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=v.length,location=mid)
    o=bpy.context.object;o.rotation_mode="QUATERNION";o.rotation_quaternion=Vector((0,0,1)).rotation_difference(v.normalized())
    return finish(o,name,matl,root,True,.012)


def beam(name,a,b,width,thickness,matl,root,bevel=.015):
    """Rectangular blade/plate between points, local Z aligned to the vector."""
    a,b=Vector(a),Vector(b);v=b-a;mid=(a+b)*.5
    bpy.ops.mesh.primitive_cube_add(size=1,location=mid)
    o=bpy.context.object;o.scale=(width,thickness,v.length/2);apply_scale(o)
    o.rotation_mode="QUATERNION";o.rotation_quaternion=Vector((0,0,1)).rotation_difference(v.normalized())
    return finish(o,name,matl,root,False,bevel)

# ---------- face / clothing ----------
def add_face(root,p,spec,helmet=False,masked=False):
    female=spec.get("gender")=="female";z=1.93
    sphere("Head",(0,-.02,z),(.205 if female else .215,.185,.235),p["skin"],root)
    sphere("Ear.L",(-.205,-.005,z),(.035,.025,.050),p["skin"],root,14,8)
    sphere("Ear.R",(.205,-.005,z),(.035,.025,.050),p["skin"],root,14,8)
    # readable eyes with brows
    for side,label in ((-1,"L"),(1,"R")):
        sphere(f"Eye.{label}",(side*.073,-.190,z+.045),(.038,.016,.028),p["white"],root,14,8)
        sphere(f"Iris.{label}",(side*.073,-.205,z+.045),(.016,.008,.018),p["iris"],root,12,7)
        beam(f"Brow.{label}",(side*.12,-.211,z+.105),(side*.03,-.211,z+.10),.010,.008,p["hair"],root,.004)
    cone("Nose",(0,-.220,z-.005),.032,.012,.095,p["skin"],root,rot=(math.pi/2,0,0),vertices=8)
    if not masked: beam("Mouth",(-.045,-.210,z-.095),(.045,-.210,z-.095),.008,.006,p["black"],root,.003)
    # side/back hair, not a giant cap over the forehead
    sphere("HairBack",(0,.075,z+.08),(.215,.145,.19),p["hair"],root,18,10)
    for i,x in enumerate((-.14,-.07,0,.07,.14)):
        cone(f"HairLock.{i}",(x,-.105,z+.235),.045,.010,.16,p["hair"],root,rot=(0.07,0,(i-2)*.06),vertices=7)


def torso(root,p,spec,level,robe=False,heavy=False):
    # tapered clothed torso rather than a skin-looking sphere
    cone("Tunic",(0,0,1.30),.31,.39,.70,p["primary"],root,vertices=10)
    cube("TunicFront",(0,-.245,1.28),(.29,.025,.29),p["primary_dark"],root,bevel=.035)
    cube("Belt",(0,-.01,.96),(.34,.205,.045),p["leather"],root,bevel=.02)
    cube("BeltBuckle",(0,-.222,.96),(.055,.018,.055),p["accent"],root,bevel=.012)
    # modest hip skirt/panels make the model read as clothed at RTS zoom
    cone("WaistGuard",(0,0,.87),.31,.28,.22,p["secondary"],root,vertices=10)
    if robe:
        cone("Robe",(0,.01,.64),.38,.27,.72,p["primary_dark"],root,vertices=12)
        cube("RobeFront",(0,-.25,.63),(.20,.022,.32),p["primary"],root,bevel=.025)
    # every level 2+ adds visible trim/rank mark
    if level>=2:
        cube("RankTrim",(0,-.274,1.48),(.25,.015,.022),p["accent"],root,bevel=.008)
    if level>=3:
        ico("BeltRune",(0,-.242,.96),(.045,.020,.055),p["glow"],root)
    # armor ladder
    if level>=4:
        cone("Cuirass",(0,-.035,1.31),.315,.36,.53,p["steel"],root,vertices=10)
        cube("CuirassFront",(0,-.260,1.33),(.285,.035,.235),p["steel"],root,bevel=.045)
    if level>=5:
        for side,label in ((-1,"L"),(1,"R")):
            sphere(f"Pauldron.{label}",(side*(.41 if not heavy else .45),-.01,1.51),(.16 if not heavy else .19,.17,.13),p["steel"],root,16,10)
    if level>=6:
        cube("ChestBand",(0,-.302,1.34),(.24,.018,.040),p["accent"],root,bevel=.010)
    if level>=7:
        for side,label in ((-1,"L"),(1,"R")):
            cube(f"Greave.{label}",(side*.19,-.055,.39),(.105,.085,.20),p["steel"],root,bevel=.035)
    if level>=8:
        for side,label in ((-1,"L"),(1,"R")):
            cube(f"Bracer.{label}",(side*.50,-.03,1.06),(.075,.082,.16),p["darksteel"],root,bevel=.028)
    if level>=9:
        ico("ChestGem",(0,-.315,1.36),(.065,.026,.082),p["glow"],root)
    if level>=10:
        for side,label in ((-1,"L"),(1,"R")):
            cube(f"ShoulderTrim.{label}",(side*(.41 if not heavy else .45),-.165,1.51),(.11,.018,.040),p["accent"],root,bevel=.01)
    if level>=11:
        torus("WaistRune",(0,-.02,.88),.35,.016,p["glow"],root,rot=(math.pi/2,0,0))
    if level>=12:
        for side,label in ((-1,"L"),(1,"R")):
            cone(f"EliteSpike.{label}",(side*.51,-.005,1.60),.048,.0,.20,p["accent"],root,rot=(0,side*.56,0),vertices=7)
    if level>=13:
        cube("EliteChestTrim",(0,-.325,1.18),(.235,.015,.022),p["gold"],root,bevel=.008)
    if level>=14:
        for side,label in ((-1,"L"),(1,"R")):
            ico(f"ShoulderRune.{label}",(side*.41,-.178,1.53),(.040,.018,.048),p["glow"],root)
    if level>=15:
        torus("MasteryAura",(0,0,.055),.60,.022,p["glow"],root)


def body(root,p,spec,level,robe=False,heavy=False):
    torso(root,p,spec,level,robe,heavy)
    # pants + boots
    for side,label in ((-1,"L"),(1,"R")):
        hip=(side*.17,0,.88); knee=(side*(.19 if not heavy else .22),-.01,.53);ankle=(side*(.19 if not heavy else .22),-.015,.20)
        rod(f"Thigh.{label}",hip,knee,.105 if not heavy else .12,p["secondary"],root)
        rod(f"Shin.{label}",knee,ankle,.09 if not heavy else .105,p["primary_dark"],root)
        cube(f"Boot.{label}",(ankle[0],-.075,.105),(.13 if not heavy else .15,.19,.105),p["leather"],root,bevel=.045)
    # arms: cloth sleeves plus exposed/gloved hands only
    shoulder_x=.39 if not heavy else .44
    for side,label in ((-1,"L"),(1,"R")):
        shoulder=(side*shoulder_x,0,1.47)
        elbow=(side*.50,-.02,1.17)
        hand=(side*.52,-.055,.90) if side>0 else (side*.47,-.23,1.07)
        rod(f"Sleeve.{label}",shoulder,elbow,.09 if not heavy else .105,p["primary_dark"],root)
        rod(f"Forearm.{label}",elbow,hand,.072,p["skin"],root)
        sphere(f"Hand.{label}",hand,(.078,.068,.080),p["skin"],root,16,9)

# ---------- gear ----------
def headgear(root,p,spec,level):
    k=(spec.get("helmet") or "").lower();z=1.93
    masked="mask" in k or "veil" in k
    add_face(root,p,spec,helmet=bool(k),masked=masked)
    if "bandana" in k:
        torus("Bandana",(0,0,z+.08),.205,.025,p["primary"],root,rot=(math.pi/2,0,0));return
    if "hood" in k or "veil" in k:
        # open-front hood: rear sphere + forehead strip, face remains readable
        sphere("HoodBack",(0,.08,z+.07),(.235,.17,.245),p["secondary"],root,18,10)
        cube("HoodBrow",(0,-.185,z+.16),(.20,.025,.065),p["secondary"],root,bevel=.035)
        if masked: cube("Mask",(0,-.213,z-.055),(.15,.018,.070),p["darksteel"],root,bevel=.02)
        if level>=12: ico("HoodRune",(0,-.213,z+.17),(.045,.018,.055),p["glow"],root)
        return
    if "goggles" in k:
        for side,label in ((-1,"L"),(1,"R")):
            torus(f"Goggle.{label}",(side*.082,-.210,z+.045),.052,.012,p["accent"],root,rot=(math.pi/2,0,0))
            sphere(f"Lens.{label}",(side*.082,-.223,z+.045),(.033,.010,.033),p["glow"],root,12,7)
        if level>=6: cube("LeatherCap",(0,.05,z+.16),(.19,.15,.07),p["leather"],root,bevel=.04)
        return
    if "circlet" in k:
        torus("Circlet",(0,0,z+.11),.205,.018,p["accent"],root,rot=(math.pi/2,0,0))
        if "crystal" in k: ico("CircletCrystal",(0,-.205,z+.12),(.055,.018,.075),p["ice"],root)
        return
    if "tricorn" in k or "hat" in k:
        cylinder("HatBrim",(0,0,z+.21),.29,.035,p["primary_dark"],root,vertices=24)
        cone("HatCrown",(0,0,z+.34),.19,.13,.27,p["primary"],root,vertices=14)
        cone("Feather",(.18,-.02,z+.49),.035,.006,.42,p["accent"],root,rot=(0,-.35,-.38),vertices=7);return
    if "fur" in k:
        sphere("FurCap",(0,.03,z+.13),(.23,.18,.15),p["fur"],root,16,10)
        for side,label in ((-1,"L"),(1,"R")):
            cone(f"Horn.{label}",(side*.21,.02,z+.22),.055,.005,.27,p["accent"],root,rot=(0,side*.60,0),vertices=7);return
    if "sun" in k or "winged" in k:
        sphere("HelmShell",(0,.05,z+.10),(.22,.17,.18),p["steel"],root,18,10)
        cone("SunCrest",(0,.04,z+.39),.060,.008,.36,p["accent"],root,vertices=8)
        for side,label in ((-1,"L"),(1,"R")):
            cone(f"HelmWing.{label}",(side*.23,.03,z+.18),.045,.005,.28,p["accent"],root,rot=(0,side*.65,0),vertices=7);return
    # helmets appear at higher levels even for open/basic helmet classes
    if k and (level>=4 or "closed" in k or "heavy" in k):
        sphere("HelmShell",(0,.05,z+.10),(.225,.18,.19),p["steel"],root,18,10)
        cube("BrowPlate",(0,-.185,z+.12),(.18,.025,.045),p["darksteel"],root,bevel=.018)
        if level>=12 or "heavy" in k:
            cone("HelmetCrest",(0,.03,z+.39),.055,.008,.34,p["accent"],root,vertices=8)


def cape(root,p,spec,level):
    k=(spec.get("cape") or "none").lower()
    if k=="none": return
    if k=="fur":
        for side in (-1,0,1): sphere(f"FurMantle.{side}",(side*.21,.18,1.47),(.23,.09,.13),p["fur"],root,14,8)
        return
    long=any(x in k for x in ("long","coat","cloak"));length=.82 if long else .55
    cube("Cape",(0,.22,1.18 if long else 1.30),(.36,.032,length/2),p["secondary"],root,rot=(-.07,0,0),bevel=.04)
    if "split" in k or "coat" in k:
        cube("CapeTail.L",(-.15,.23,.86),(.14,.026,.34),p["primary_dark"],root,rot=(-.10,0,-.05),bevel=.028)
        cube("CapeTail.R",(.15,.23,.86),(.14,.026,.34),p["primary_dark"],root,rot=(-.10,0,.05),bevel=.028)
    if level>=10: cube("CapeTrim",(0,.183,.79 if long else 1.03),(.36,.012,.028),p["accent"],root,bevel=.008)


def sword(root,p,level,curved=False):
    hand=Vector((.52,-.055,.90));base=hand+Vector((.02,0,-.03));tip=Vector((.80,-.08,1.92+.018*level))
    rod("SwordGrip",base,base+Vector((.07,0,.25)),.040,p["leather"],root,10)
    beam("SwordBlade",base+Vector((.06,0,.22)),tip,.070 if level<8 else .082,.025,p["steel"],root,.018)
    beam("SwordGuard",(.42,-.07,1.11),(.72,-.07,1.11),.030,.030,p["accent"],root,.012)
    cone("SwordTip",(tip.x+.025,tip.y,tip.z+.10),.075,0,.20,p["steel"],root,rot=(0,.25,0),vertices=8)
    if level>=8: ico("SwordRune",(.69,-.10,1.62),(.04,.018,.060),p["glow"],root)
    if level>=14: rod("SwordGlowLine",(.67,-.105,1.48),(.77,-.105,1.82),.012,p["glow"],root,8)


def shield(root,p,level,tower=False,buckler=False):
    x=-.47;z=1.08
    if tower:
        cube("TowerShield",(x,-.33,z),(.31,.055,.52),p["steel"],root,bevel=.09)
    else:
        cylinder("Shield",(x,-.33,z),.23 if buckler else .31,.075,p["steel"],root,rot=(math.pi/2,0,0),vertices=28,bevel=.025)
    ico("ShieldBoss",(x,-.382,z),(.075,.025,.075),p["accent"],root)
    if level>=6: torus("ShieldRing",(x,-.388,z),.16 if buckler else .22,.015,p["accent"],root,rot=(math.pi/2,0,0))
    if level>=12: ico("ShieldRune",(x,-.405,z),(.045,.018,.055),p["glow"],root)


def bow(root,p,level):
    x=.57;z=1.25
    rod("BowUpper",(x,-.10,z),(x+.15,-.10,z+.62),.028,p["wood"],root,10)
    rod("BowLower",(x,-.10,z),(x+.15,-.10,z-.62),.028,p["wood"],root,10)
    rod("BowString",(x+.15,-.115,z+.62),(x+.15,-.115,z-.62),.006,p["glow"] if level>=10 else p["accent"],root,7)
    cube("BowGrip",(x,-.10,z),(.04,.032,.13),p["leather"],root,bevel=.012)
    if level>=8: ico("BowRune",(x+.15,-.13,z+.62),(.035,.015,.045),p["glow"],root)


def spear(root,p,level):
    bottom=(.66,-.02,.20);top=(.46,-.04,2.22+.015*level)
    rod("SpearShaft",bottom,top,.036,p["wood"],root,10)
    cone("SpearHead",(.445,-.04,top[2]+.17),.095,0,.34,p["steel"],root,rot=(0,-.06,0),vertices=8)
    if level>=7: torus("SpearRing",(.47,-.04,1.90),.080,.012,p["accent"],root,rot=(math.pi/2,0,0))
    if level>=13: ico("SpearRune",(.46,-.06,2.05),(.035,.015,.050),p["glow"],root)


def axe(root,p,level,side=1):
    x=.52*side;bottom=(x,-.04,.84);top=(x+.10*side,-.04,1.85+.012*level)
    rod(f"AxeHandle.{side}",bottom,top,.042,p["wood"],root,10)
    cube(f"AxeHead.{side}",(top[0]+.11*side,-.04,top[2]),(.17,.06,.14),p["steel"],root,bevel=.03)
    cone(f"AxeEdge.{side}",(top[0]+.27*side,-.04,top[2]),.14,.018,.28,p["steel"],root,rot=(0,math.pi/2,0),vertices=8)
    if level>=12: ico(f"AxeRune.{side}",(top[0]+.10*side,-.09,top[2]),(.035,.018,.045),p["glow"],root)


def hammer(root,p,level):
    bottom=(.54,-.04,.80);top=(.63,-.04,1.88+.012*level)
    rod("HammerHandle",bottom,top,.052,p["wood"],root,10)
    cube("HammerHead",(top[0],-.04,top[2]),(.30,.13,.17),p["darksteel"],root,bevel=.055)
    cube("HammerCap.L",(top[0]-.30,-.04,top[2]),(.09,.16,.20),p["steel"],root,bevel=.035)
    cube("HammerCap.R",(top[0]+.30,-.04,top[2]),(.09,.16,.20),p["steel"],root,bevel=.035)
    if level>=7: ico("HammerRune",(top[0],-.18,top[2]),(.070,.025,.070),p["glow"],root)


def staff(root,p,level,element="magic"):
    bottom=(.60,-.02,.12);top=(.48,-.03,2.15+.012*level)
    rod("Staff",bottom,top,.037,p["wood"],root,10)
    em=p["ice"] if element=="ice" else p["fire"] if element=="fire" else p["glow"]
    ico("StaffFocus",(top[0],top[1],top[2]+.13),(.14,.095,.14),em,root)
    torus("FocusRing",(top[0],top[1],top[2]+.13),.19,.013,p["accent"],root,rot=(math.pi/2,0,0))
    if level>=10: torus("FocusRing2",(top[0],top[1],top[2]+.13),.235,.010,em,root,rot=(math.pi/2,.45,0))


def rifle(root,p,level):
    beam("RifleStock",(.44,-.10,.94),(.70,-.12,1.28),.075,.065,p["wood"],root,.025)
    rod("RifleBarrel",(.62,-.13,1.19),(.92,-.13,1.72+.012*level),.035,p["steel"],root,12)
    cube("RifleReceiver",(.64,-.14,1.25),(.09,.055,.12),p["accent"],root,bevel=.022)
    if level>=8: torus("RifleSight",(.83,-.15,1.53),.050,.010,p["glow"],root,rot=(math.pi/2,0,0))


def daggers(root,p,level):
    for side,label in ((-1,"L"),(1,"R")):
        hand=(side*.48,-.20 if side<0 else -.06,1.00)
        tip=(side*.70,-.24 if side<0 else -.09,1.38)
        beam(f"Dagger.{label}",hand,tip,.045,.020,p["steel"],root,.012)
        cube(f"DaggerGuard.{label}",(side*.51,hand[1],1.08),(.09,.025,.025),p["accent"],root,bevel=.008)
        if level>=12: ico(f"DaggerRune.{label}",(side*.62,tip[1]-.02,1.27),(.030,.012,.040),p["glow"],root)


def bomb_gear(root,p,level):
    sphere("Bomb",(.58,-.10,1.05),(.18,.16,.18),p["darksteel"],root,18,10)
    rod("Fuse",(.58,-.10,1.22),(.66,-.10,1.39),.018,p["fire"],root,7)
    cube("BombPack",(0,.22,1.22),(.25,.14,.31),p["leather"],root,bevel=.05)
    for i in range(2+(1 if level>=8 else 0)):
        sphere(f"PackBomb.{i}",(-.10+i*.11,.35,1.18),(.075,.065,.075),p["darksteel"],root,12,8)


def orb_weapon(root,p,level):
    ico("StormOrb",(.60,-.12,1.12),(.15,.09,.15),p["glow"],root)
    torus("OrbRing",(.60,-.12,1.12),.23,.014,p["accent"],root,rot=(math.pi/2,0,0))
    if level>=10: torus("OrbRing2",(.60,-.12,1.12),.29,.010,p["glow"],root,rot=(math.pi/2,.6,0))


def quiver(root,p,level):
    cube("Quiver",(-.18,.24,1.29),(.11,.10,.30),p["leather"],root,rot=(0,0,-.15),bevel=.035)
    for i in range(4+(1 if level>=10 else 0)):
        rod(f"Arrow.{i}",(-.27+i*.045,.28,1.42),(-.27+i*.045,.28,1.84),.010,p["accent"],root,7)


def satchel(root,p,name="Satchel"):
    cube(name,(-.23,.22,1.03),(.17,.11,.21),p["leather"],root,bevel=.045)
    cube(name+"Clasp",(-.23,.095,1.06),(.040,.012,.035),p["accent"],root,bevel=.008)


def wings(root,p,level,crystal=False):
    for side,label in ((-1,"L"),(1,"R")):
        count=6+(1 if level>=10 else 0)+(1 if level>=15 else 0)
        for i in range(count):
            start=(side*.20,.18,1.48-i*.01);end=(side*(.55+i*.13),.25,1.55-i*.10)
            matl=p["ice"] if crystal else (p["accent"] if i%2 else p["primary"])
            rod(f"Wing.{label}.{i}",start,end,.045 if i<4 else .035,matl,root,9)
            cone(f"Feather.{label}.{i}",(end[0],end[1],end[2]-.08),.070,.010,.28,matl,root,rot=(0,side*.28,0),vertices=7)
        if level>=12: ico(f"WingRune.{label}",(side*.50,.16,1.50),(.055,.025,.075),p["glow"],root)


def special_accessories(root,p,spec,level):
    uid=spec.get("_id","")
    if uid=="berserker":
        for side in (-1,0,1): sphere(f"FurShoulder.{side}",(side*.20,.12,1.49),(.18,.10,.11),p["fur"],root,14,8)
    elif uid=="healer":
        torus("MedicHalo",(0,.03,2.20),.19,.014,p["glow"],root)
        satchel(root,p,"MedicSatchel")
    elif uid=="musketeer":
        cube("CoatTail.L",(-.14,.19,.77),(.13,.025,.30),p["primary_dark"],root,rot=(-.10,0,-.04),bevel=.025)
        cube("CoatTail.R",(.14,.19,.77),(.13,.025,.30),p["primary_dark"],root,rot=(-.10,0,.04),bevel=.025)
    elif uid=="sentinel":
        rod("BannerPole",(-.30,.22,.72),(-.30,.22,2.28),.025,p["wood"],root,8)
        cube("BackBanner",(-.30,.20,1.95),(.22,.025,.24),p["primary"],root,bevel=.015)
    elif uid=="frostweaver":
        for side in (-1,1): cone(f"IceShard.{side}",(side*.35,.15,1.56),.050,.006,.26,p["ice"],root,rot=(0,side*.30,0),vertices=7)
    elif uid=="stormcaller":
        for side in (-1,1):
            ico(f"StormSatellite.{side}",(side*.36,.12,1.63),(.060,.045,.060),p["glow"],root)
    elif uid=="duelist":
        cone("HatFeather",(.18,.02,2.42),.030,.005,.40,p["accent"],root,rot=(0,-.32,-.35),vertices=7)

# ---------- humanoid troop ----------
def build_humanoid(uid,spec,level,p):
    spec=dict(spec);spec["_id"]=uid
    root=root_empty()
    caster=uid in {"mage","healer","frostweaver","stormcaller"}
    heavy=uid in {"guardian","breaker","sentinel","hammerguard"}
    body(root,p,spec,level,robe=caster,heavy=heavy)
    headgear(root,p,spec,level)
    cape(root,p,spec,level)
    w=spec.get("weapon","").lower();off=spec.get("offhand","").lower()
    if "bow" in w:
        bow(root,p,level);quiver(root,p,level)
    elif "spear" in w or "lance" in w:
        spear(root,p,level)
    elif "axe" in w:
        axe(root,p,level,1)
        if "twin" in w: axe(root,p,level,-1)
    elif "hammer" in w:
        hammer(root,p,level)
    elif "staff" in w:
        element="ice" if "ice" in w else "fire" if uid=="mage" else "magic"
        staff(root,p,level,element)
    elif "rifle" in w:
        rifle(root,p,level)
    elif "dagger" in w:
        daggers(root,p,level)
    elif "bomb" in w:
        bomb_gear(root,p,level)
    elif "orb" in w:
        orb_weapon(root,p,level)
    else:
        sword(root,p,level,curved=("saber" in w))
    if "shield" in off or "buckler" in off:
        shield(root,p,level,tower=("tower" in off),buckler=("buckler" in off))
    elif "satchel" in off and uid!="healer": satchel(root,p)
    elif "bomb_pack" in off and "bomb" not in w: bomb_gear(root,p,level)
    special_accessories(root,p,spec,level)
    # identity rune and role color remain visible at all levels
    ico("ClassRune",(0,-.305,1.34),(.042+.002*level,.018,.052+.002*level),p["glow"],root)
    scale=float(spec.get("scale",1.0))*(1+.018*(level-1)/14)
    root.scale=(scale,scale,scale)
    return root

# ---------- creatures ----------
def build_giant(uid,spec,level,p):
    root=root_empty();r=(level-1)/14
    sphere("Torso",(0,0,1.13),(.52,.39,.64),p["primary"],root,18,10)
    sphere("Head",(0,-.05,1.85),(.32,.29,.31),p["secondary"],root,16,10)
    for side,label in ((-1,"L"),(1,"R")):
        rod(f"Arm.{label}",(side*.46,0,1.42),(side*.69,-.03,.69),.20,p["primary"],root,12)
        sphere(f"Fist.{label}",(side*.71,-.06,.54),(.25,.22,.24),p["secondary"],root,16,10)
        rod(f"Leg.{label}",(side*.24,0,.68),(side*.28,0,.20),.20,p["primary_dark"],root,12)
        cube(f"Foot.{label}",(side*.28,-.09,.09),(.27,.27,.11),p["secondary"],root,bevel=.08)
    # Every level grows a new stone/rune feature.
    for i in range(2+level):
        a=i*math.tau/(2+level)
        x=math.sin(a)*.44;z=1.25+math.cos(a)*.32
        matl=p["glow"] if i>=6 else p["accent"]
        cone(f"StoneGrowth.{i}",(x,.28,z),.045+.0015*level,.005,.17+.008*level,matl,root,rot=(math.pi/2,0,-a),vertices=7)
    if level>=8: torus("GiantRune",(0,-.39,1.16),.26,.018,p["glow"],root,rot=(math.pi/2,0,0))
    if level>=15: torus("GiantAura",(0,0,.055),.70,.025,p["glow"],root)
    s=float(spec.get("scale",1.38))*(1+.025*r);root.scale=(s,s,s);return root


def build_construct(uid,spec,level,p):
    root=root_empty();r=(level-1)/14
    cube("CoreBody",(0,0,1.10),(.44,.34,.50),p["darksteel"],root,bevel=.11)
    ico("ForgeCore",(0,-.35,1.12),(.15,.050,.15),p["glow"],root)
    cube("Head",(0,-.02,1.73),(.27,.24,.23),p["steel"],root,bevel=.08)
    for side,label in ((-1,"L"),(1,"R")):
        sphere(f"Shoulder.{label}",(side*.54,0,1.40),(.21,.20,.20),p["steel"],root,16,10)
        rod(f"Arm.{label}",(side*.54,0,1.32),(side*.66,-.02,.68),.15,p["darksteel"],root,12)
        cube(f"Fist.{label}",(side*.67,-.05,.53),(.19,.17,.19),p["steel"],root,bevel=.06)
        rod(f"Leg.{label}",(side*.22,0,.64),(side*.24,0,.20),.15,p["darksteel"],root,12)
        cube(f"Foot.{label}",(side*.24,-.08,.09),(.22,.27,.10),p["steel"],root,bevel=.055)
    for i in range(1+level):
        a=i*math.tau/(1+level)
        cube(f"ArmorPlate.{i}",(math.sin(a)*.39,-.35,1.11+math.cos(a)*.29),(.065,.025,.085),p["accent"] if i<8 else p["glow"],root,rot=(0,0,a),bevel=.018)
    if level>=7: hammer(root,p,level)
    if level>=15: torus("OverdriveAura",(0,0,.055),.66,.025,p["glow"],root)
    s=float(spec.get("scale",1.32))*(1+.025*r);root.scale=(s,s,s);return root


def build_flying(uid,spec,level,p):
    root=root_empty();r=(level-1)/14;phoenix=uid=="phoenix";crystal=uid=="drake"
    sphere("Body",(0,.03,1.10),(.36,.44,.48),p["primary"],root,18,10)
    sphere("Chest",(0,-.34,1.14),(.26,.16,.31),p["secondary"],root,16,10)
    rod("Neck",(0,-.16,1.45),(0,-.36,1.66),.16,p["primary"],root,12)
    sphere("Head",(0,-.43,1.79),(.24,.27,.22),p["primary"],root,16,10)
    cone("Snout",(0,-.69,1.77),.11,.025,.38,p["accent"],root,rot=(math.pi/2,0,0),vertices=9)
    for side,label in ((-1,"L"),(1,"R")):
        sphere(f"Eye.{label}",(side*.085,-.645,1.84),(.030,.020,.030),p["glow"],root,12,7)
        rod(f"Leg.{label}",(side*.15,0,.80),(side*.19,-.05,.40),.050,p["secondary"],root,9)
        for j in (-1,0,1): rod(f"Talon.{label}.{j}",(side*.19,-.05,.40),(side*.19+j*.05,-.18,.27),.014,p["accent"],root,7)
    wings(root,p,level,crystal=crystal)
    # level-by-level back spines or flame plumes
    for i in range(2+level):
        z=.72+i*(.95/(2+level));matl=p["fire"] if phoenix else p["ice"] if crystal else p["glow"]
        cone(f"BackFeature.{i}",(0,.28,z+.60),.035+.001*level,.004,.14+.005*level,matl,root,rot=(math.pi/2,0,0),vertices=7)
    if level>=8: torus("FlightRune",(0,0,.30),.48,.018,p["glow"],root)
    if level>=15: torus("FlightAura",(0,0,.08),.68,.026,p["glow"],root)
    s=float(spec.get("scale",1.25))*(1+.025*r);root.scale=(s,s,s);return root


def build(uid,spec,level,p):
    ar=spec.get("archetype","humanoid")
    if ar=="giant": return build_giant(uid,spec,level,p)
    if ar=="construct": return build_construct(uid,spec,level,p)
    if ar in {"wyvern","drake","phoenix"}: return build_flying(uid,spec,level,p)
    root=build_humanoid(uid,spec,level,p)
    if ar=="winged_humanoid" or spec.get("flying"): wings(root,p,level,crystal=False)
    return root

# ---------- stage/export ----------
def bounds():
    pts=[]
    for o in bpy.context.scene.objects:
        if o.get(TAG) and o.type=="MESH":
            pts.extend(o.matrix_world@Vector(c) for c in o.bound_box)
    if not pts:return Vector((-1,-1,0)),Vector((1,1,2))
    return Vector((min(x.x for x in pts),min(x.y for x in pts),min(x.z for x in pts))),Vector((max(x.x for x in pts),max(x.y for x in pts),max(x.z for x in pts)))


def aim(o,target): o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()


def stage(size):
    mn,mx=bounds();center=(mn+mx)*.5;height=mx.z-mn.z;width=max(mx.x-mn.x,mx.y-mn.y)
    bpy.ops.object.camera_add(location=(4.8,-7.8,3.45));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=max(2.65,height*1.18,width*1.25);aim(cam,center)
    scene=bpy.context.scene;scene.camera=cam
    try:scene.render.engine='BLENDER_EEVEE_NEXT'
    except Exception:scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=size;scene.render.resolution_y=size;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
    try: scene.view_settings.look='AgX - Medium High Contrast'
    except Exception: pass
    for name,loc,power,sz in (("Key",(4,-5,6),650,4.0),("Fill",(-4,-3,3),230,3.8),("Rim",(2,4,5),800,3.0)):
        bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.name=name;light.data.energy=power;light.data.shape='DISK';light.data.size=sz;aim(light,center)
    scene.world.color=(.006,.009,.012)


def export_glb(path):
    bpy.ops.object.select_all(action='DESELECT');items=[]
    for o in bpy.context.scene.objects:
        if o.get(TAG):o.select_set(True);items.append(o)
    if items:bpy.context.view_layer.objects.active=items[0]
    kwargs=dict(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
    try:bpy.ops.export_scene.gltf(**kwargs,export_lights=False,export_cameras=False)
    except TypeError:bpy.ops.export_scene.gltf(**kwargs)


def progression_changes(level):
    labels={1:"base class identity",2:"rank trim",3:"belt rune",4:"cuirass/gear reinforcement",5:"shoulder armor",6:"elite trim/shield upgrade",7:"greaves/weapon growth",8:"bracers/weapon rune",9:"chest enchantment",10:"prestige trim",11:"waist rune",12:"elite crest/spikes",13:"master trim",14:"weapon/shoulder magic",15:"mastery aura/final silhouette"}
    return labels[level]


def generate(uid,spec,level,out,size,save_blend):
    clear_scene();p=palette(spec,level);root=build(uid,spec,level,p);root.name=f"troop_{uid}_L{level:02d}";root["unit_id"]=uid;root["level"]=level;root["name"]=spec["name"]
    stage(size)
    folder=out/uid/f"level-{level:02d}";folder.mkdir(parents=True,exist_ok=True)
    glb=folder/f"{uid}-level-{level:02d}.glb";png=folder/f"{uid}-level-{level:02d}.png"
    export_glb(glb);bpy.context.scene.render.filepath=str(png);bpy.ops.render.render(write_still=True)
    blend=None
    if save_blend:
        blend=folder/f"{uid}-level-{level:02d}.blend";bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    meta={"generator":"army-v3","id":uid,"name":spec["name"],"level":level,"max_level":15,"archetype":spec.get("archetype"),"weapon":spec.get("weapon"),"silhouette":spec.get("silhouette"),"motif":spec.get("motif"),"progression_change":progression_changes(level),"glb":glb.name,"preview":png.name,"blend":blend.name if blend else None}
    (folder/"metadata.json").write_text(json.dumps(meta,indent=2),encoding='utf-8');return meta


def update_manifest(out,items):
    path=out/"manifest.json";old={"generator":"army-v3","assets":[]}
    if path.exists():
        try:old=json.loads(path.read_text(encoding='utf-8'))
        except Exception:pass
    idx={(x["id"],x["level"]):x for x in old.get("assets",[])}
    for x in items:idx[(x["id"],x["level"])]=x
    old["generator"]="tools/blender/generate_army_v3.py";old["assets"]=sorted(idx.values(),key=lambda x:(x["id"],x["level"]))
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(old,indent=2),encoding='utf-8')


def main():
    a=cli();specs=json.loads(SPECS_PATH.read_text(encoding='utf-8'))["troops"]
    if a.all_troops:work=list(specs.items())
    else:
        if a.unit not in specs:raise SystemExit(f"Unknown troop {a.unit}. Available: {', '.join(specs)}")
        work=[(a.unit,specs[a.unit])]
    levels=parse_levels(a.levels);out=Path(a.output).resolve();items=[]
    for uid,spec in work:
        for level in levels:
            print(f"[Army v3] {spec['name']} ({uid}) level {level}/15",flush=True)
            items.append(generate(uid,spec,level,out,a.preview_size,a.save_blend))
    update_manifest(out,items);print(f"Generated {len(items)} Army level assets -> {out}",flush=True)

if __name__=="__main__":main()
