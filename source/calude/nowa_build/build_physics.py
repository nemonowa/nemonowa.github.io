# Nowa着物版 工程3: 揺れ物の剛体+ジョイント(スカート8列x3節・袖左右3列x2節・帯の垂れ2本x3節)と表示枠。
# 先頭の節は親ボーンに追従(静的)、以降は物理演算(MMDの定番スカートの作り)。体(脚)の剛体とは衝突させ、スカートが脚を貫通しない。
# 使い方: blender -b nowa_s2.blend -P build_physics.py -- <出力.blend>
import bpy, sys, math
from mathutils import Vector, Euler, Matrix
OUTF=sys.argv[sys.argv.index("--")+1]
bpy.ops.preferences.addon_enable(module="mmd_tools")
bpy.context.preferences.filepaths.save_version=0
from mmd_tools.core.rigid_body import FnRigidBody, shapeType
from mmd_tools.core.model import FnModel
ctx=bpy.context
root=bpy.data.objects["Nowa_Mel_v1_2"]; arm=bpy.data.objects["Nowa_Mel_v1_2_arm"]
rg=FnModel.ensure_rigid_group_object(ctx,root); jg=FnModel.ensure_joint_group_object(ctx,root)
M=arm.matrix_world
Z=Vector((0,0,1))
def bone_pts(b):
    bb=arm.data.bones[b]; return M@bb.head_local, M@bb.tail_local
def frame_rot(y,zhint):
    """y: ボーン方向(Y軸), zhint: 板の法線の目安。x=y×z。YXZオイラーで返す。"""
    y=y.normalized(); x=y.cross(zhint)
    if x.length<1e-6: x=y.cross(Vector((0,1,0)))
    x.normalize(); z=x.cross(y).normalized()
    return Matrix((x,y,z)).transposed().to_euler("YXZ")
RB={}
def rigid(bname,shape,size,dyn,group,mask,mass,ld,ad,name,rot,loc=None,fric=0.5):
    h,t=bone_pts(bname)
    o=FnRigidBody.setup_rigid_body_object(obj=FnRigidBody.new_rigid_body_object(ctx,rg),shape_type=shapeType(shape),location=loc if loc is not None else (h+t)/2,rotation=rot,
        size=Vector(size),dynamics_type=dyn,name=name,name_e=bname,collision_group_number=group,collision_group_mask=mask,
        mass=mass,friction=fric,bounce=0.0,linear_damping=ld,angular_damping=ad,bone=bname)
    RB[bname]=o; return o
def joint(ra,rb,name,loc,rot_lim,spring_ang=(20,20,20),lin=0.0,spring_lin=(0,0,0)):
    FnRigidBody.setup_joint_object(obj=FnRigidBody.new_joint_object(ctx,jg,FnModel.get_empty_display_size(root)),name=name,name_e=name,
        location=loc,rotation=Euler((0,0,0)),rigid_a=ra,rigid_b=rb,maximum_location=Vector((lin,lin,lin)),minimum_location=Vector((-lin,-lin,-lin)),
        maximum_rotation=Euler(rot_lim),minimum_rotation=Euler([-x for x in rot_lim]),spring_angular=Vector(spring_ang),spring_linear=Vector(spring_lin))
# 親になる既存の剛体(ボーン追従)
exist={}
for o in bpy.data.objects:
    if o.mmd_type=="RIGID_BODY" and o.mmd_rigid.bone and o.mmd_rigid.type=="0": exist.setdefault(o.mmd_rigid.bone,o)
def mask(*no_hit):   # 指定グループとは衝突しない(True=衝突しない)
    m=[False]*16
    for g in no_hit: m[g]=True
    return m
G_SKIRT,G_SLEEVE,G_TAIL=6,7,8
MK_SKIRT=mask(G_SKIRT,G_SLEEVE,G_TAIL)        # スカートは体(グループ0)と衝突
MK_SLEEVE=mask(*range(16))                    # 袖の垂れは何とも衝突させない(腕に埋まって暴れないように)
MK_TAIL=mask(*[g for g in range(16) if g!=0]) # 帯の垂れは体(グループ0)とだけ衝突
# ---------- スカート ----------
cnt={"skirt":0,"sleeve":0,"tail":0}
for c in range(8):
    prev=None
    for s in range(3):
        bn=f"KSkirt_{c}_{s}"; h,t=bone_pts(bn); d=t-h; L=d.length
        out=Vector(((h+t).x,(h+t).y+0.005,0)).normalized()       # 外向き(軸は原点付近)
        rad=Vector(((h+t).x/2,(h+t).y/2,0)).length
        wid=2*math.pi*rad/8*0.55
        rot=frame_rot(d,out)
        o=rigid(bn,"BOX",(wid,L/2*0.9,0.010),0 if s==0 else 1,G_SKIRT,MK_SKIRT,[0.5,0.7,0.7][s],[0.9,0.8,0.7][s],[0.9,0.8,0.7][s],f"裾{c+1}_{s+1}",rot)
        cnt["skirt"]+=1
        if s==0: prev=o; continue
        joint(prev,o,f"裾{c+1}_{s+1}J",h,(math.radians(30),math.radians(8),math.radians(12)),spring_ang=(30,30,30)); prev=o
