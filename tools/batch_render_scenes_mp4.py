"""Render each scene to an MP4 (H.264) with Eevee settings and auto-camera safety.

Env overrides:
  OUT=/abs/path/renders  RESX=1920  RESY=1080  FPS=24
  CRF=18 (quality mode, lower=better) or VBR=12000 (kbps fallback if CRF unset)
  GOP=24  PRESET=MEDIUM  SKIP_MASTER=0|1

Run:
  blender -b your_project.blend -P tools/batch_render_scenes_mp4.py
"""
import os
import bpy

OUT = os.environ.get("OUT", "//renders")
RESX = int(os.environ.get("RESX", "1920"))
RESY = int(os.environ.get("RESY", "1080"))
FPS = int(os.environ.get("FPS", "24"))
CRF = os.environ.get("CRF")  # if set, overrides bitrate mode
VBR = int(os.environ.get("VBR", "12000"))  # kbps when CRF not set
GOP = int(os.environ.get("GOP", "24"))
PRESET = os.environ.get("PRESET", "MEDIUM")
SKIP_MASTER = os.environ.get("SKIP_MASTER", "1") not in ("0", "false", "False")


def ensure_eevee(scn: bpy.types.Scene) -> None:
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

    scn.render.image_settings.file_format = "FFMPEG"
    scn.render.ffmpeg.format = "MPEG4"
    scn.render.ffmpeg.codec = "H264"
    scn.render.ffmpeg.ffmpeg_preset = PRESET.upper()
    scn.render.ffmpeg.pixel_format = "YUV420P"
    scn.render.ffmpeg.use_max_b_frames = True
    scn.render.ffmpeg.gopsize = GOP
    scn.render.ffmpeg.audio_codec = "AAC"
    scn.render.ffmpeg.audio_bitrate = 192
    scn.render.ffmpeg.audio_channels = "STEREO"

    if CRF is not None and CRF != "":
        scn.render.ffmpeg.constant_rate_factor = "HIGH"
        if hasattr(scn.render.ffmpeg, "crf"):
            try:
                scn.render.ffmpeg.crf = int(CRF)
            except Exception:
                pass
    else:
        scn.render.ffmpeg.constant_rate_factor = "MEDIUM"
        scn.render.ffmpeg.video_bitrate = max(1000, VBR)


def ensure_camera(scn: bpy.types.Scene):
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
        scn.render.filepath = os.path.join(subdir, scn.name)
        print(f"[Render:MP4] {scn.name}: {scn.frame_start}-{scn.frame_end} -> {scn.render.filepath}.mp4 (camera: {cam.name})")
        bpy.ops.render.render(animation=True, scene=scn.name)
    print("All scenes rendered to MP4.")


if __name__ == "__main__":
    render_all_scenes()
