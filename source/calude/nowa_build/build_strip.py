# Nowa着物版 工程1: 元の服(くらげスカート・内スカート・ビスチェ・手持ちフリル扇・脚のリボン・ブーツ)を撤去する。
# 顔・目・口・髪・肌・髪飾り(頭ボーンの服/宝石)・水着ボトム(下半身の小片)は残す。
# 撤去パーツに属する不要ボーン・剛体・ジョイント・表示枠も削除する。
# 使い方: blender -b nowa_orig.blend -P build_strip.py -- <作業ディレクトリ>
import bpy, bmesh, sys, collections
S=sys.argv[sys.argv.index("--")+1]
bpy.ops.preferences.addon_enable(module="mmd_tools")
bpy.context.preferences.filepaths.save_version=0
root=bpy.data.objects["Nowa_Mel_v1_2"]; arm=bpy.data.objects["Nowa_Mel_v1_2_arm"]; body=bpy.data.objects["Nowa_Mel_v1_2_mesh"]
me=body.data; gn={g.index:g.name for g in body.vertex_groups}
# ---------- 1. 連結成分ごとに残す/消すを判定(素材+支配的な骨のウェイト) ----------
# シェイプキー(表情モーフ)を保つため、編集モードのbmeshで面を消す
bpy.context.view_layer.objects.active=body; body.select_set(True)
bpy.ops.object.mode_set(mode="EDIT"); bm=bmesh.from_edit_mesh(me)
dl=bm.verts.layers.deform.active
seen=set(); kill=set(); stat=collections.Counter()
for f in bm.faces:
    if f in seen: continue
    st=[f]; seen.add(f); c=[]
    while st:
        x=st.pop(); c.append(x)
        for e in x.edges:
            for g in e.link_faces:
                if g not in seen: seen.add(g); st.append(g)
    m=c[0].material_index
    if m in (0,1,2,3,4,10): continue            # 顔・目・口・髪・肌・目の透過は全部残す
    bw=collections.Counter()
    for v in {v for f in c for v in f.verts}:
        for k,w in v[dl].items():
            if not gn[k].startswith("mmd"): bw[gn[k]]+=w
    dom=bw.most_common(1)[0][0]; zs=[v.co.z for f in c for v in f.verts]
    if dom=="head": continue                    # 髪飾り(くらげのお団子・宝石)は据え置き
    if m==7 and dom=="lower_body" and max(zs)<0.94: continue   # 水着ボトム(+腰の小さな紐)は残す
    kill.update(c); stat[m]+=len(c)
print("delete faces by material",dict(stat))
bmesh.ops.delete(bm,geom=list(kill),context="FACES")
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
bmesh.update_edit_mesh(me); bpy.ops.object.mode_set(mode="OBJECT")
print("mesh now",len(me.vertices),"verts",len(me.polygons),"faces","shape keys",len(me.shape_keys.key_blocks))
# 面を持たなくなった素材スロット(フリル/装身具/透過服)を外す
used={p.material_index for p in me.polygons}
for i in sorted(range(len(me.materials)),reverse=True):
    if i not in used:
        body.active_material_index=i; bpy.ops.object.material_slot_remove()
print("materials",[m.name for m in me.materials])
# ---------- 2. 対応する剛体・ジョイント・表示枠を先に削除(拘束がボーンを参照しているため) ----------
names=[b.name for b in arm.data.bones if b.name.startswith(("Skirt_","InnerSkirt_","RibbonFrill_","drop_"))]

rm_rb={o for o in bpy.data.objects if o.mmd_type=="RIGID_BODY" and (o.mmd_rigid.bone in names or o.name[4:].startswith(("下半身x1","下半身x2")))}
rm_j=[o for o in bpy.data.objects if o.mmd_type=="JOINT" and o.rigid_body_constraint and (o.rigid_body_constraint.object1 in rm_rb or o.rigid_body_constraint.object2 in rm_rb)]
for o in list(rm_j)+list(rm_rb): bpy.data.objects.remove(o,do_unlink=True)
fr=root.mmd_root.display_item_frames
for i in reversed(range(len(fr))):
    if fr[i].name in("内スカート","くらげスカート","その他"): fr.remove(i)
# ---------- 3. 不要ボーン(くらげスカート/内スカート/脚のリボン/しずく)を削除 ----------
for n in names:
    g=body.vertex_groups.get(n)
    if g: body.vertex_groups.remove(g)
bpy.context.view_layer.objects.active=arm; bpy.ops.object.mode_set(mode="EDIT")
for n in names: arm.data.edit_bones.remove(arm.data.edit_bones[n])
bpy.ops.object.mode_set(mode="OBJECT")
print("removed bones",len(names),"rigid",len(rm_rb),"joints",len(rm_j))
bpy.ops.wm.save_as_mainfile(filepath=S+"/nowa_s1.blend")
print("DONE1")