for c in range(7):          # 横のつながり(隣の列の同じ節どうし。ゆるく)
    for s in (1,2):
        a,b=RB[f"KSkirt_{c}_{s}"],RB[f"KSkirt_{c+1}_{s}"]
        joint(a,b,f"裾横{c+1}_{s+1}J",(a.location+b.location)/2,(0.5,0.5,0.5),spring_ang=(5,5,5),lin=0.02,spring_lin=(50,50,50))
# ---------- 袖 ----------
for sf,jp in (("L","左"),("R","右")):
    for k in range(3):
        par=exist.get("arm_"+sf if k==0 else "elbow_"+sf)
        prev=par
        for s in range(2):
            bn=f"KSleeve_{sf}_{k}_{s}"; h,t=bone_pts(bn); L=(t-h).length
            o=rigid(bn,"CAPSULE",(0.02,max(L-0.03,0.005),0),1,G_SLEEVE,MK_SLEEVE,0.3,0.8,0.9,f"{jp}袖{k+1}_{s+1}",Vector((0,0,1)).rotation_difference((t-h).normalized()).to_euler("YXZ"))   # カプセルの長軸はローカルZ
            joint(prev,o,f"{jp}袖{k+1}_{s+1}J",h,(math.radians(45),math.radians(10),math.radians(30)),spring_ang=(15,15,15)); prev=o; cnt["sleeve"]+=1
# ---------- 帯の垂れ ----------
for k in range(2):
    prev=None
    for s in range(3):
        bn=f"KObiTail_{k}_{s}"; h,t=bone_pts(bn); d=t-h; L=d.length
        o=rigid(bn,"BOX",(0.022,L/2*0.9,0.006),0 if s==0 else 1,G_TAIL,MK_TAIL,0.2,0.9,0.9,f"帯{k+1}_{s+1}",frame_rot(d,Vector((0,-1,0))))
        cnt["tail"]+=1
        if s==0: prev=o; continue
        joint(prev,o,f"帯{k+1}_{s+1}J",h,(math.radians(35),math.radians(8),math.radians(15)),spring_ang=(25,25,25)); prev=o
# ---------- 表示枠: 元データの項目名は取り込み前のPMXのボーン名(例:つま先.L)のままでボーンと対応せず書き出しで落ちるため、
# ボーン名(英語)で作り直す。新しい揺れ物の枠も追加する ----------
import os
fr=root.mmd_root.display_item_frames
names=[b.name for b in arm.data.bones]
hair=[n for n in names if n.startswith(("hair","twintail","ahoge","sidehair","fringe"))]
LR=lambda *bs:[f"{b}_{s}" for s in "LR" for b in bs]
TABLE={"センター":["center","groove"],"ＩＫ":LR("legIK","toeIK"),"目":["eyes","eye_L","eye_R"],"頭部":["neck","head"],
  "後髪根本":[n for n in hair if n.startswith("hair") and "_1_" in n],"後髪他":[n for n in hair if n.startswith("hair") and "_1_" not in n],
  "その他髪":[n for n in hair if not n.startswith("hair")],
  "上半身":["upper_body","upper_body2","bust_L","bust_R"],
  "上半身L":[f"{b}_L" for b in ("shoulderP","shoulder","arm","arm_twist","elbow","wrist_twist","wrist")],
  "上半身R":[f"{b}_R" for b in ("shoulderP","shoulder","arm","arm_twist","elbow","wrist_twist","wrist")],
  "指L":[n for n in names if n.endswith("_L") and n.startswith(("thumb","fore","middle","third","little"))],
  "指R":[n for n in names if n.endswith("_R") and n.startswith(("thumb","fore","middle","third","little"))],
  "下半身":["lower_body","hip_L","hip_R"]+LR("leg","knee","ankle","toe")}
for f in fr:
    if f.name in TABLE:
        f.data.clear()
        for bn in TABLE[f.name]:
            if bn in arm.data.bones: it=f.data.add(); it.type="BONE"; it.name=bn
# 取り込み前のWindowsパスのままのトゥーンテクスチャを、実在する tx/ のファイルへ付け替える(PMX書き出しでコピーされる)
TX=os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","ノア_Ver1.2","tx"))
for m in bpy.data.materials:
    tt=m.mmd_material.toon_texture
    if tt and ("\\" in tt or not os.path.exists(tt)):
        p=os.path.join(TX,tt.replace("\\","/").split("/")[-1])
        if os.path.exists(p): m.mmd_material.toon_texture=p
def frame(name,name_e,bones):
    f=fr.add(); f.name=name; f.name_e=name_e
    for bn in bones:
        it=f.data.add(); it.type="BONE"; it.name=bn
frame("着物スカート","kimono skirt",[f"KSkirt_{c}_{s}" for c in range(8) for s in range(3)])
frame("袖","sleeves",[f"KSleeve_{sf}_{k}_{s}" for sf in "LR" for k in range(3) for s in range(2)])
frame("帯","obi",[f"KObiTail_{k}_{s}" for k in range(2) for s in range(3)])
# 物理(剛体ワールド)のキャッシュ範囲
sc=ctx.scene; sc.frame_start=1; sc.frame_end=250
bpy.ops.wm.save_as_mainfile(filepath=OUTF)
print("DONEP rigid added",cnt,"total rigid",len([o for o in bpy.data.objects if o.mmd_type=="RIGID_BODY"]),"joints",len([o for o in bpy.data.objects if o.mmd_type=="JOINT"]))
