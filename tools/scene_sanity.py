"""Injects minimal lighting and geometry so scenes don't render black.

Adds/ensures per scene:
- World background set to a bright color
- One key area light
- A large ground plane
- A placeholder "HeroCube" if the scene has no other meshes
- A camera if missing

Run before batch rendering:
  blender -b your_project.blend -P tools/scene_sanity.py
"""
import bpy
from mathutils import Vector


def ensure_world(scn: bpy.types.Scene) -> None:
    if not scn.world:
        scn.world = bpy.data.worlds.new(f"{scn.name}_World")
    scn.world.use_nodes = True
    nt = scn.world.node_tree
    bg = nt.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.95, 0.96, 1.0, 1.0)
        bg.inputs[1].default_value = 1.2


def ensure_light(scn: bpy.types.Scene) -> None:
    if any(o.type == "LIGHT" for o in scn.objects):
        return
    data = bpy.data.lights.new(f"{scn.name}_Key", type="AREA")
    data.energy = 1500
    data.size = 3.0
    obj = bpy.data.objects.new(data.name, data)
    scn.collection.objects.link(obj)
    obj.location = (3.0, -6.0, 4.0)
    obj.rotation_euler = (1.2, 0.0, -0.4)


def mesh_from_pydata(name: str, verts, faces):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    return me


def ensure_ground(scn: bpy.types.Scene) -> None:
    if any(o.type == "MESH" and o.name.startswith("Ground") for o in scn.objects):
        return
    size = 40.0
    s = size * 0.5
    me = mesh_from_pydata("GroundMesh", [(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new("Ground", me)
    scn.collection.objects.link(obj)


def ensure_test_cube_if_empty(scn: bpy.types.Scene) -> None:
    has_mesh = any(o.type == "MESH" and o.name != "Ground" for o in scn.objects)
    if has_mesh:
        return
    s = 1.0
    verts = [Vector((x, y, z)) for x in (-s, s) for y in (-s, s) for z in (-s, s)]
    faces = [(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4), (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)]
    me = mesh_from_pydata("HeroCubeMesh", verts, faces)
    cube = bpy.data.objects.new("HeroCube", me)
    scn.collection.objects.link(cube)
    cube.location = (0, 0, 1.0)


def ensure_camera(scn: bpy.types.Scene):
    if scn.camera:
        return scn.camera
    for obj in scn.objects:
        if obj.type == "CAMERA":
            scn.camera = obj
            return scn.camera
    cam_data = bpy.data.cameras.new(f"{scn.name}_AutoCam")
    cam = bpy.data.objects.new(cam_data.name, cam_data)
    scn.collection.objects.link(cam)
    cam.location = (0.0, -10.0, 4.0)
    cam.rotation_euler = (1.2, 0.0, 0.0)
    scn.camera = cam
    return cam


def main() -> None:
    for scn in bpy.data.scenes:
        ensure_world(scn)
        ensure_light(scn)
        ensure_ground(scn)
        ensure_test_cube_if_empty(scn)
        ensure_camera(scn)
        print(f"[Sanity] {scn.name} ready")
    print("Scene sanity pass done.")


if __name__ == "__main__":
    main()
