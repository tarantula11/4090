# 4090

## Blender toon storyboard renderer
Use `render_toon_storyboard.py` to build toon-style storyboard frames for **TERMINATOR T-2045: BLOCKCHAIN MELTDOWN**. The script constructs the entire scene from scratch (factory reset, world/camera, toon lights, toon materials, characters, speech bubbles, and Freestyle outlines) so no `.blend` starter file is required.

Run in Blender (headless or GUI):
```bash
blender -b -P render_toon_storyboard.py
```
Frames render to `./renders/panel_XX.png` alongside your working directory.

Quick syntax check without Blender (verifies the file parses):
```bash
python -m compileall render_toon_storyboard.py
```

### Authoring your own panels

1. Create a `scripts/` folder next to `render_toon_storyboard.py`.
2. Add numbered `.txt` files (e.g., `panel_01.txt`, `panel_02.txt`).
3. Put the panel title on the first line and the panel dialogue/action on the following lines. Blank lines are ignored.

When the folder exists, the renderer will render your custom files in alphabetical order. If no files are present, it falls back to the built-in Terminator T-2045 storyboard text.

### Included sample script

This repository ships with a prewritten **TERMINATOR T-2045** storyboard under `scripts/` (cover + pages 1–20). You can use it as-is to generate panels or as a template for your own `.txt` files.

### Bootstrap a 12-scene production file

Kickstart a full T-2045 project file (12 scenes with cameras, collections, Eevee settings, and camera markers) using the bootstrapper:

```bash
blender -b -P tools/bootstrap_t2045_project.py
```

Each scene receives Characters/Environment/Props/FX/Lights/Audio collections, a shot-note text block, three placeholder cameras bound to markers, and toon-friendly Eevee defaults (AO, Bloom, SSR, Filmic grade). Edit within the generated `.blend` to drop in assets, animate, and render per scene.

### Quickly make scenes visible (avoid black renders)

The bootstrapper creates empty, unlit scenes on purpose. If you need fast non-black preview renders before adding assets, run the sanity helper to inject a bright world BG, a key area light, a ground plane, a placeholder cube (when empty), and a camera if missing:

```bash
blender -b your_project.blend -P tools/scene_sanity.py
```

### Batch-render every scene in a `.blend`

After you populate and animate the generated scenes, you can render them all in one pass. Each scene is rendered to its own folder under `./renders/<SceneName>/` by default. The renderer auto-picks/creates a camera per scene and skips the `MASTER` scene unless you disable it via `SKIP_MASTER=0`.

```bash
# Render all scenes to PNG sequences
blender -b your_project.blend -P tools/batch_render_scenes.py

# Override output, resolution, or include MASTER
OUT=/abs/path/renders RESX=1920 RESY=1080 SKIP_MASTER=0 \
  blender -b your_project.blend -P tools/batch_render_scenes.py
```

### Render MP4s per scene (H.264)

If you prefer final MP4s instead of PNG sequences, use the FFmpeg helper. It sets consistent Eevee defaults, assigns a camera per scene, and writes `<SceneName>.mp4` into per-scene folders.

```bash
# CRF mode (quality): lower CRF = better quality, larger files
OUT=/abs/path/renders CRF=18 PRESET=MEDIUM \
  blender -b your_project.blend -P tools/batch_render_scenes_mp4.py

# Bitrate mode (kbps): use when CRF is unset
OUT=/abs/path/renders VBR=12000 GOP=24 PRESET=FAST \
  blender -b your_project.blend -P tools/batch_render_scenes_mp4.py
```

Both batch renderers enforce Eevee/Filmic (AO, Bloom, SSR, soft shadows) before rendering each scene's frame range.

### One-command previs render (fix black/white or blown-out frames)

Run the all-in-one helper when you need immediately visible previs without hand-lighting or materials. It disables the compositor, applies Eevee/Filmic, adds a key light, tinted world, ground, optional backdrop, lightweight placeholders, and a camera that tracks the origin. It can output MP4 (H.264) or PNG sequences.

Examples:

```bash
# MP4, toon placeholders, darker BG tint
OUT=/abs/renders FORMAT=MP4 CRF=18 PRESET=GOOD APPLY_TOON=1 BG="#1e2230" \
  blender -b your_project.blend -P tools/t2045_all_in_one_v2.py

# PNG sequences at 1280x720, no toon look
OUT=/abs/renders FORMAT=PNG RESX=1280 RESY=720 APPLY_TOON=0 \
  blender -b your_project.blend -P tools/t2045_all_in_one_v2.py
```

Environment knobs:
- `BG` (hex) and `WORLD_INT` (float) set world color/intensity.
- `BACKDROP=0/1` toggles a rear card; `FOG=0/1` adds light volume scatter.
- `APPLY_TOON=0/1` applies a toon material and outline to placeholders.
- `SKIP_MASTER=0/1` skips the MASTER scene by default.

Scene placeholders (auto-added): S01 rocket, S02 sun, S03 ship, S09 portal, other scenes get labeled signs (e.g., “MAX STUPIDITY”).

### TTS audio import + rough lipsync

Drop WAVs under `audio/<SceneName>/` (matching scene names, e.g., `S01_Launch_At_Sun/001_intro.wav`). Then run:

```bash
AUDIO_DIR=/abs/path/audio JAW_KEY=JawOpen START=1 GAP=6 \
  blender -b your_project.blend -P tools/t2045_audio_lipsync.py
```

What it does:
- Adds 3D Speakers for each `.wav` in the scene folder
- Optionally drops VSE sound strips for waveform reference
- Bakes amplitude to the `JawOpen` shapekey on the first mesh in the scene for previs mouth flaps (change `JAW_KEY` to match your rig)
