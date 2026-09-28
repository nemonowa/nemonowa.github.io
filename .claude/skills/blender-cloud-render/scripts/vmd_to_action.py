"""
MMDモーション(.vmd) -> Blenderアクション 変換スクリプト

使い方:
  blender --background input.blend --python vmd_to_action.py -- input.vmd [root_object_name] [action_name]

- root_object_nameを省略した場合、シーン内のmmd_root(ROOT)オブジェクトを自動検出する。
- action_nameを省略した場合、インポート後にアーマチュアへ割り当てられたアクション名を
  そのまま使う(通常はVMDファイル名由来の名前になる)。指定した場合はインポート後に
  リネームする。
- 変換後は元の.blendに上書き保存する。別名保存したい場合はこのスクリプトの後段で
  bpy.ops.wm.save_as_mainfile(filepath=...)を呼ぶこと。

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
    if len(argv) < 1:
        raise SystemExit(
            "使い方: blender --background input.blend --python vmd_to_action.py -- input.vmd [root_object_name] [action_name]"
        )
    vmd_path = os.path.abspath(argv[0])
    root_name = argv[1] if len(argv) > 1 else None
    action_name = argv[2] if len(argv) > 2 else None
    return vmd_path, root_name, action_name


def find_root_object(root_name):
    if root_name:
        obj = bpy.data.objects.get(root_name)
        if obj is None:
            raise SystemExit(f"指定されたrootオブジェクトが見つかりません: {root_name}")
        if obj.mmd_type != "ROOT":
            raise SystemExit(f"指定オブジェクトはmmd_root(ROOT)ではありません: {root_name}")
        return obj

    roots = [o for o in bpy.data.objects if o.mmd_type == "ROOT"]
    if len(roots) == 0:
        raise SystemExit("シーン内にmmd_root(ROOT)オブジェクトが見つかりません。")
    if len(roots) > 1:
        names = ", ".join(o.name for o in roots)
        raise SystemExit(f"mmd_rootが複数見つかりました。root_object_nameで明示指定してください: {names}")
    return roots[0]


def find_armature_and_mesh(root_obj):
    children = [o for o in bpy.data.objects if o.parent == root_obj]
    arm_obj = next((o for o in children if o.type == "ARMATURE"), None)
    mesh_obj = next((o for o in children if o.type == "MESH"), None)
    if arm_obj is None:
        raise SystemExit(f"{root_obj.name}の子にアーマチュアが見つかりません。")
    return arm_obj, mesh_obj


def main():
    vmd_path, root_name, action_name = parse_args()

    if not os.path.exists(vmd_path):
        raise SystemExit(f"入力ファイルが見つかりません: {vmd_path}")

    ok = bpy.ops.preferences.addon_enable(module="mmd_tools")
    if "FINISHED" not in ok:
        raise SystemExit("mmd_toolsアドオンの有効化に失敗しました。導入状態を確認してください。")

    root_obj = find_root_object(root_name)
    arm_obj, mesh_obj = find_armature_and_mesh(root_obj)

    bpy.ops.object.select_all(action="DESELECT")
    arm_obj.hide_set(False)  # 非表示(eyeアイコンoff)のままだとselect_set()が無視される
    arm_obj.select_set(True)
    if mesh_obj:
        mesh_obj.hide_set(False)
        mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    print(f"[vmd_to_action] importing: {vmd_path} -> armature: {arm_obj.name}")
    bpy.ops.mmd_tools.import_vmd(
        filepath=vmd_path,
        scale=1.0,
        margin=5,
        bone_mapper="BLENDER",
        rename_bones=False,
        use_underscore=False,
        dictionary="DISABLED",
        use_pose_mode=False,
        use_mirror=False,
        update_scene_settings=True,
        use_NLA=False,
    )

    if action_name and arm_obj.animation_data and arm_obj.animation_data.action:
        arm_obj.animation_data.action.name = action_name
        print(f"[vmd_to_action] renamed action to: {action_name}")

    blend_path = bpy.data.filepath
    if not blend_path:
        raise SystemExit("元の.blendファイルのパスが取得できません(ファイルを開いた状態で実行してください)。")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"[vmd_to_action] saved: {blend_path}")


if __name__ == "__main__":
    main()
