# /tools/batch_render_scenes.py
# Render every scene in the current .blend to its own folder with consistent Eevee settings.
# Run: blender -b your_project.blend -P tools/batch_render_scenes.py
import os
import bpy

OUT = os.environ.get("OUT", "//renders")  # allow override: OUT=/abs/path
RESX = int(os.environ.get("RESX", "1920"))
RESY = int(os.environ.get("RESY", "1080"))
FPS = int(os.environ.get("FPS", "24"))
FMT = os.environ.get("FMT", "PNG")  # PNG, OPEN_EXR, FFMPEG (if ffmpeg codec set)


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


def render_all_scenes() -> None:
    for scn in bpy.data.scenes:
        bpy.context.window.scene = scn
        ensure_eevee(scn)
        subdir = os.path.join(OUT, scn.name)
        os.makedirs(subdir, exist_ok=True)
        scn.render.filepath = os.path.join(subdir, scn.name + "_")
        print(f"[Render] {scn.name}: {scn.frame_start}-{scn.frame_end} -> {subdir}")
        bpy.ops.render.render(animation=True)
    print("All scenes rendered.")


if __name__ == "__main__":
    render_all_scenes()
