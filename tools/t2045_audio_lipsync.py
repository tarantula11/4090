"""Quick TTS audio + lipsync helper for the T-2045 previs scenes.

What it does per scene (skips MASTER):
- Imports all .wav files from AUDIO_DIR/<SceneName>/ as 3D Speaker objects
- Places optional VSE sound strips so you can see waveforms later
- Bakes amplitude to a shapekey (default "JawOpen") on the first mesh in the scene
  so you get rough mouth flaps for previs playback

Expected folder layout:
    project/
      your_project.blend
      audio/
        S01_Launch_At_Sun/
          001_intro.wav
          002_scientist.wav
        S02_Slingshot_Powerup/
          001_robot.wav

Run (examples):
    AUDIO_DIR=/abs/path/audio JAW_KEY=JawOpen START=1 GAP=6 \
      blender -b your_project.blend -P tools/t2045_audio_lipsync.py
"""

import os
from pathlib import Path
import bpy


AUDIO_DIR = Path(os.environ.get("AUDIO_DIR", "//audio"))
JAW_KEY = os.environ.get("JAW_KEY", "JawOpen")
START_F = int(os.environ.get("START", "1"))
GAP_F = int(os.environ.get("GAP", "6"))


def ensure_speaker(scene: bpy.types.Scene, name: str, sound_path: Path) -> bpy.types.Object:
    sound = bpy.data.sounds.load(str(sound_path), check_existing=True)
    speaker_data = bpy.data.speakers.new(name)
    speaker_obj = bpy.data.objects.new(name, speaker_data)
    scene.collection.objects.link(speaker_obj)
    speaker_obj.data.sound = sound
    speaker_obj.location = (0, -5, 2)
    return speaker_obj


def get_or_create_shapekey(obj: bpy.types.Object, key_name: str):
    if obj.type != "MESH":
        return None
    if not obj.data.shape_keys:
        obj.shape_key_add(name="Basis", from_mix=False)
    key = obj.data.shape_keys.key_blocks.get(key_name)
    if key is None:
        key = obj.shape_key_add(name=key_name, from_mix=False)
    return key


def bake_sound_to_shapekey(obj: bpy.types.Object, key_name: str, sound_path: Path, frame_start: int) -> None:
    key = get_or_create_shapekey(obj, key_name)
    if not key:
        return
    bpy.context.view_layer.objects.active = obj
    key.value = 0.0
    key.keyframe_insert(data_path="value", frame=frame_start)
    try:
        bpy.ops.graph.sound_bake(
            filepath=str(sound_path),
            low=200.0,
            high=4000.0,
            attack=0.01,
            release=0.2,
            threshold=0.0,
            use_accumulate=False,
            use_additive=False,
        )
    except Exception as exc:  # pragma: no cover - depends on Blender environment
        print(f"[Warn] sound_bake failed on {obj.name}: {exc}")


def add_sound_strip(scene: bpy.types.Scene, wav: Path, frame_start: int) -> None:
    try:
        if scene.sequence_editor is None:
            scene.sequence_editor_create()
        scene.sequence_editor.sequences.new_sound(wav.stem, str(wav), 1, frame_start)
    except Exception as exc:  # pragma: no cover
        print(f"[Warn] VSE add failed: {exc}")


def main():
    if not AUDIO_DIR.exists():
        print(f"[Info] AUDIO_DIR not found: {AUDIO_DIR}")
        return

    for scene in bpy.data.scenes:
        if scene.name.upper() == "MASTER":
            continue
        scene_dir = AUDIO_DIR / scene.name
        if not scene_dir.exists():
            print(f"[Skip] No audio folder for {scene.name}: {scene_dir}")
            continue
        print(f"[Audio] Scene {scene.name} from {scene_dir}")

        frame_cursor = START_F
        mesh_target = next((obj for obj in scene.objects if obj.type == "MESH"), None)

        for wav in sorted(scene_dir.glob("*.wav")):
            speaker = ensure_speaker(scene, wav.stem, wav)
            add_sound_strip(scene, wav, frame_cursor)
            sound = speaker.data.sound
            duration = int(getattr(sound, "frame_duration", 48))

            if mesh_target:
                bake_sound_to_shapekey(mesh_target, JAW_KEY, wav, frame_cursor)

            frame_cursor += duration + GAP_F

    print("Audio import & lipsync bake complete.")


if __name__ == "__main__":
    main()
