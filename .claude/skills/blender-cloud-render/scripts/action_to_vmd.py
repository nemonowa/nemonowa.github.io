"""
Blenderアクション -> MMDモーション(.vmd) 変換スクリプト

使い方:
  blender --background input.blend --python action_to_vmd.py -- output.vmd action_name [root_object_name]

- action_nameは必須(.blend内に複数アクションがあるのが通常なので自動検出はしない)。
  書き出し前に対象アーマチュアへそのアクションを割り当ててから実行する。
- root_object_nameを省略した場合、シーン内のmmd_root(ROOT)オブジェクトを自動検出する。
- フレームレンジはアクションのframe_range(実際に打たれているキーフレームの範囲)を
  そのままシーンのframe_start/frame_endに設定してから書き出す
  (use_frame_range=Trueでシーンのフレーム範囲がそのまま使われるため)。

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
            "使い方: blender --background input.blend --python action_to_vmd.py -- output.vmd action_name [root_object_name]"
        )
    vmd_path = os.path.abspath(argv[0])
    action_name = argv[1]
    root_name = argv[2] if len(argv) > 2 else None
    return vmd_path, action_name, root_name


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
    vmd_path, action_name, root_name = parse_args()

    action = bpy.data.actions.get(action_name)
    if action is None:
        names = ", ".join(a.name for a in bpy.data.actions)
        raise SystemExit(f"アクションが見つかりません: {action_name}(利用可能: {names})")

    ok = bpy.ops.preferences.addon_enable(module="mmd_tools")
    if "FINISHED" not in ok:
        raise SystemExit("mmd_toolsアドオンの有効化に失敗しました。導入状態を確認してください。")

    root_obj = find_root_object(root_name)
    arm_obj, mesh_obj = find_armature_and_mesh(root_obj)

    if arm_obj.animation_data is None:
        arm_obj.animation_data_create()
    arm_obj.animation_data.action = action

    frame_start, frame_end = (int(v) for v in action.frame_range)
    scene = bpy.context.scene
    scene.frame_start = frame_start
    scene.frame_end = frame_end
    print(f"[action_to_vmd] action: {action_name} frame_range: {frame_start}-{frame_end}")

    bpy.ops.object.select_all(action="DESELECT")
    arm_obj.hide_set(False)  # 非表示(eyeアイコンoff)のままだとselect_set()が無視される
    arm_obj.select_set(True)
    if mesh_obj:
        mesh_obj.hide_set(False)
        mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    os.makedirs(os.path.dirname(vmd_path), exist_ok=True)
    print(f"[action_to_vmd] exporting: {arm_obj.name} -> {vmd_path}")
    bpy.ops.mmd_tools.export_vmd(
        filepath=vmd_path,
        scale=1.0,
        use_pose_mode=False,
        use_frame_range=True,
    )
    print(f"[action_to_vmd] saved: {vmd_path}")


if __name__ == "__main__":
    main()
