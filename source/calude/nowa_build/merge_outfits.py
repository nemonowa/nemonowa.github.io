# 元のノア(通常)と着物版(PMX往復後)を1つの.blendにまとめ、コレクションで表示を切り替えられるようにする。
# 使い方: blender -b nowa_orig.blend -P merge_outfits.py -- 出力.blend "着物 (kimono)=rt_kimono.blend"
import bpy, sys
a=sys.argv[sys.argv.index("--")+1:]; out=a[0]; others=[x.split("=",1) for x in a[1:]]
bpy.context.preferences.filepaths.save_version=0
sc=bpy.context.scene
def coll(name):
    c=bpy.data.collections.new(name); sc.collection.children.link(c); return c
cA=coll("通常 (default)")
for o in list(sc.collection.all_objects):
    if o.type in("CAMERA","LIGHT"): continue
    # シーンコレクションから外して移すだけ。剛体ワールド/拘束のコレクションへの所属は残す(物理が壊れないように)
    if o.name in sc.collection.objects: sc.collection.objects.unlink(o)
    if o.name not in cA.objects: cA.objects.link(o)
lc=bpy.context.view_layer.layer_collection.children
counts=[len(cA.objects)]
for name,path in others:
    cB=coll(name)
    with bpy.data.libraries.load(path,link=False) as (src,dst): dst.objects=[n for n in src.objects]
    for o in dst.objects:
        if o is None or o.type in("CAMERA","LIGHT"): continue
        cB.objects.link(o)
    # 既定は通常だけ表示。着物はコレクションのチェックで表示切替
    cB.hide_viewport=True; cB.hide_render=True; lc[cB.name].hide_viewport=True
    counts.append(len(cB.objects))
bpy.ops.wm.save_as_mainfile(filepath=out)
print("DONEM",counts)
