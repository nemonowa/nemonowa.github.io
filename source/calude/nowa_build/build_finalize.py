# Nowa着物版 工程4: モデル名を付け、アニメ(待機モーション)を外してレスト姿勢に戻す(PMX書き出し用)。
# 使い方: blender -b nowa_s3.blend -P build_finalize.py -- <出力.blend>
import bpy, sys
OUTF=sys.argv[sys.argv.index("--")+1]
bpy.ops.preferences.addon_enable(module="mmd_tools")
bpy.context.preferences.filepaths.save_version=0
root=bpy.data.objects["Nowa_Mel_v1_2"]; arm=bpy.data.objects["Nowa_Mel_v1_2_arm"]
root.name="Nowa_Mel_kimono"; root.mmd_root.name="ノア・メル(着物)"; root.mmd_root.name_e="Nowa Mel (kimono)"
# 元データに付いている待機モーションのアクションが残っていると、書き出し時に腕がポーズ位置で出力されるため外してレストに戻す
if arm.animation_data: arm.animation_data.action=None
for p in arm.pose.bones:
    p.location=(0,0,0); p.rotation_quaternion=(1,0,0,0); p.rotation_euler=(0,0,0); p.scale=(1,1,1)
bpy.context.scene.frame_set(1)
root.hide_set(False)    # 非表示のままだとblend_to_mmd.pyのselect_setが効かずpollで落ちる
bpy.ops.wm.save_as_mainfile(filepath=OUTF)
print("DONEF")
