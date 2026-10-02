# 衣装コレクションと剛体・ジョイントの表示状態を、切り替えても崩れない形に整える(finalize.pyから読み込む)
# - 衣装の切替は目のアイコン(ビューレイヤーのhide_viewport)で行う。モニター(Collection.hide_viewport)や
#   除外(☑)を使うと目が効かなかったり、除外を外したときにオブジェクト単位の非表示(hide_set)が初期化される
# - 剛体・ジョイントは衣装ごとの子コレクション「物理」に移し、そのコレクションを目で隠す。
#   コレクション単位の非表示はファイルに保存され、親の衣装を切り替えても消えない(物理演算は止まらない)
import bpy

PHYS={"RIGID_BODY","JOINT","NON_COLLISION_CONSTRAINT","TRACK_TARGET"}

def fix(scene=None, active=0):
    sc=scene or bpy.context.scene
    vl=bpy.context.view_layer
    outfits=list(sc.collection.children)
    for i,c in enumerate(outfits):
        phys=[o for o in c.all_objects if getattr(o,"mmd_type","NONE") in PHYS]
        if phys:
            pc=next((ch for ch in c.children if ch.name.endswith("(physics)")),None)   # 再実行しても増やさない
            if pc is None: pc=bpy.data.collections.new(c.name.split(" ")[0]+" 物理 (physics)"); c.children.link(pc)
            inside={c,*c.children_recursive}   # 衣装の中のコレクションからだけ外す(RigidBodyWorld/RigidBodyConstraintsなど物理用の登録は残す)
            for o in phys:
                for u in list(o.users_collection):
                    if u is not pc and u in inside: u.objects.unlink(o)
                if o.name not in pc.objects: pc.objects.link(o)
        c.hide_viewport=False; c.hide_render=(i!=active)
        lc=vl.layer_collection.children[c.name]
        lc.exclude=False; lc.hide_viewport=(i!=active)
        for ch in lc.children:
            if ch.name.endswith("(physics)"):
                ch.exclude=False; ch.hide_viewport=True; ch.collection.hide_render=True
        for o in phys: o.hide_set(True)
        for o in c.all_objects:   # アーマチュア(ボーン表示)も既定で隠す。PMX往復で作った衣装は表示状態で読み込まれる
            if o.type=="ARMATURE": o.hide_set(True)
        r=[o for o in c.all_objects if getattr(o,"mmd_type","")=="ROOT"]
        for o in r:
            o.mmd_root.show_rigid_bodies=False; o.mmd_root.show_joints=False; o.mmd_root.show_temporary_objects=False; o.mmd_root.show_armature=False
    return [(c.name,len(c.all_objects)) for c in outfits]
