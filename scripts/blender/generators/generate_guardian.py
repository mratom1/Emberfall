from pathlib import Path
import json
import math
import bpy

REPO = Path(__file__).resolve().parents[3]
BASE = REPO / "assets" / "characters" / "troops" / "guardian"
SOURCE = BASE / "source"
EXPORTS = BASE / "exports"
SOURCE.mkdir(parents=True, exist_ok=True)
EXPORTS.mkdir(parents=True, exist_ok=True)


def mat(name, color, metallic=0.0, roughness=0.55):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return m


def assign(obj, material):
    if obj.data and hasattr(obj.data, "materials"):
        obj.data.materials.append(material)


def tag(obj, bone):
    if obj.type == "MESH":
        vg = obj.vertex_groups.new(name=bone)
        vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    return obj


def box(name, loc, scale, material, bone, bevel=0.08, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    if bevel:
        mod = o.modifiers.new("SoftBevel", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    assign(o, material)
    return tag(o, bone)


def cylinder(name, loc, radius, depth, material, bone, verts=10, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    assign(o, material)
    return tag(o, bone)


def sphere(name, loc, scale, material, bone):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o, material)
    return tag(o, bone)


def blade(name, loc, length, width, thickness, material, bone):
    x = width * 0.5
    y = thickness * 0.5
    z0 = -length * 0.5
    z1 = length * 0.35
    z2 = length * 0.5
    verts = [
        (-x, -y, z0), (x, -y, z0), (x, y, z0), (-x, y, z0),
        (-x, -y, z1), (x, -y, z1), (x, y, z1), (-x, y, z1),
        (0, -y, z2), (0, y, z2),
    ]
    faces = [
        (0, 1, 2, 3), (0, 4, 5, 1), (3, 2, 6, 7),
        (0, 3, 7, 4), (1, 5, 6, 2), (4, 7, 9, 8),
        (5, 8, 9, 6), (4, 8, 5), (7, 6, 9)
    ]
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    o.location = loc
    assign(o, material)
    return tag(o, bone)


def shield(name, loc, width, height, depth, material, accent, bone):
    x = width * 0.5
    y = depth * 0.5
    z = height * 0.5
    verts = [
        (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z),
        (-x, -y, -z * 0.55), (x, -y, -z * 0.55), (x, y, -z * 0.55), (-x, y, -z * 0.55),
        (0, -y, -z), (0, y, -z),
    ]
    faces = [
        (0, 1, 2, 3), (0, 4, 5, 1), (3, 2, 6, 7), (0, 3, 7, 4),
        (1, 5, 6, 2), (4, 8, 5), (7, 6, 9), (4, 7, 9, 8), (5, 8, 9, 6)
    ]
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    o.location = loc
    assign(o, material)
    tag(o, bone)
    ridge = box(name + "_Ridge", (loc[0], loc[1] - depth * 0.62, loc[2]), (0.07, depth * 0.22, height * 0.43), accent, bone, bevel=0.025)
    return o, ridge


def create_armature():
    arm_data = bpy.data.armatures.new("GuardianRig")
    arm = bpy.data.objects.new("GuardianRig", arm_data)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    def bone(name, head, tail, parent=None):
        b = arm_data.edit_bones.new(name)
        b.head, b.tail = head, tail
        if parent:
            b.parent = arm_data.edit_bones[parent]
        return b

    bone("root", (0, 0, 0), (0, 0, 0.3))
    bone("pelvis", (0, 0, 0.65), (0, 0, 1.05), "root")
    bone("spine", (0, 0, 1.05), (0, 0, 1.85), "pelvis")
    bone("head", (0, 0, 1.85), (0, 0, 2.45), "spine")
    bone("upper_arm.L", (0.12, 0, 1.72), (0.62, 0, 1.55), "spine")
    bone("forearm.L", (0.62, 0, 1.55), (0.88, 0, 1.25), "upper_arm.L")
    bone("hand.L", (0.88, 0, 1.25), (0.95, 0, 1.12), "forearm.L")
    bone("upper_arm.R", (-0.12, 0, 1.72), (-0.62, 0, 1.55), "spine")
    bone("forearm.R", (-0.62, 0, 1.55), (-0.88, 0, 1.25), "upper_arm.R")
    bone("hand.R", (-0.88, 0, 1.25), (-0.95, 0, 1.12), "forearm.R")
    bone("thigh.L", (0.23, 0, 0.85), (0.23, 0, 0.38), "pelvis")
    bone("shin.L", (0.23, 0, 0.38), (0.23, 0, -0.18), "thigh.L")
    bone("thigh.R", (-0.23, 0, 0.85), (-0.23, 0, 0.38), "pelvis")
    bone("shin.R", (-0.23, 0, 0.38), (-0.23, 0, -0.18), "thigh.R")
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.show_in_front = True
    return arm


def build(level):
    bpy.ops.wm.read_factory_settings(use_empty=True)

    leather = mat("Leather", (0.16, 0.07, 0.035), 0.0, 0.72)
    cloth = mat("AshCloth", (0.12, 0.13, 0.14), 0.0, 0.86)
    skin = mat("Skin", (0.42, 0.22, 0.13), 0.0, 0.78)
    iron = mat("Iron", (0.22, 0.25, 0.27), 0.68, 0.30)
    steel = mat("Steel", (0.37, 0.42, 0.46), 0.82, 0.24)
    dark = mat("DarkPlate", (0.075, 0.09, 0.11), 0.88, 0.22)
    ember = mat("EmberAccent", (0.68, 0.16, 0.035), 0.35, 0.28)
    bronze = mat("Bronze", (0.45, 0.24, 0.08), 0.72, 0.30)

    arm = create_armature()
    meshes = []

    meshes += [
        box("Boot_L", (0.23, -0.03, -0.18), (0.18, 0.29, 0.14), leather, "shin.L", 0.05),
        box("Boot_R", (-0.23, -0.03, -0.18), (0.18, 0.29, 0.14), leather, "shin.R", 0.05),
        cylinder("Shin_L", (0.23, 0, 0.18), 0.15, 0.62, iron if level < 10 else dark, "shin.L", 8),
        cylinder("Shin_R", (-0.23, 0, 0.18), 0.15, 0.62, iron if level < 10 else dark, "shin.R", 8),
        cylinder("Thigh_L", (0.23, 0, 0.72), 0.19, 0.52, cloth, "thigh.L", 8),
        cylinder("Thigh_R", (-0.23, 0, 0.72), 0.19, 0.52, cloth, "thigh.R", 8),
        box("PelvisGuard", (0, 0, 0.92), (0.46, 0.27, 0.22), leather if level == 1 else iron, "pelvis", 0.09),
        box("Torso", (0, 0, 1.43), (0.48, 0.29, 0.50), cloth, "spine", 0.12),
        box("ChestPlate", (0, -0.06, 1.48), (0.52, 0.24, 0.39), iron if level == 1 else (steel if level == 5 else dark), "spine", 0.10),
        sphere("Head", (0, 0, 2.08), (0.29, 0.27, 0.34), skin, "head"),
        cylinder("UpperArm_L", (0.66, 0, 1.52), 0.14, 0.55, cloth, "upper_arm.L", 8, (0, math.radians(73), 0)),
        cylinder("UpperArm_R", (-0.66, 0, 1.52), 0.14, 0.55, cloth, "upper_arm.R", 8, (0, math.radians(-73), 0)),
        cylinder("Forearm_L", (0.90, 0, 1.24), 0.12, 0.42, leather, "forearm.L", 8, (0, math.radians(38), 0)),
        cylinder("Forearm_R", (-0.90, 0, 1.24), 0.12, 0.42, leather, "forearm.R", 8, (0, math.radians(-38), 0)),
    ]

    helmet_mat = iron if level == 1 else (steel if level == 5 else dark)
    meshes.append(box("Helmet", (0, 0.02, 2.22), (0.34, 0.30, 0.24), helmet_mat, "head", 0.10))
    meshes.append(box("HelmetBrow", (0, -0.29, 2.16), (0.35, 0.05, 0.07), bronze if level < 10 else ember, "head", 0.025))

    meshes.append(cylinder("SwordGrip", (-1.02, -0.04, 1.03), 0.055, 0.38, leather, "hand.R", 10))
    meshes.append(box("SwordGuard", (-1.02, -0.04, 1.20), (0.22, 0.06, 0.045), bronze, "hand.R", 0.025))
    sword_len = 1.12 if level == 1 else (1.34 if level == 5 else 1.52)
    meshes.append(blade("SwordBlade", (-1.02, -0.04, 1.72), sword_len, 0.22 if level < 10 else 0.28, 0.075, steel, "hand.R"))

    shield_main, shield_ridge = shield("GuardianShield", (1.05, -0.02, 1.32), 0.72 if level == 1 else 0.84, 1.18 if level == 1 else 1.36, 0.12, helmet_mat, ember if level >= 5 else bronze, "hand.L")
    meshes += [shield_main, shield_ridge]

    if level >= 5:
        meshes += [
            box("Pauldron_L", (0.56, 0, 1.74), (0.27, 0.34, 0.18), steel if level == 5 else dark, "upper_arm.L", 0.10),
            box("Pauldron_R", (-0.56, 0, 1.74), (0.27, 0.34, 0.18), steel if level == 5 else dark, "upper_arm.R", 0.10),
            box("WaistPlate_L", (0.34, 0, 0.93), (0.15, 0.24, 0.28), steel if level == 5 else dark, "pelvis", 0.06, (0, 0, math.radians(-8))),
            box("WaistPlate_R", (-0.34, 0, 0.93), (0.15, 0.24, 0.28), steel if level == 5 else dark, "pelvis", 0.06, (0, 0, math.radians(8))),
            box("ChestBand", (0, -0.255, 1.51), (0.40, 0.045, 0.075), bronze if level == 5 else ember, "spine", 0.02),
        ]

    if level >= 10:
        meshes += [
            box("CrestSpine", (0, 0.03, 2.55), (0.07, 0.13, 0.31), ember, "head", 0.035),
            box("KneeGuard_L", (0.23, -0.17, 0.42), (0.20, 0.08, 0.16), dark, "shin.L", 0.055),
            box("KneeGuard_R", (-0.23, -0.17, 0.42), (0.20, 0.08, 0.16), dark, "shin.R", 0.055),
            box("BackMantle", (0, 0.27, 1.52), (0.53, 0.08, 0.51), dark, "spine", 0.07),
            box("EmberCore", (0, -0.305, 1.55), (0.12, 0.035, 0.15), ember, "spine", 0.03, (0, 0, math.radians(45))),
        ]

    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    mesh_obj = bpy.context.object
    mesh_obj.name = f"Guardian_L{level}_Mesh"

    arm_mod = mesh_obj.modifiers.new("GuardianRig", "ARMATURE")
    arm_mod.object = arm
    mesh_obj.parent = arm

    for p in mesh_obj.data.polygons:
        p.use_smooth = False

    mesh_obj.data.calc_loop_triangles()
    tri_count = len(mesh_obj.data.loop_triangles)

    arm.select_set(True)
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm

    blend_path = SOURCE / f"guardian_l{level}.blend"
    glb_path = EXPORTS / f"guardian_l{level}.glb"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_animations=True,
    )

    return {
        "level": level,
        "triangles": tri_count,
        "blend": str(blend_path.relative_to(REPO)).replace("\\", "/"),
        "glb": str(glb_path.relative_to(REPO)).replace("\\", "/"),
        "geometry": {
            "level_1": "base cuirass, compact sword, tapered guardian shield",
            "level_5": "layered pauldrons, waist plates, longer sword, reinforced shield",
            "level_10": "dark plate mantle, knee guards, ember crest/core, largest sword and shield",
        }[f"level_{level}"],
    }


results = [build(level) for level in (1, 5, 10)]
manifest = {
    "troop": "guardian",
    "displayName": "Guardian",
    "concept": "Emberfall Gatewarden — an original broad-silhouette frontline swordsman built around a tapered shield, layered plate, and ember-forged crest.",
    "blender": bpy.app.version_string,
    "levels": results,
}
(BASE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(json.dumps(manifest, indent=2))
