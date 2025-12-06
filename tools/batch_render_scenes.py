"""Batch render every scene in a .blend to PNG sequences with consistent Eevee settings.

- Auto-picks or creates a camera per scene (fixes "Cannot render, no camera").
- Skips the MASTER scene by default; disable via SKIP_MASTER=0.
- Headless-safe (does not rely on window context).

Run:
  blender -b your_project.blend -P tools/batch_render_scenes.py
  OUT=/abs/path/renders RESX=1920 RESY=1080 blender -b your_project.blend -P tools/batch_render_scenes.py
"""
import os
import bpy

OUT = os.environ.get("OUT", "//renders")
RESX = int(os.environ.get("RESX", "1920"))
RESY = int(os.environ.get("RESY", "1080"))
FPS = int(os.environ.get("FPS", "24"))
FMT = os.environ.get("FMT", "PNG")  # PNG, OPEN_EXR, FFMPEG (if ffmpeg codec set)
SKIP_MASTER = os.environ.get("SKIP_MASTER", "1") not in ("0", "false", "False")


def ensure_eevee(scn: bpy.types.Scene) -> None:
    """Apply toon-friendly Eevee settings and render size to the scene."""
    scn.render.engine = "BLENDER_EEVEE"
    scn.render.resolution_x = RESX
    scn.render.resolution_y = RESY
    scn.render.fps = FPS
    scn.view_settings.view_transform = "Filmic"
    scn.view_settings.look = "Medium High Contrast"
    scn.eevee.use_gtao = True
    scn.eevee.gtao_distance = 0.2
    scn.eevee.use_bloom = True
    scn.eevee.use_ssr = True
    scn.eevee.use_soft_shadows = True
    scn.render.image_settings.file_format = FMT


def ensure_camera(scn: bpy.types.Scene) -> bpy.types.Object:
    """Guarantee the scene has a camera by using markers, existing cameras, or auto-creating one."""
    if scn.camera:
        return scn.camera
    for marker in scn.timeline_markers:
        if marker.camera:
            scn.camera = marker.camera
            return scn.camera
    for obj in scn.objects:
        if obj.type == "CAMERA":
            scn.camera = obj
            return scn.camera
    cam_data = bpy.data.cameras.new(f"{scn.name}_AutoCam")
    cam = bpy.data.objects.new(cam_data.name, cam_data)
    scn.collection.objects.link(cam)
    cam.location = (0.0, -8.0, 2.0)
    cam.rotation_euler = (1.20, 0.0, 0.0)
    scn.camera = cam
    return cam


def render_all_scenes() -> None:
    base_out = bpy.path.abspath(OUT)
    for scn in bpy.data.scenes:
        if SKIP_MASTER and scn.name.upper() == "MASTER":
            print(f"[Skip] {scn.name} (MASTER)")
            continue
        ensure_eevee(scn)
        cam = ensure_camera(scn)
        subdir = os.path.join(base_out, scn.name)
        os.makedirs(subdir, exist_ok=True)
        scn.render.filepath = os.path.join(subdir, scn.name + "_")
        print(f"[Render] {scn.name}: {scn.frame_start}-{scn.frame_end} -> {subdir} (camera: {cam.name})")
        bpy.ops.render.render(animation=True, scene=scn.name)
    print("All scenes rendered.")


if __name__ == "__main__":
    render_all_scenes()
