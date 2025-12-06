"""
Batch-import assets into each scene for the T-2045 toon project.

Usage (from your project folder):
    ASSET_ROOT=/abs/path/assets blender -b your_project.blend -P tools/import_t2045_assets.py

Options (env):
    ASSET_ROOT   Root folder containing assets. Defaults to //assets next to the .blend.
    PER_SCENE    If set to 1 (default), imports assets from ASSET_ROOT/<SceneName>/ when present;
                 otherwise, imports everything in ASSET_ROOT into every scene.
    SKIP_MASTER  Skip the MASTER scene (default 1). Set to 0 to process MASTER.
    LINK_BLEND   If set to 1, link objects from .blend assets instead of appending.

Supported formats: .blend, .fbx, .obj, .glb, .gltf

For each scene, the script:
    * switches context to the scene
    * imports supported files from its asset folder
    * links new objects into an "Imported" child collection under that scene
    * prints a summary of how many files and objects were added
"""

import os
from pathlib import Path
from typing import Iterable

import bpy

SUPPORTED_EXTS = {".blend", ".fbx", ".obj", ".glb", ".gltf"}

ASSET_ROOT = Path(bpy.path.abspath(os.environ.get("ASSET_ROOT", "//assets")))
PER_SCENE = os.environ.get("PER_SCENE", "1") not in {"0", "false", "False"}
SKIP_MASTER = os.environ.get("SKIP_MASTER", "1") not in {"0", "false", "False"}
LINK_BLEND = os.environ.get("LINK_BLEND", "0") in {"1", "true", "True"}


def ensure_scene_context(scene: bpy.types.Scene) -> None:
    """Try to make the scene active for operator imports."""
    win = getattr(bpy.context, "window", None)
    if win is not None:
        try:
            win.scene = scene
        except Exception:
            pass


def ensure_import_collection(scene: bpy.types.Scene) -> bpy.types.Collection:
    """Return (or create) a child collection named Imported."""
    for child in scene.collection.children:
        if child.name == "Imported":
            return child
    col = bpy.data.collections.new("Imported")
    scene.collection.children.link(col)
    return col


def link_objects_to_collection(objs: Iterable[bpy.types.Object], collection: bpy.types.Collection) -> None:
    for obj in objs:
        if obj is None:
            continue
        if collection not in obj.users_collection:
            collection.objects.link(obj)


def import_blend(filepath: Path, target_collection: bpy.types.Collection) -> Iterable[bpy.types.Object]:
    imported = []
    with bpy.data.libraries.load(str(filepath), link=LINK_BLEND) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if name]
    for obj in data_to.objects:
        if obj is None:
            continue
        link_objects_to_collection([obj], target_collection)
        imported.append(obj)
    return imported


def import_with_operator(ext: str, filepath: Path) -> None:
    if ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(filepath))
    elif ext == ".obj":
        bpy.ops.import_scene.obj(filepath=str(filepath))
    elif ext in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=str(filepath))


def import_assets_for_scene(scene: bpy.types.Scene, folder: Path) -> None:
    if not folder.exists() or not any(folder.iterdir()):
        print(f"[Skip] {scene.name}: no assets in {folder}")
        return

    ensure_scene_context(scene)
    target_col = ensure_import_collection(scene)

    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS]
    if not files:
        print(f"[Skip] {scene.name}: supported assets not found in {folder}")
        return

    before = set(obj.name for obj in bpy.data.objects)
    imported_count = 0

    for fp in sorted(files):
        ext = fp.suffix.lower()
        print(f"[Import] {scene.name}: {fp.name}")
        try:
            if ext == ".blend":
                imported_objs = import_blend(fp, target_col)
                imported_count += len(imported_objs)
            else:
                import_with_operator(ext, fp)
        except Exception as exc:  # pragma: no cover - Blender-specific
            print(f"  [Warn] failed to import {fp.name}: {exc}")
            continue

    # Move any operator-imported objects into the target collection
    after = set(obj.name for obj in bpy.data.objects)
    new_names = after - before
    new_objs = [bpy.data.objects[name] for name in new_names if name in bpy.data.objects]
    link_objects_to_collection(new_objs, target_col)

    total = len(new_names) if imported_count == 0 else imported_count + len(new_names)
    print(f"[Done] {scene.name}: {total} new objects from {len(files)} file(s)")


def main() -> None:
    root = ASSET_ROOT
    if not root.exists():
        print(f"[Info] Asset root not found: {root}")
        return

    for scene in bpy.data.scenes:
        if SKIP_MASTER and scene.name.upper() == "MASTER":
            print(f"[Skip] {scene.name} (MASTER)")
            continue

        scene_folder = root / scene.name if PER_SCENE else root
        import_assets_for_scene(scene, scene_folder)

    print("Asset import pass complete.")


if __name__ == "__main__":
    main()
