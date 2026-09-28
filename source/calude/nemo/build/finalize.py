# 配布用の仕上げ: テクスチャ埋め込み、ソリッド表示でも色が出るようビューポート色とシェーディングを設定
import bpy,sys,numpy as np
out=sys.argv[sys.argv.index("--")+1]
bpy.ops.file.pack_all()
for m in bpy.data.materials:
    if not m.use_nodes: continue
    tex=[n.image for n in m.node_tree.nodes if n.type=="TEX_IMAGE" and n.image]
    if tex and tex[0].size[0]:
        px=np.array(tex[0].pixels[:],np.float32).reshape(-1,4); px=px[px[:,3]>0.5] if (px[:,3]>0.5).any() else px
        m.diffuse_color=(*np.median(px[:,:3],0),1)
for sc in bpy.data.screens:
    for ar in sc.areas:
        for sp in ar.spaces:
            if sp.type=="VIEW_3D": sp.shading.color_type="TEXTURE"
bpy.context.scene.display.shading.color_type="TEXTURE"
bpy.ops.wm.save_as_mainfile(filepath=out,compress=True)
