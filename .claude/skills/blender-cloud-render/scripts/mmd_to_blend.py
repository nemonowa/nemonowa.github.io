"""
MMD(.pmx) -> Blender(.blend) 変換スクリプト

使い方:
  blender --background --python mmd_to_blend.py -- input.pmx output.blend [--scale 0.08]

前提: mmd_toolsアドオンが導入済みであること(cloud_setup_script.sh参照)。
"""
import sys
import os
import bpy

def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    if len(argv) < 2:
        raise SystemExit(
            "使い方: blender --background --python mmd_to_blend.py -- input.pmx output.blend [--scale 0.08]"
        )
    pmx_path = os.path.abspath(argv[0])
    blend_path = os.path.abspath(argv[1])
    scale = 0.08
    if "--scale" in argv:
        scale = float(argv[argv.index("--scale") + 1])
    return pmx_path, blend_path, scale


def main():
    pmx_path, blend_path, scale = parse_args()

    if not os.path.exists(pmx_path):
        raise SystemExit(f"入力ファイルが見つかりません: {pmx_path}")

    ok = bpy.ops.preferences.addon_enable(module="mmd_tools")
    if "FINISHED" not in ok:
        raise SystemExit("mmd_toolsアドオンの有効化に失敗しました。導入状態を確認してください。")

    # デフォルトシーンのCube等を除去してからインポート
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    print(f"[mmd_to_blend] importing: {pmx_path}")
    bpy.ops.mmd_tools.import_model(
        filepath=pmx_path,
        scale=scale,
        types={"MESH", "ARMATURE", "PHYSICS", "MORPHS", "DISPLAY"},
        clean_model=True,
        remove_doubles=False,
        fix_IK_links=False,
        apply_bone_fixed_axis=False,
        rename_bones=False,  # mmd_bone.name_e等の情報は保持したままリネームは別スクリプトで行う
        use_underscore=False,
        dictionary="DISABLED",
    )

    os.makedirs(os.path.dirname(blend_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"[mmd_to_blend] saved: {blend_path}")


if __name__ == "__main__":
    main()
