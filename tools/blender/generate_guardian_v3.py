#!/usr/bin/env python3
"""Emberfall Guardian v3 — smooth premium Army character, Level 1..15.

This generator intentionally builds ONLY the first Army unit: Guardian.
It targets a polished original mobile-MOBA-inspired fantasy look without
copying any existing character. Compared with earlier procedural drafts,
this version uses longer heroic proportions, custom tapered organic meshes,
clean layered armor, a dynamic sword-down pose, a large beveled kite shield,
flowing cloth, restrained facial features, and level-specific geometry.

Outputs per level: GLB, PNG preview, metadata.json, optional editable BLEND.
Designed for Blender headless execution in GitHub Actions.
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
BASE_PATH = Path(__file__).resolve().with_name("generate_army_v3.py")
BASE_SPEC = importlib.util.spec_from_file_location("emberfall_army_base", BASE_PATH)
base = importlib.util.module_from_spec(BASE_SPEC)
BASE_SPEC.loader.exec_module(base)

MAX_LEVEL = 15
TAG = base.TAG


def args():
    raw = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--levels", default="1-15")
    p.add_argument("--output", default=str(ROOT / "generated" / "guardian-v3"))
    p.add_argument("--preview-size", type=int, default=768)
    p.add_argument("--save-blend", action="store_true")
    return p.parse_args(raw)


def parse_levels(text: str):
    out=set()
    for chunk in text.split(','):
        chunk=chunk.strip()
        if not chunk: continue
        if '-' in chunk:
            a,b=map(int,chunk.split('-',1)); out.update(range(min(a,b),max(a,b)+1))
        else: out.add(int(chunk))
    vals=sorted(x for x in out if 1<=x<=MAX_LEVEL)
    if not vals: raise SystemExit("Guardian levels must be within 1..15")
    return vals


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
def M(name,color,metal=0.0,rough=.42,emission=None,strength=0.0):
    m=base.material(name,color,metal,rough,emission,strength)
    m.diffuse_color=(*color,1)
    return m


def materials(level):
    t=(level-1)/14
    steel=(.34+.15*t,.39+.15*t,.47+.14*t)
    silver=(.58+.12*t,.62+.12*t,.68+.11*t)
    gold=(.63+.16*t,.39+.10*t,.10+.035*t)
    blue=(.025,.105+.035*t,.27+.06*t)
    glow=(.035,.40+.12*t,1.0)
    return {
        "skin":M("Skin",(.61,.39,.27),0,.48),
        "skin_hi":M("SkinWarm",(.71,.48,.34),0,.46),
        "hair":M("Hair",(.040,.020,.014),0,.56),
        "eye":M("Eye",(.72,.78,.80),0,.24),
        "iris":M("Iris",(.025,.09,.16),0,.20),
        "mouth":M("Mouth",(.12,.025,.022),0,.55),
        "blue":M("RoyalBlue",blue,0,.48),
        "blue_dark":M("RoyalBlueDark",(.010,.035,.095),0,.56),
        "blue_light":M("RoyalBlueLight",(.045,.22+.03*t,.44+.07*t),0,.42),
        "steel":M("Steel",steel,.74,.28),
        "silver":M("Silver",silver,.78,.24),
        "darksteel":M("DarkSteel",(.10,.14,.20),.68,.30),
        "gold":M("Gold",gold,.76,.23),
        "gold_dark":M("GoldDark",(.31,.17,.04),.72,.28),
        "leather":M("Leather",(.18,.065,.022),0,.66),
        "leather2":M("LeatherLight",(.31,.13,.045),0,.61),
        "cloth":M("Cloth",blue,0,.60),
        "cloth_dark":M("ClothDark",(.012,.034,.085),0,.65),
        "whitefur":M("WhiteFur",(.72,.75,.78),0,.80),
        "glow":M("AzureGlow",glow,.05,.16,glow,.8+1.5*t),
        "warmglow":M("WarmGlow",(1.0,.50,.10),.03,.16,(1.0,.35,.04),.5+1.1*t),
    }


# ---------------------------------------------------------------------------
# Mesh helpers
# ---------------------------------------------------------------------------
def root_empty():
    o=bpy.data.objects.new("GuardianRoot",None); bpy.context.collection.objects.link(o); o[TAG]=True; return o


def finish(o,name,mat,root,bevel=0.0,subsurf=0,smooth=True):
    o.name=name; o.parent=root; o[TAG]=True
    if o.type=='MESH':
        o.data.materials.append(mat)
        if smooth:
            for poly in o.data.polygons: poly.use_smooth=True
        if bevel>0:
            b=o.modifiers.new("SoftBevel","BEVEL"); b.width=bevel; b.segments=3
        if subsurf>0:
            s=o.modifiers.new("SurfaceSmooth","SUBSURF"); s.levels=subsurf; s.render_levels=subsurf
    return o


def mesh_obj(name,verts,faces,mat,root,bevel=.0,subsurf=0,smooth=True):
    me=bpy.data.meshes.new(name+"Mesh"); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o)
    return finish(o,name,mat,root,bevel,subsurf,smooth)


def uv(name,loc,scale,mat,root,segments=32,rings=18,subsurf=1):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc)
    o=bpy.context.object; o.scale=scale
    bpy.context.view_layer.objects.active=o; o.select_set(True)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.select_set(False)
    return finish(o,name,mat,root,.004,subsurf,True)


def rounded_box(name,loc,scale,mat,root,rot=(0,0,0),bevel=.035,subsurf=1):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc,rotation=rot)
    o=bpy.context.object; o.scale=scale
    bpy.context.view_layer.objects.active=o; o.select_set(True)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.select_set(False)
    return finish(o,name,mat,root,bevel,subsurf,False)


def cone(name,loc,r1,r2,depth,mat,root,rot=(0,0,0),vertices=16):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=r1,radius2=r2,depth=depth,location=loc,rotation=rot)
    return finish(bpy.context.object,name,mat,root,.012,1,True)


def torus(name,loc,major,minor,mat,root,rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=32,minor_segments=10,location=loc,rotation=rot)
    return finish(bpy.context.object,name,mat,root,.004,1,True)


def tube(name,points,radii,mat,root,sides=16,bevel=.006,subsurf=1):
    """Smooth tapered tube through 3D points, with local ring orientation."""
    pts=[Vector(p) for p in points]
    verts=[]
    frames=[]
    for i,p in enumerate(pts):
        if i==0: tangent=(pts[1]-pts[0]).normalized()
        elif i==len(pts)-1: tangent=(pts[-1]-pts[-2]).normalized()
        else: tangent=(pts[i+1]-pts[i-1]).normalized()
        ref=Vector((0,1,0))
        if abs(tangent.dot(ref))>.92: ref=Vector((1,0,0))
        u=tangent.cross(ref).normalized(); v=tangent.cross(u).normalized(); frames.append((u,v))
    for i,p in enumerate(pts):
        u,v=frames[i]; r=radii[i]
        for j in range(sides):
            a=2*math.pi*j/sides; q=p+u*(math.cos(a)*r)+v*(math.sin(a)*r); verts.append(tuple(q))
    faces=[]
    for i in range(len(pts)-1):
        for j in range(sides):
            a=i*sides+j; b=i*sides+(j+1)%sides; c=(i+1)*sides+(j+1)%sides; d=(i+1)*sides+j
            faces.append((a,b,c,d))
    faces.append(tuple(range(sides-1,-1,-1)))
    faces.append(tuple((len(pts)-1)*sides+j for j in range(sides)))
    return mesh_obj(name,verts,faces,mat,root,bevel,subsurf,True)


def ring_body(name,rings,mat,root,sides=24,bevel=.004,subsurf=1):
    """Organic elliptical torso from (z,rx,ry,y_offset) profile rings."""
    verts=[]
    for z,rx,ry,yo in rings:
        for j in range(sides):
            a=2*math.pi*j/sides
            verts.append((math.cos(a)*rx,yo+math.sin(a)*ry,z))
    faces=[]
    for i in range(len(rings)-1):
        for j in range(sides):
            a=i*sides+j;b=i*sides+(j+1)%sides;c=(i+1)*sides+(j+1)%sides;d=(i+1)*sides+j
            faces.append((a,b,c,d))
    faces.append(tuple(range(sides-1,-1,-1)))
    last=(len(rings)-1)*sides; faces.append(tuple(last+j for j in range(sides)))
    return mesh_obj(name,verts,faces,mat,root,bevel,subsurf,True)


def plate(name,pts,depth,mat,root,bevel=.025,subsurf=1):
    """Extruded front-facing polygon; pts are (x,z), y centered around -depth/2."""
    front=-depth; back=0
    verts=[(x,front,z) for x,z in pts]+[(x,back,z) for x,z in pts]
    n=len(pts); faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    for i in range(n): faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
    return mesh_obj(name,verts,faces,mat,root,bevel,subsurf,False)


def beam(name,a,b,width,thick,mat,root):
    a,b=Vector(a),Vector(b); d=b-a; mid=(a+b)*.5
    bpy.ops.mesh.primitive_cube_add(size=1,location=mid)
    o=bpy.context.object; o.scale=(width,thick,d.length/2)
    bpy.context.view_layer.objects.active=o; o.select_set(True); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.select_set(False)
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=Vector((0,0,1)).rotation_difference(d.normalized())
    return finish(o,name,mat,root,.012,1,False)


# ---------------------------------------------------------------------------
# Anatomy / face
# ---------------------------------------------------------------------------
def build_head(root,p,level):
    # Smaller, mature heroic head — deliberately avoids chibi/bobble proportions.
    z=2.075
    uv("Head",(0,-.035,z),(.155,.142,.190),p["skin_hi"],root,36,20,1)
    uv("Jaw",(0,-.070,z-.080),(.137,.126,.118),p["skin"],root,32,18,1)
    uv("Chin",(0,-.155,z-.145),(.055,.038,.045),p["skin_hi"],root,24,14,1)
    uv("Neck",(0,.0,1.835),(.105,.095,.13),p["skin"],root,28,16,1)
    # restrained eyes and brows, not cartoon circles
    for s,l in ((-1,"L"),(1,"R")):
        uv(f"Eye.{l}",(s*.051,-.172,z+.028),(.024,.007,.012),p["eye"],root,18,10,0)
        uv(f"Iris.{l}",(s*.051,-.179,z+.028),(.009,.004,.009),p["iris"],root,14,8,0)
        beam(f"Brow.{l}",(s*.092,-.178,z+.075),(s*.020,-.178,z+.070),.006,.004,p["hair"],root)
    # nose wedge and narrow mouth
    pts=[(-.028,z+.045),(.028,z+.045),(.018,z-.040),(0,z-.068),(-.018,z-.040)]
    nose=plate("Nose",[(x,zz) for x,zz in pts],.032,p["skin_hi"],root,.008,1); nose.location.y=-.158
    beam("Mouth",(-.035,-.177,z-.096),(.035,-.177,z-.096),.004,.003,p["mouth"],root)
    # smooth swept hair cap plus layered locks
    uv("HairCap",(0,.035,z+.105),(.165,.125,.125),p["hair"],root,30,18,1)
    lock_data=[(-.12,.18,-.22),(-.075,.21,-.12),(-.025,.225,-.04),(.03,.22,.05),(.08,.205,.13),(.125,.18,.21)]
    for i,(x,h,rz) in enumerate(lock_data):
        tube(f"HairLock.{i}",[(x,-.105,z+.12),(x*.92,-.135,z+h)], [.034,.012], p["hair"],root,10,.003,1)


def build_body(root,p,level):
    # Under-tunic torso with long athletic proportions.
    ring_body("Tunic",[(1.03,.255,.155,.01),(1.18,.285,.17,.0),(1.45,.345,.205,.0),(1.66,.39,.215,.015),(1.73,.35,.19,.02)],p["blue"],root,28,.004,1)
    rounded_box("Belt",(0,-.015,1.055),(.285,.165,.042),p["leather"],root,bevel=.025,subsurf=1)
    rounded_box("Buckle",(0,-.188,1.055),(.047,.018,.050),p["gold"],root,bevel=.012,subsurf=1)
    # Split tabard starts at level 1, with elegant taper.
    for s,l in ((-1,"L"),(1,"R")):
        pts=[(s*.02,1.03),(s*.20,1.00),(s*.18,.54),(s*.08,.43),(s*.025,.52)] if s>0 else [(s*.02,1.03),(s*.20,1.00),(s*.18,.54),(s*.08,.43),(s*.025,.52)]
        tab=plate(f"Tabard.{l}",pts,.025,p["cloth"],root,.012,1); tab.location.y=-.185
    if level>=2:
        for s,l in ((-1,"L"),(1,"R")):
            beam(f"TabardTrim.{l}",(s*.06,-.216,.52),(s*.15,-.216,.57),.013,.006,p["gold"],root)
    # Breastplate is a custom tapered shell instead of a spherical blob.
    if level>=3:
        ring_body("Cuirass",[(1.20,.285,.185,-.025),(1.39,.345,.225,-.030),(1.61,.385,.225,-.020),(1.69,.345,.195,-.005)],p["steel"],root,28,.003,1)
        plate("CuirassCenter",[(-.065,1.61),(.065,1.61),(.085,1.29),(0,1.20),(-.085,1.29)],.055,p["darksteel"],root,.018,1).location.y=-.208
    if level>=4:
        # Layered flattened shoulder plates, not round balls.
        for s,l in ((-1,"L"),(1,"R")):
            uv(f"ShoulderBase.{l}",(s*.425,-.010,1.64),(.165,.120,.092),p["steel"],root,28,16,1)
            rounded_box(f"ShoulderPlate.{l}",(s*.46,-.095,1.665),(.145,.055,.065),p["silver"],root,rot=(0,s*.12,s*.05),bevel=.035,subsurf=1)
    if level>=5:
        plate("ChestV",[(-.25,1.61),(0,1.45),(.25,1.61),(.18,1.67),(0,1.56),(-.18,1.67)],.028,p["gold"],root,.008,0).location.y=-.235
    if level>=6:
        uv("ChestMedallion",(0,-.255,1.49),(.050,.018,.060),p["gold"],root,20,12,0)
    if level>=8:
        uv("ChestCore",(0,-.274,1.49),(.035,.012,.047),p["glow"],root,18,10,0)
    if level>=9:
        for s,l in ((-1,"L"),(1,"R")):
            rounded_box(f"ShoulderGold.{l}",(s*.47,-.152,1.67),(.090,.012,.018),p["gold"],root,bevel=.007,subsurf=0)
    if level>=10:
        for s,l in ((-1,"L"),(1,"R")):
            rounded_box(f"ElitePauldron.{l}",(s*.505,-.020,1.70),(.145,.105,.050),p["darksteel"],root,rot=(0,s*.15,0),bevel=.040,subsurf=1)
            cone(f"ShoulderFin.{l}",(s*.615,-.005,1.74),.030,.004,.20,p["gold"],root,rot=(0,s*.70,0),vertices=12)
    if level>=12:
        for s,l in ((-1,"L"),(1,"R")):
            uv(f"ShoulderRune.{l}",(s*.49,-.155,1.68),(.028,.009,.035),p["glow"],root,16,8,0)
    if level>=15:
        torus("ChestMasterRing",(0,-.282,1.49),.085,.008,p["warmglow"],root,rot=(math.pi/2,0,0))


def build_legs(root,p,level):
    for s,l in ((-1,"L"),(1,"R")):
        hip=(s*.155,.0,1.02); thigh=(s*.175,-.005,.80); knee=(s*.185,-.015,.61); shin=(s*.19,-.025,.39); ankle=(s*.19,-.035,.18)
        tube(f"Leg.{l}",[hip,thigh,knee,shin,ankle],[.105,.112,.095,.082,.070],p["blue_dark"],root,16,.004,1)
        # boots shaped as two pieces for a less toy-like foot
        rounded_box(f"BootAnkle.{l}",(s*.19,-.060,.175),(.105,.105,.105),p["leather"],root,bevel=.040,subsurf=1)
        rounded_box(f"BootFoot.{l}",(s*.19,-.135,.075),(.115,.185,.070),p["leather2"],root,rot=(.06,0,0),bevel=.045,subsurf=1)
        if level>=4:
            rounded_box(f"Greave.{l}",(s*.19,-.105,.39),(.095,.060,.175),p["steel"],root,bevel=.050,subsurf=1)
            uv(f"Knee.{l}",(s*.185,-.125,.62),(.095,.055,.075),p["silver"],root,24,14,1)
        if level>=7:
            beam(f"GreaveLine.{l}",(s*.19,-.170,.50),(s*.19,-.170,.29),.012,.006,p["gold"],root)
        if level>=13:
            uv(f"KneeRune.{l}",(s*.185,-.183,.62),(.020,.008,.027),p["glow"],root,14,8,0)


def build_arms(root,p,level):
    # Sword arm hangs naturally downward; shield arm bends forward.
    right=[(.37,0,1.64),(.48,-.04,1.39),(.51,-.08,1.13)]
    left=[(-.37,0,1.64),(-.49,-.07,1.43),(-.52,-.19,1.23)]
    for pts,s,l in ((right,1,"R"),(left,-1,"L")):
        tube(f"UpperArm.{l}",pts[:2],[.088,.076],p["blue_dark"],root,16,.004,1)
        tube(f"Forearm.{l}",pts[1:],[.074,.058],p["skin"],root,16,.004,1)
        uv(f"Hand.{l}",pts[-1],(.061,.053,.067),p["skin_hi"],root,24,14,1)
        if level>=4:
            uv(f"ArmPlate.{l}",((pts[0][0]+pts[1][0])*.5,-.055,1.51),(.087,.065,.125),p["steel"],root,24,14,1)
        if level>=6:
            mid=((pts[1][0]+pts[2][0])*.5,(pts[1][1]+pts[2][1])*.5,(pts[1][2]+pts[2][2])*.5)
            tube(f"Bracer.{l}",[pts[1],mid],[.087,.075],p["silver"],root,16,.004,1)
        if level>=11:
            torus(f"WristRank.{l}",pts[-1],.063,.008,p["gold"],root,rot=(math.pi/2,0,0))


def build_helmet(root,p,level):
    build_head(root,p,level)
    # Concept direction: readable uncovered head through L10, elite helmet L11+.
    if level<11: return
    z=2.075
    uv("HelmBack",(0,.045,z+.085),(.170,.135,.145),p["darksteel"],root,30,18,1)
    rounded_box("HelmBrow",(0,-.150,z+.105),(.145,.025,.030),p["silver"],root,bevel=.020,subsurf=1)
    for s,l in ((-1,"L"),(1,"R")):
        plate(f"CheekGuard.{l}",[(s*.105,z+.04),(s*.150,z+.015),(s*.130,z-.095),(s*.085,z-.125)],.030,p["silver"],root,.015,1).location.y=-.128
    cone("CrownCrest",(0,.045,z+.34),.038,.005,.30,p["gold"],root,vertices=12)
    if level>=12:
        for s,l in ((-1,"L"),(1,"R")):
            cone(f"HelmWing.{l}",(s*.185,.025,z+.19),.028,.003,.22,p["gold"],root,rot=(0,s*.72,0),vertices=12)
            cone(f"HelmFeather.{l}",(s*.225,.035,z+.24),.020,.002,.18,p["silver"],root,rot=(0,s*.88,0),vertices=12)
    if level>=14:
        uv("HelmGem",(0,-.173,z+.115),(.024,.008,.034),p["glow"],root,14,8,0)


def build_cape(root,p,level):
    if level<7: return
    # Wavy cape surface behind the body.
    rows=8 if level>=12 else 7; cols=7
    verts=[]; faces=[]
    length=1.10 if level>=12 else .92
    for r in range(rows):
        t=r/(rows-1); z=1.68-t*length; y=.17+.08*t+.035*math.sin(t*math.pi)
        half=.30+.12*t
        for c in range(cols):
            u=c/(cols-1); x=(u-.5)*2*half
            wave=.025*math.sin(u*math.pi*2+t*2.5)
            verts.append((x,y+wave,z+.018*math.cos(u*math.pi)))
    for r in range(rows-1):
        for c in range(cols-1):
            a=r*cols+c;faces.append((a,a+1,a+1+cols,a+cols))
    cape=mesh_obj("Cape",verts,faces,p["blue"],root,.002,1,True)
    sol=cape.modifiers.new("CapeThickness","SOLIDIFY"); sol.thickness=.016
    rounded_box("CapeClasp",(0,.145,1.675),(.105,.035,.035),p["gold"],root,bevel=.020,subsurf=1)
    if level>=12:
        for s,i in ((-1,0),(0,1),(1,2)):
            uv(f"FurMantle.{i}",(s*.20,.115,1.68),(.20,.075,.075),p["whitefur"],root,24,14,1)


def shield_polygon(x,z,w,h):
    return [(x,z+h*.52),(x-w*.47,z+h*.30),(x-w*.44,z-h*.17),(x,z-h*.55),(x+w*.44,z-h*.17),(x+w*.47,z+h*.30)]


def extruded_poly(name,pts,y_front,y_back,mat,root,bevel=.030,subsurf=1):
    n=len(pts); verts=[(x,y_front,z) for x,z in pts]+[(x,y_back,z) for x,z in pts]
    faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    for i in range(n): faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
    return mesh_obj(name,verts,faces,mat,root,bevel,subsurf,False)


def build_shield(root,p,level):
    x,z=-.60,1.18
    w=.57+.018*max(0,level-3)+.015*max(0,level-10)
    h=1.07+.018*max(0,level-3)+.018*max(0,level-10)
    pts=shield_polygon(x,z,w,h)
    extruded_poly("ShieldBody",pts,-.34,-.25,p["darksteel"],root,.040,1)
    inset=shield_polygon(x,z,w*.90,h*.90)
    extruded_poly("ShieldFace",inset,-.365,-.345,p["blue"],root,.025,1)
    if level>=2:
        frame=shield_polygon(x,z,w*.98,h*.98); extruded_poly("ShieldGoldOuter",frame,-.385,-.370,p["gold"],root,.016,0)
        inner=shield_polygon(x,z,w*.88,h*.88); extruded_poly("ShieldBlueInset",inner,-.397,-.388,p["blue_light"],root,.012,0)
    # central 4-ray heraldic mark
    uv("ShieldBoss",(x,-.420,z+.035),(.065,.018,.085),p["gold"],root,20,12,1)
    if level>=5:
        for sx,sz,name in ((-.19,.17,"UL"),(.19,.17,"UR"),(-.17,-.19,"LL"),(.17,-.19,"LR")):
            beam("ShieldRay"+name,(x,-.420,z+.03),(x+sx*w,-.420,z+sz*h),.013,.006,p["gold"],root)
    if level>=8:
        uv("ShieldCrystal",(x,-.442,z+.035),(.040,.010,.060),p["glow"],root,16,8,0)
    if level>=9:
        torus("ShieldRune",(x,-.448,z+.035),.14,.009,p["glow"],root,rot=(math.pi/2,0,0))
    if level>=11:
        for s,l in ((-1,"L"),(1,"R")):
            cone(f"ShieldCrown.{l}",(x+s*w*.32,-.31,z+h*.42),.026,.002,.18,p["gold"],root,rot=(0,s*.44,0),vertices=12)
    if level>=13:
        torus("ShieldRune2",(x,-.454,z+.035),.21,.010,p["glow"],root,rot=(math.pi/2,.18,0))
    if level>=15:
        torus("ShieldMaster",(x,-.461,z+.035),.27,.010,p["warmglow"],root,rot=(math.pi/2,-.22,0))


def blade(name,start,end,width,mat,root,glowmat=None):
    s=Vector(start); e=Vector(end); d=(e-s).normalized(); side=Vector((1,0,0))
    if abs(d.dot(side))>.9: side=Vector((0,1,0))
    side=(d.cross(side)).normalized()*width; normal=(d.cross(side)).normalized()*.012
    tip=e+d*width*.9
    verts=[tuple(s-side-normal),tuple(s+side-normal),tuple(s+side+normal),tuple(s-side+normal),tuple(tip-normal*.4),tuple(tip+normal*.4)]
    faces=[(0,1,2,3),(0,4,1),(3,2,5),(0,3,5,4),(1,4,5,2)]
    return mesh_obj(name,verts,faces,mat,root,.008,0,False)


def build_sword(root,p,level):
    # Sword points downward/outward for a confident guardian stance.
    hand=Vector((.51,-.08,1.13)); grip_end=Vector((.58,-.085,.98)); blade_start=Vector((.60,-.09,.94))
    blade_end=Vector((.88,-.12,.18))
    tube("SwordGrip",[hand,grip_end],[.030,.030],p["leather"],root,12,.004,1)
    beam("SwordGuard",(.45,-.10,1.01),(.68,-.10,1.01),.024,.018,p["gold"],root)
    width=.045+.004*max(0,level-5)+.004*max(0,level-11)
    blade("SwordBlade",blade_start,blade_end,width,p["silver"],root)
    uv("SwordPommel",(.505,-.08,1.17),(.035,.025,.038),p["gold"],root,16,10,1)
    if level>=7:
        uv("SwordGem",(.60,-.115,.92),(.020,.007,.027),p["glow"],root,14,8,0)
    if level>=10:
        beam("SwordGoldSpine",(.63,-.113,.86),(.84,-.125,.29),.006,.004,p["gold"],root)
    if level>=14:
        beam("SwordEnergy",(.64,-.120,.84),(.85,-.132,.27),.006,.004,p["glow"],root)
    if level>=15:
        torus("SwordAura",(.84,-.13,.29),.075,.006,p["warmglow"],root,rot=(math.pi/2,.0,.35))


def build_late_fx(root,p,level):
    if level>=13:
        for s,l in ((-1,"L"),(1,"R")):
            cone(f"EnergyWing.{l}",(s*.59,.045,1.77),.024,.002,.19,p["glow"],root,rot=(0,s*.75,0),vertices=12)
    if level>=14:
        torus("BackRune",(0,.20,1.98),.29,.009,p["glow"],root,rot=(math.pi/2,0,0))
    if level>=15:
        torus("BackHaloGold",(0,.23,2.02),.36,.010,p["warmglow"],root,rot=(math.pi/2,.20,0))
        torus("GroundAura",(0,0,.045),.64,.014,p["glow"],root)


LEVEL_CHANGE={
1:"Recruit guardian — fitted blue tunic, leather boots, clean sword and shield",
2:"Gold-trimmed shield and tabard rank trim",
3:"Tapered steel cuirass and center plate",
4:"Layered pauldrons, arm plates and greaves",
5:"Gold chest V, shield heraldic rays",
6:"Bracers and guardian chest medallion",
7:"Flowing royal-blue cape, sword gem and greave lines",
8:"Azure chest core and shield crystal",
9:"Glowing shield rune and richer gold armor accents",
10:"Elite layered pauldrons, shoulder fins and sword gold spine",
11:"Open-face guardian helmet, wrist rank rings and crowned shield",
12:"Winged crest, white mantle and glowing shoulder runes",
13:"Second shield rune, knee runes and restrained energy wings",
14:"Back rune plus enchanted sword energy core",
15:"Master Guardian — radiant halo, master shield aura, sword aura and ground sigil",
}


def build(level):
    p=materials(level); r=root_empty()
    build_body(r,p,level); build_legs(r,p,level); build_arms(r,p,level); build_helmet(r,p,level)
    build_cape(r,p,level); build_shield(r,p,level); build_sword(r,p,level); build_late_fx(r,p,level)
    # modest scale increase only; progression comes from geometry/details.
    sc=1.0+.012*(level-1)/14; r.scale=(sc,sc,sc)
    return r


# ---------------------------------------------------------------------------
# Rendering / export
# ---------------------------------------------------------------------------
def bounds():
    pts=[]
    for o in bpy.context.scene.objects:
        if o.get(TAG) and o.type=='MESH':
            pts.extend(o.matrix_world@Vector(c) for c in o.bound_box)
    if not pts:return Vector((-1,-1,0)),Vector((1,1,2.3))
    return Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts))),Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))


def aim(o,target): o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()


def stage(size):
    mn,mx=bounds(); center=(mn+mx)*.5; center.z+=.04
    height=mx.z-mn.z; width=mx.x-mn.x
    # Heroic 3/4 camera similar to premium mobile character previews.
    bpy.ops.object.camera_add(location=(4.6,-8.2,3.05)); cam=bpy.context.object; cam.data.type='ORTHO'; cam.data.ortho_scale=max(2.65,height*1.18,width*1.18); aim(cam,center)
    scene=bpy.context.scene; scene.camera=cam
    try: scene.render.engine='BLENDER_EEVEE_NEXT'
    except Exception: scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=size;scene.render.resolution_y=size;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
    try: scene.view_settings.look='AgX - Medium High Contrast'
    except Exception: pass
    # large soft key + fill + strong edge light
    for name,loc,power,sz,col in [
        ("Key",(4.5,-5.0,6.3),850,4.2,(1.0,.90,.78)),
        ("Fill",(-4.5,-3.0,3.7),360,4.0,(.50,.68,1.0)),
        ("Rim",(2.5,4.2,5.4),1050,3.2,(.40,.62,1.0)),
        ("WarmRim",(-3.0,2.8,4.8),520,2.8,(1.0,.58,.28)),
    ]:
        bpy.ops.object.light_add(type='AREA',location=loc); l=bpy.context.object; l.name=name; l.data.energy=power; l.data.shape='DISK'; l.data.size=sz; l.data.color=col; aim(l,center)
    scene.world.color=(.004,.007,.014)
    try:
        scene.eevee.taa_render_samples=96
        scene.eevee.use_gtao=True;scene.eevee.gtao_distance=3;scene.eevee.gtao_factor=1.15
    except Exception: pass


def generate(level,out,size,save_blend):
    base.clear_scene(); root=build(level); root.name=f"troop_guardian_L{level:02d}"; root["unit_id"]="guardian";root["level"]=level;root["name"]="Guardian"
    stage(size)
    folder=out/"guardian"/f"level-{level:02d}";folder.mkdir(parents=True,exist_ok=True)
    glb=folder/f"guardian-level-{level:02d}.glb";png=folder/f"guardian-level-{level:02d}.png"
    base.export_glb(glb);bpy.context.scene.render.filepath=str(png);bpy.ops.render.render(write_still=True)
    blend=None
    if save_blend:
        blend=folder/f"guardian-level-{level:02d}.blend";bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    meta={"generator":"guardian-v3","id":"guardian","name":"Guardian","level":level,"max_level":15,
          "role":"frontline defensive melee","design":"original premium smooth blue/silver/gold guardian",
          "progression_change":LEVEL_CHANGE[level],"glb":glb.name,"preview":png.name,"blend":blend.name if blend else None}
    (folder/"metadata.json").write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return meta


def main():
    a=args(); levels=parse_levels(a.levels); out=Path(a.output).resolve(); items=[]
    for lv in levels:
        print(f"[Guardian v3] L{lv:02d}/15 — {LEVEL_CHANGE[lv]}",flush=True)
        items.append(generate(lv,out,a.preview_size,a.save_blend))
    out.mkdir(parents=True,exist_ok=True)
    (out/"manifest.json").write_text(json.dumps({"generator":"tools/blender/generate_guardian_v3.py","unit":"guardian","assets":items},indent=2),encoding='utf-8')
    print(f"Generated {len(items)} Guardian v3 level assets -> {out}",flush=True)


if __name__=='__main__': main()
