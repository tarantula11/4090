# /tools/bootstrap_t2045_project.py
# Run inside Blender: blender -b -P tools/bootstrap_t2045_project.py
import bpy

FPS = 24
SCENES = [
    ("S01_Launch_At_Sun", 240),
    ("S02_Slingshot_Powerup", 264),
    ("S03_Crash_Pandemic", 264),
    ("S04_Distance_Confusion", 240),
    ("S05_Blockchain_Shovel", 200),
    ("S06_Cyber_Heist", 300),
    ("S07_Rubber_Knife", 200),
    ("S08_Fishman_Costume", 220),
    ("S09_TimePolice_Showdown", 300),
    ("S10_Max_Stupidity_Mode", 220),
    ("S11_Final_Meme_Upload", 240),
    ("S12_The_End", 220),
]


def new_scene(name, length):
    scn = bpy.data.scenes.new(name)
    bpy.context.window.scene = scn

    # Eevee defaults (toon-friendly)
    scn.render.engine = "BLENDER_EEVEE"
    scn.render.resolution_x = 1920
    scn.render.resolution_y = 1080
    scn.render.fps = FPS
    scn.eevee.use_gtao = True
    scn.eevee.gtao_distance = 0.2
    scn.eevee.use_bloom = True
    scn.eevee.use_ssr = True
    scn.eevee.use_soft_shadows = True
    scn.view_settings.view_transform = "Filmic"
    scn.view_settings.look = "Medium High Contrast"
    scn.render.image_settings.file_format = "PNG"
    scn.frame_start = 1
    scn.frame_end = length

    # Collections
    for col in ("Characters", "Environment", "Props", "FX", "Lights", "Audio"):
        collection = bpy.data.collections.new(col)
        scn.collection.children.link(collection)

    # Camera
    cam_data = bpy.data.cameras.new(f"{name}_Cam")
    cam_obj = bpy.data.objects.new(f"{name}_Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    scn.camera = cam_obj
    cam_data.lens = 35

    # Camera markers (A, B, C placeholders)
    for i, lens in enumerate((35, 24, 50), start=0):
        if i == 0:
            cam = cam_obj
        else:
            cam_data_variant = bpy.data.cameras.new(f"{name}_Cam_{chr(ord('A') + i)}")
            cam = bpy.data.objects.new(cam_data_variant.name, cam_data_variant)
            bpy.context.scene.collection.objects.link(cam)
        cam.location = (0.0, -8.0 + i * 0.5, 2.0 + 0.2 * i)
        cam.rotation_euler = (1.20, 0.0, 0.0)
        cam.data.lens = lens
        frame = 1 + i * max(1, (length // 3))
        marker = scn.timeline_markers.new(f"SHOT_{chr(ord('A') + i)}", frame=frame)
        marker.camera = cam

    # Text "Shot Sheet" to keep notes in-file
    notes = bpy.data.texts.new(f"{name}_SHOT_NOTES")
    notes.write(
        "Shots:\n"
        "- A: Establish / Gag\n"
        "- B: Insert / UI / Reaction\n"
        "- C: Punchline / FX\n"
    )
    return scn


# Create a clean file with a “MASTER” first (optional)
bpy.ops.wm.read_factory_settings(use_empty=True)
master = bpy.context.scene
master.name = "MASTER"
master.render.engine = "BLENDER_EEVEE"

# Build all scenes
for scn_name, length in SCENES:
    new_scene(scn_name, length)

print("Bootstrap complete: Created", len(SCENES), "scenes.")
