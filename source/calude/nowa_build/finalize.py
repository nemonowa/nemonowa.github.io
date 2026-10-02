# 配布用の仕上げ: テクスチャ埋め込み、ソリッド表示でも色が出るようビューポート色とシェーディングを設定
import bpy,sys,numpy as np
bpy.ops.preferences.addon_enable(module='mmd_tools')
out=sys.argv[sys.argv.index("--")+1]
bpy.context.preferences.filepaths.save_version=0
try: bpy.ops.file.pack_all()
except RuntimeError as e: print('pack warn',e)
for m in bpy.data.materials:
    if m.mmd_material.alpha<0.999: m.blend_method='BLEND'; m.show_transparent_back=False   # PMX取り込みで戻ったHASHEDだと半透明の布がチラつくのでBLENDにする
    if not m.use_nodes: continue
    tex=[n.image for n in m.node_tree.nodes if n.type=="TEX_IMAGE" and n.image]
    if tex and tex[0].size[0] and tex[0].has_data:
        px=np.array(tex[0].pixels[:],np.float32).reshape(-1,4); px=px[px[:,3]>0.5] if (px[:,3]>0.5).any() else px
        m.diffuse_color=(*np.median(px[:,:3],0),1)
for sc in bpy.data.screens:
    for ar in sc.areas:
        for sp in ar.spaces:
            if sp.type=="VIEW_3D": sp.shading.color_type="TEXTURE"
bpy.context.scene.display.shading.color_type="TEXTURE"
import os; sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","nemo","build") if "nowa_build" in __file__ else os.path.dirname(os.path.abspath(__file__)))
import outfit_visibility; print("VIS",outfit_visibility.fix())
bpy.ops.wm.save_as_mainfile(filepath=out,compress=True)
