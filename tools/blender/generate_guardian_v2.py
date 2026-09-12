#!/usr/bin/env python3
"""Premium smooth Guardian generator for Emberfall Kingdoms.

Generates ONLY the first Army unit (Guardian) at levels 1..15.
The look is an original premium mobile-MOBA-inspired fantasy knight: smooth
surfaces, clean heroic proportions, readable blue/silver/gold silhouette,
and meaningful structural progression every level.

Outputs per level: GLB, transparent PNG, metadata.json and optional BLEND.
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

spec = importlib.util.spec_from_file_location("emberfall_army_v3_guardian2", V3_PATH)
v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3)

MAX_LEVEL = 15


def cli():
    raw = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--levels", default="1-15")
    p.add_argument("--output", default=str(ROOT / "generated" / "guardian-v2"))
    p.add_argument("--preview-size", type=int, default=512)
    p.add_argument("--save-blend", action="store_true")
    return p.parse_args(raw)


def parse_levels(text):
    vals=set()
    for c in text.split(','):
        c=c.strip()
        if not c: continue
        if '-' in c:
            a,b=map(int,c.split('-',1)); vals.update(range(min(a,b),max(a,b)+1))
        else: vals.add(int(c))
    vals=sorted(x for x in vals if 1<=x<=15)
    if not vals: raise SystemExit("Guardian levels must be within 1..15")
    return vals


def mat(name, color, metallic=0.0, rough=.4, emission=None, strength=0.0):
    return v3.material(name, color, metallic, rough, emission, strength)


def palette(level):
    r=(level-1)/14
    return {
        "skin": mat("Skin",(.62,.40,.28),0,.46),
        "skin2": mat("SkinWarm",(.72,.48,.34),0,.45),
        "hair": mat("Hair",(.055,.025,.018),0,.58),
        "blue": mat("RoyalBlue",(.025,.13+.025*r,.30+.05*r),0,.42),
        "blue2": mat("DeepBlue",(.018,.055,.14),0,.50),
        "silver": mat("Silver",(.46+.15*r,.50+.15*r,.56+.14*r),.84,.18),
        "silver2": mat("DarkSilver",(.17,.22,.29),.78,.22),
        "gold": mat("Gold",(.72+.12*r,.48+.08*r,.16),.82,.17),
        "gold2": mat("DarkGold",(.40,.22,.055),.76,.22),
        "leather": mat("Leather",(.19,.075,.025),0,.63),
        "cloth": mat("Cloth",(.035,.14,.32),0,.55),
        "cloth_dark": mat("ClothDark",(.015,.045,.105),0,.62),
        "white": mat("EyeWhite",(.78,.82,.84),0,.30),
        "iris": mat("Iris",(.025,.12,.20),0,.24),
        "black": mat("Black",(.006,.008,.012),0,.38),
        "glow": mat("AzureMagic",(.08,.46,.98),.06,.14,(.06,.42,1.0),.7+1.7*r),
        "glow2": mat("WarmMagic",(1.0,.58,.16),.04,.14,(1.0,.42,.08),.5+1.2*r),
        "fur": mat("WhiteFur",(.78,.80,.82),0,.75),
    }


def finish(o,name,material,root,bevel=.0,subsurf=0,smooth=True):
    o.name=name; o.parent=root; o[v3.TAG]=True
    if o.type=='MESH':
        o.data.materials.append(material)
        if smooth:
            for poly in o.data.polygons: poly.use_smooth=True
        if bevel:
            m=o.modifiers.new("SoftBevel","BEVEL"); m.width=bevel; m.segments=3
        if subsurf:
            m=o.modifiers.new("SmoothSurface","SUBSURF"); m.levels=subsurf; m.render_levels=subsurf
    return o


def ellipsoid(name,loc,scale,material,root,segments=32,rings=18,subsurf=1):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    o=bpy.context.object; o.scale=scale
    bpy.context.view_layer.objects.active=o; o.select_set(True)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.select_set(False)
    return finish(o,name,material,root,.008,subsurf,True)


def capsule(name,a,b,r,material,root):
    a,b=Vector(a),Vector(b); v=b-a; mid=(a+b)*.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=v.length,location=mid)
    o=bpy.context.object; o.rotation_mode='QUATERNION'; o.rotation_quaternion=Vector((0,0,1)).rotation_difference(v.normalized())
    finish(o,name,material,root,.028,1,True)
    ellipsoid(name+"A",a,(r,r,r),material,root,24,14,1)
    ellipsoid(name+"B",b,(r,r,r),material,root,24,14,1)


def rounded_box(name,loc,scale,material,root,rot=(0,0,0),bevel=.05):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc,rotation=rot)
    o=bpy.context.object; o.scale=scale
    bpy.context.view_layer.objects.active=o; o.select_set(True)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.select_set(False)
    return finish(o,name,material,root,bevel,1,False)


def custom_plate(name,verts,faces,material,root,bevel=.035):
    mesh=bpy.data.meshes.new(name+"Mesh"); mesh.from_pydata(verts,[],faces); mesh.update()
    o=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(o)
    return finish(o,name,material,root,bevel,1,False)


def kite_shield_mesh(name,x,y,z,w,h,depth,material,root):
    # Convex, elegant kite shield with a pointed lower tip.
    front=y-depth/2; back=y+depth/2
    pts2=[(0,h*.52),(-w*.48,h*.30),(-w*.44,-h*.18),(0,-h*.55),(w*.44,-h*.18),(w*.48,h*.30)]
    verts=[(x+px,front,z+pz) for px,pz in pts2]+[(x+px,back,z+pz) for px,pz in pts2]
    faces=[(0,1,2,3,4,5),(11,10,9,8,7,6)]
    for i in range(6): faces.append((i,(i+1)%6,(i+1)%6+6,i+6))
    return custom_plate(name,verts,faces,material,root,.045)


def blade_mesh(name,a,b,width,thickness,material,root):
    a,b=Vector(a),Vector(b); d=(b-a).normalized(); side=Vector((1,0,0))
    if abs(d.dot(side))>.9: side=Vector((0,1,0))
    side=(d.cross(side)).normalized()*width
    normal=(d.cross(side)).normalized()*thickness
    tip=b+d*width*.7
    base=a
    verts=[tuple(base-side-normal),tuple(base+side-normal),tuple(base+side+normal),tuple(base-side+normal),tuple(tip-normal*.45),tuple(tip+normal*.45)]
    faces=[(0,1,2,3),(0,4,1),(3,2,5),(0,3,5,4),(1,4,5,2)]
    return custom_plate(name,verts,faces,material,root,.012)


def face(root,p,level):
    # Heroic stylized head, readable in a 512px preview.
    z=2.04
    ellipsoid("Head",(0,-.04,z),(.205,.178,.245),p["skin2"],root,32,18,1)
    # subtle jaw and chin geometry
    ellipsoid("Jaw",(0,-.085,z-.08),(.175,.145,.145),p["skin"],root,28,16,1)
    ellipsoid("Chin",(0,-.188,z-.155),(.075,.045,.060),p["skin2"],root,24,12,1)
    for s,l in ((-1,"L"),(1,"R")):
        ellipsoid(f"EyeWhite.{l}",(s*.070,-.195,z+.045),(.034,.012,.022),p["white"],root,20,10,0)
        ellipsoid(f"Iris.{l}",(s*.070,-.207,z+.045),(.014,.007,.015),p["iris"],root,16,8,0)
        # eyebrow
        v3.beam(f"Brow.{l}",(s*.120,-.210,z+.105),(s*.025,-.210,z+.095),.010,.007,p["hair"],root,.004)
    ellipsoid("Nose",(0,-.208,z-.005),(.030,.045,.060),p["skin2"],root,20,12,0)
    v3.beam("Mouth",(-.045,-.206,z-.100),(.045,-.206,z-.100),.006,.006,p["black"],root,.002)
    # Swept-back brown hair with separated locks.
    ellipsoid("HairBack",(0,.055,z+.11),(.220,.150,.185),p["hair"],root,28,16,1)
    for i,(x,rz) in enumerate(((-.15,-.20),(-.08,-.08),(0,.04),(.08,.11),(.15,.20))):
        v3.cone(f"HairLock.{i}",(x,-.115,z+.23),.048,.010,.20,p["hair"],root,rot=(.12,rz,0),vertices=9)


def body(root,p,level):
    # Athletic, clean proportions rather than blocky primitives.
    ellipsoid("ChestBase",(0,0,1.42),(.37,.25,.47),p["cloth"],root,32,18,1)
    ellipsoid("Waist",(0,0,1.03),(.285,.205,.26),p["cloth_dark"],root,28,16,1)
    rounded_box("Belt",(0,-.02,.96),(.34,.20,.047),p["leather"],root,bevel=.025)
    rounded_box("Buckle",(0,-.225,.96),(.055,.018,.055),p["gold"],root,bevel=.012)
    # split blue tabard
    rounded_box("Tabard.L",(-.095,-.248,.77),(.095,.020,.31),p["blue"],root,rot=(0,0,-.025),bevel=.025)
    rounded_box("Tabard.R",(.095,-.248,.77),(.095,.020,.31),p["blue"],root,rot=(0,0,.025),bevel=.025)
    # gold hem appears early and becomes a constant identity cue
    if level>=2:
        rounded_box("TabardTrim.L",(-.095,-.270,.49),(.095,.010,.018),p["gold"],root,bevel=.007)
        rounded_box("TabardTrim.R",(.095,-.270,.49),(.095,.010,.018),p["gold"],root,bevel=.007)
    if level>=3:
        # smooth chest armor shell
        ellipsoid("Breastplate",(0,-.055,1.45),(.36,.245,.39),p["silver"],root,32,18,1)
        rounded_box("ChestCenter",(0,-.280,1.43),(.065,.025,.235),p["silver2"],root,bevel=.035)
    if level>=4:
        for s,l in ((-1,"L"),(1,"R")):
            ellipsoid(f"Pauldron.{l}",(s*.43,-.015,1.57),(.205,.175,.145),p["silver"],root,28,16,1)
            rounded_box(f"PauldronGold.{l}",(s*.43,-.175,1.58),(.115,.020,.038),p["gold"],root,bevel=.012)
    if level>=6:
        # elegant gold chest framing
        rounded_box("ChestGoldTop",(0,-.310,1.62),(.235,.012,.018),p["gold"],root,bevel=.006)
        for s,l in ((-1,"L"),(1,"R")):
            v3.beam(f"ChestLine.{l}",(s*.22,-.310,1.60),(s*.10,-.310,1.29),.014,.007,p["gold"],root,.004)
    if level>=8:
        ellipsoid("ChestGem",(0,-.326,1.47),(.060,.020,.080),p["glow"],root,20,12,0)
    if level>=10:
        for s,l in ((-1,"L"),(1,"R")):
            # second-layer angular shoulder plate
            rounded_box(f"EliteShoulder.{l}",(s*.49,-.025,1.63),(.16,.15,.075),p["silver2"],root,rot=(0,s*.12,0),bevel=.045)
            v3.cone(f"ShoulderFin.{l}",(s*.60,.00,1.68),.045,.006,.24,p["gold"],root,rot=(0,s*.60,0),vertices=9)
    if level>=12:
        for s,l in ((-1,"L"),(1,"R")):
            ellipsoid(f"ShoulderRune.{l}",(s*.45,-.205,1.58),(.040,.014,.050),p["glow"],root,18,10,0)
    if level>=15:
        # radiant final chest crest
        v3.torus("ChestHalo",(0,-.328,1.47),.105,.010,p["glow2"],root,rot=(math.pi/2,0,0))


def legs(root,p,level):
    for s,l in ((-1,"L"),(1,"R")):
        hip=(s*.18,0,.91); knee=(s*.205,-.015,.56); ankle=(s*.21,-.025,.21)
        capsule(f"Thigh.{l}",hip,knee,.105,p["cloth_dark"],root)
        capsule(f"Shin.{l}",knee,ankle,.095,p["cloth_dark"],root)
        rounded_box(f"Boot.{l}",(s*.21,-.085,.115),(.135,.185,.10),p["leather"],root,bevel=.055)
        if level>=5:
            rounded_box(f"Greave.{l}",(s*.21,-.115,.40),(.105,.072,.19),p["silver"],root,bevel=.055)
            ellipsoid(f"Knee.{l}",(s*.205,-.150,.575),(.112,.060,.090),p["silver2"],root,24,14,1)
        if level>=9:
            rounded_box(f"GreaveGold.{l}",(s*.21,-.186,.42),(.055,.012,.15),p["gold"],root,bevel=.010)
        if level>=13:
            ellipsoid(f"KneeRune.{l}",(s*.205,-.215,.58),(.032,.012,.042),p["glow"],root,16,8,0)


def arms(root,p,level):
    for s,l in ((-1,"L"),(1,"R")):
        shoulder=(s*.39,0,1.53)
        elbow=(s*.50,-.035,1.23)
        hand=(s*.53,-.10,1.00) if s>0 else (s*.50,-.245,1.10)
        capsule(f"UpperArm.{l}",shoulder,elbow,.090,p["blue2"],root)
        capsule(f"Forearm.{l}",elbow,hand,.073,p["skin"],root)
        ellipsoid(f"Hand.{l}",hand,(.080,.067,.083),p["skin2"],root,24,14,1)
        if level>=4:
            # silver upper-arm guard under pauldrons
            ellipsoid(f"ArmGuard.{l}",((shoulder[0]+elbow[0])*.5,-.035,1.38),(.105,.085,.16),p["silver2"],root,24,14,1)
        if level>=6:
            mid=((elbow[0]+hand[0])*.5,(elbow[1]+hand[1])*.5,(elbow[2]+hand[2])*.5)
            capsule(f"Bracer.{l}",elbow,mid,.092,p["silver"],root)
        if level>=11:
            v3.torus(f"WristGold.{l}",hand,.088,.012,p["gold"],root,rot=(math.pi/2,0,0))


def helmet(root,p,level):
    face(root,p,level)
    z=2.04
    if level<5: return
    # open-face smooth shell, preserving face readability
    ellipsoid("HelmetShell",(0,.055,z+.10),(.225,.165,.185),p["silver2"],root,30,18,1)
    rounded_box("HelmetBrow",(0,-.175,z+.13),(.175,.030,.042),p["silver"],root,bevel=.025)
    for s,l in ((-1,"L"),(1,"R")):
        rounded_box(f"CheekGuard.{l}",(s*.163,-.145,z-.025),(.042,.028,.115),p["silver2"],root,rot=(0,0,s*.10),bevel=.020)
    if level>=10:
        v3.cone("HelmetCrest",(0,.05,z+.42),.055,.010,.36,p["gold"],root,vertices=10)
    if level>=12:
        for s,l in ((-1,"L"),(1,"R")):
            # stylized winged crest, original shape
            v3.cone(f"CrestWing.{l}",(s*.235,.03,z+.22),.042,.004,.25,p["gold"],root,rot=(0,s*.62,0),vertices=9)
            v3.cone(f"CrestFeather.{l}",(s*.29,.04,z+.28),.032,.003,.20,p["silver"],root,rot=(0,s*.78,0),vertices=9)
    if level>=15:
        ellipsoid("HelmRune",(0,-.202,z+.16),(.045,.014,.062),p["glow"],root,16,8,0)


def cape(root,p,level):
    if level<7: return
    # broad flowing cape from upper back, smooth and layered
    rows=5 if level<12 else 7
    cols=5
    verts=[]; faces=[]
    for r in range(rows):
        t=r/(rows-1)
        zz=1.62-t*(1.05 if level>=12 else .88)
        yy=.18+t*(.16+.06*math.sin(t*math.pi))
        half=.31+.10*t
        for c in range(cols):
            u=c/(cols-1); x=(u-.5)*2*half
            yy2=yy+.025*math.cos(u*math.pi*2+t*2)
            verts.append((x,yy2,zz+.035*math.sin(u*math.pi)))
    for r in range(rows-1):
        for c in range(cols-1):
            a=r*cols+c; faces.append((a,a+1,a+1+cols,a+cols))
    o=custom_plate("Cape",verts,faces,p["blue"],root,.006)
    sol=o.modifiers.new("CapeThickness","SOLIDIFY"); sol.thickness=.018
    if level>=10:
        rounded_box("CapeGoldClasp",(0,.155,1.63),(.12,.045,.045),p["gold"],root,bevel=.025)
    if level>=12:
        # white mantle for elite silhouette
        for s in (-1,0,1): ellipsoid(f"Mantle.{s}",(s*.21,.13,1.62),(.22,.09,.105),p["fur"],root,22,12,1)


def shield(root,p,level):
    x,y,z=-.57,-.34,1.12
    w=.58 + .035*max(0,level-4) + .020*max(0,level-10)
    h=1.08 + .030*max(0,level-4) + .025*max(0,level-10)
    matl=p["blue"] if level<3 else p["silver2"]
    kite_shield_mesh("ShieldBase",x,y,z,w,h,.10,matl,root)
    # inset face plate
    kite_shield_mesh("ShieldFace",x,y-.060,z,w*.86,h*.88,.025,p["blue"],root)
    # border via scaled second plate reads as polished gold rim
    if level>=2:
        kite_shield_mesh("ShieldGoldFrame",x,y-.078,z,w*.96,h*.96,.018,p["gold"],root)
        kite_shield_mesh("ShieldBlueInset",x,y-.090,z,w*.82,h*.83,.022,p["blue"],root)
    # central heraldic diamond/star motif
    ellipsoid("ShieldBoss",(x,y-.112,z+.05),(.090,.025,.115),p["gold"],root,20,12,1)
    if level>=6:
        for s,l in ((-1,"L"),(1,"R")):
            v3.beam(f"ShieldRay.{l}",(x,y-.120,z+.05),(x+s*w*.28,y-.120,z+.25),.018,.008,p["gold"],root,.005)
            v3.beam(f"ShieldRayLow.{l}",(x,y-.120,z+.02),(x+s*w*.24,y-.120,z-.24),.014,.008,p["gold"],root,.005)
    if level>=8:
        ellipsoid("ShieldCore",(x,y-.140,z+.05),(.060,.018,.085),p["glow"],root,18,10,0)
    if level>=9:
        v3.torus("ShieldRuneRing",(x,y-.145,z+.05),.17,.012,p["glow"],root,rot=(math.pi/2,0,0))
    if level>=11:
        for s,l in ((-1,"L"),(1,"R")):
            v3.cone(f"ShieldCrown.{l}",(x+s*w*.32,y-.08,z+h*.43),.035,.004,.22,p["gold"],root,rot=(0,s*.42,0),vertices=9)
    if level>=14:
        v3.torus("ShieldEnergy",(x,y-.155,z+.05),.245,.015,p["glow"],root,rot=(math.pi/2,.24,0))
    if level>=15:
        v3.torus("ShieldMasterRing",(x,y-.160,z+.05),.305,.012,p["glow2"],root,rot=(math.pi/2,-.30,0))


def sword(root,p,level):
    hand=Vector((.53,-.10,1.00)); grip_end=Vector((.63,-.12,1.18))
    blade_start=grip_end+Vector((.01,0,.03)); blade_end=Vector((.97,-.14,1.92+.018*level))
    capsule("SwordGrip",hand,grip_end,.040,p["leather"],root)
    v3.beam("SwordGuard",(.48,-.13,1.19),(.78,-.13,1.19),.030,.026,p["gold"],root,.012)
    width=.065+.006*max(0,level-4)+.006*max(0,level-10)
    blade_mesh("SwordBlade",blade_start,blade_end,width,.018,p["silver"],root)
    ellipsoid("Pommel",tuple(hand+Vector((-.025,0,-.065))),(.047,.035,.058),p["gold"],root,18,10,1)
    if level>=7:
        ellipsoid("SwordGem",(.75,-.155,1.48),(.033,.012,.045),p["glow"],root,16,8,0)
    if level>=10:
        # gold spine accent
        v3.rod("SwordGoldSpine",(.73,-.160,1.42),(.91,-.160,1.82),.009,p["gold"],root,8)
    if level>=14:
        v3.rod("SwordEnergyCore",(.72,-.168,1.39),(.94,-.168,1.86),.010,p["glow"],root,8)
    if level>=15:
        v3.torus("SwordAura",(.93,-.15,1.82),.11,.009,p["glow2"],root,rot=(math.pi/2,0,0))


def final_auras(root,p,level):
    if level>=13:
        # small shoulder energy feathers; readable but not overdone for an Army unit
        for s,l in ((-1,"L"),(1,"R")):
            v3.cone(f"EnergyFin.{l}",(s*.60,.07,1.72),.035,.003,.23,p["glow"],root,rot=(0,s*.68,0),vertices=9)
    if level>=15:
        # final prestige halo arcs behind the head/shoulders
        for ang in (-.55,0,.55):
            t=v3.torus(f"MasterHalo{ang}",(0,.20,2.15),.34+.06*abs(ang),.012,p["glow2"],root,rot=(math.pi/2,ang,0))
        v3.torus("MasterGroundAura",(0,0,.055),.72,.020,p["glow"],root)


LEVEL_CHANGES={
1:"Recruit Guardian: blue tunic, leather, simple polished kite shield and sword",
2:"Gold tabard trim and framed shield",
3:"Smooth silver breastplate and rank-ready shield",
4:"Rounded pauldrons and upper-arm guards",
5:"Greaves, knees and open-face helmet shell",
6:"Gold chest framing, polished bracers and shield heraldry",
7:"Flowing blue cape and sword gem",
8:"Azure chest gem and shield energy core",
9:"Gold greave accents and glowing shield rune ring",
10:"Elite shoulder layer, helmet crest, sword gold spine",
11:"Wrist gold rank rings and crowned shield silhouette",
12:"Winged helmet crest, white mantle and shoulder runes",
13:"Knee runes and restrained shoulder energy fins",
14:"Enchanted sword core and expanded shield energy",
15:"Master Guardian: radiant crest, double shield aura, sword aura and prestige halos",
}


def build(level):
    p=palette(level); root=v3.root_empty("GuardianRoot")
    body(root,p,level); legs(root,p,level); arms(root,p,level); helmet(root,p,level)
    cape(root,p,level); shield(root,p,level); sword(root,p,level); final_auras(root,p,level)
    # Stable heroic proportion; tiny scale increase only.
    s=1.0+.015*(level-1)/14; root.scale=(s,s,s)
    return root,p


def stage(size):
    v3.stage(size)
    sc=bpy.context.scene
    sc.render.resolution_x=size; sc.render.resolution_y=size
    sc.render.film_transparent=True
    try:
        sc.eevee.use_gtao=True; sc.eevee.gtao_distance=3; sc.eevee.gtao_factor=1.2
        sc.eevee.taa_render_samples=64
    except Exception: pass
    try: sc.view_settings.look='AgX - Medium High Contrast'
    except Exception: pass


def generate(level,out,size,save_blend):
    v3.clear_scene(); root,p=build(level); root.name=f"troop_guardian_L{level:02d}"
    root["unit_id"]="guardian"; root["level"]=level; root["name"]="Guardian"
    stage(size)
    folder=out/"guardian"/f"level-{level:02d}"; folder.mkdir(parents=True,exist_ok=True)
    glb=folder/f"guardian-level-{level:02d}.glb"; png=folder/f"guardian-level-{level:02d}.png"
    v3.export_glb(glb); bpy.context.scene.render.filepath=str(png); bpy.ops.render.render(write_still=True)
    blend=None
    if save_blend:
        blend=folder/f"guardian-level-{level:02d}.blend"; bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    meta={"generator":"guardian-v2","id":"guardian","name":"Guardian","level":level,"max_level":15,
          "role":"frontline defensive melee","visual_style":"original smooth premium mobile fantasy",
          "progression_change":LEVEL_CHANGES[level],"glb":glb.name,"preview":png.name,"blend":blend.name if blend else None}
    (folder/"metadata.json").write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return meta


def main():
    a=cli(); levels=parse_levels(a.levels); out=Path(a.output).resolve(); assets=[]
    for level in levels:
        print(f"[Guardian v2] Level {level}/15 - {LEVEL_CHANGES[level]}",flush=True)
        assets.append(generate(level,out,a.preview_size,a.save_blend))
    out.mkdir(parents=True,exist_ok=True)
    (out/"manifest.json").write_text(json.dumps({"generator":"tools/blender/generate_guardian_v2.py","unit":"guardian","assets":assets},indent=2),encoding='utf-8')
    print(f"Generated {len(assets)} premium Guardian levels -> {out}",flush=True)

if __name__=='__main__': main()
