# 複数のMMDモデル(軍服/白礼装/赤コート)を1つの.blendにまとめ、コレクションで表示を切り替えられるようにする
# 使い方: blender -b 軍服.blend -P merge_outfits.py -- 出力.blend 名前1=追加1.blend [名前2=追加2.blend ...]
import bpy, sys
a=sys.argv[sys.argv.index("--")+1:]; out=a[0]; others=[x.split("=",1) for x in a[1:]]
sc=bpy.context.scene
def coll(name):
    c=bpy.data.collections.new(name); sc.collection.children.link(c); return c
cA=coll("軍服 (military)")
for o in list(sc.collection.all_objects):
    if o.type in("CAMERA","LIGHT"): continue
    for c in list(o.users_collection): c.objects.unlink(o)
    cA.objects.link(o)
for c in list(bpy.data.collections):   # 空になった既定コレクションを消す
    if c is not cA and not c.all_objects: bpy.data.collections.remove(c)
lc=bpy.context.view_layer.layer_collection.children
counts=[len(cA.objects)]
for name,path in others:
    cB=coll(name)
    with bpy.data.libraries.load(path,link=False) as (src,dst): dst.objects=[n for n in src.objects]
    for o in dst.objects:
        if o is None or o.type in("CAMERA","LIGHT"): continue
        cB.objects.link(o)
    # 既定は軍服だけ表示。ほかはコレクションのチェックで表示切替
    cB.hide_viewport=True; cB.hide_render=True; lc[cB.name].hide_viewport=True
    counts.append(len(cB.objects))
bpy.ops.wm.save_as_mainfile(filepath=out)
print("DONEM",counts)
