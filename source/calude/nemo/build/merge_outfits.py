# 2つのMMDモデル(軍服/白礼装)を1つの.blendにまとめ、コレクションで表示を切り替えられるようにする
import bpy, sys
a=sys.argv[sys.argv.index("--")+1:]; other,out=a[0],a[1]
sc=bpy.context.scene
def coll(name):
    c=bpy.data.collections.new(name); sc.collection.children.link(c); return c
cA=coll("軍服 (military)"); cB=coll("白礼装 (formal)")
for o in list(sc.collection.all_objects):
    if o.type in("CAMERA","LIGHT"): continue
    for c in list(o.users_collection): c.objects.unlink(o)
    cA.objects.link(o)
with bpy.data.libraries.load(other,link=False) as (src,dst): dst.objects=[n for n in src.objects]
for o in dst.objects:
    if o is None or o.type in("CAMERA","LIGHT"): continue
    cB.objects.link(o)
# 既定は軍服を表示。白礼装はコレクションのチェックで表示切替
cB.hide_viewport=True; cB.hide_render=True
lc=bpy.context.view_layer.layer_collection.children
lc[cB.name].hide_viewport=True
bpy.ops.wm.save_as_mainfile(filepath=out)
print("DONEM",len(cA.objects),len(cB.objects))
