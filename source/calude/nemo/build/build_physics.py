# MMD物理: マントの揺れ物剛体(物理演算)+関節、体側の衝突用剛体(ボーン追従)
import bpy, sys, math
from mathutils import Vector, Euler, Matrix
S=sys.argv[sys.argv.index("--")+1]; OUTF=sys.argv[sys.argv.index("--")+2]
bpy.ops.preferences.addon_enable(module="mmd_tools")
from mmd_tools.core.rigid_body import FnRigidBody, shapeType
from mmd_tools.core.model import FnModel
ctx=bpy.context
root=[o for o in bpy.data.objects if o.mmd_type=="ROOT"][0]
arm=FnModel.find_armature_object(root)
rg=FnModel.ensure_rigid_group_object(ctx,root); jg=FnModel.ensure_joint_group_object(ctx,root)
M=arm.matrix_world
def bone_frame(b):
    h=M@b.head_local; t=M@b.tail_local; d=(t-h)
    rot=Vector((0,1,0)).rotation_difference(d.normalized()).to_euler("YXZ")   # カプセルはY軸方向
    return (h+t)/2,rot,d.length
mask_body=[False]*16; mask_cape=[False]*16; mask_cape[1]=True   # マント同士は衝突しない
RB={}
def rigid(bname,shape,size,dyn,group,mask,mass=1.0,ld=0.5,ad=0.5,name=None):
    b=arm.data.bones[bname]; loc,rot,L=bone_frame(b)
    o=FnRigidBody.setup_rigid_body_object(obj=FnRigidBody.new_rigid_body_object(ctx,rg),shape_type=shapeType(shape),location=loc,rotation=rot,
        size=Vector(size if size else (0.02,L,0.02)),dynamics_type=dyn,name=name or arm.pose.bones[bname].mmd_bone.name_j or bname,name_e=bname,
        collision_group_number=group,collision_group_mask=mask,mass=mass,friction=0.5,bounce=0.0,linear_damping=ld,angular_damping=ad,bone=bname)
    RB[bname]=o; return o
# 体の衝突用(ボーン追従=0)
for bn,r in (("upper_body2",0.145),("upper_body",0.135),("lower_body",0.15),("leg_L",0.07),("leg_R",0.07),("knee_L",0.055),("knee_R",0.055),("arm_L",0.05),("arm_R",0.05)):
    if bn in arm.data.bones:
        L=bone_frame(arm.data.bones[bn])[2]; rigid(bn,"CAPSULE",(r,max(L-r,0.02),0),0,0,mask_body,mass=1)
# マント(物理=1)。付け根の上位に胸の追従剛体を使う
caps=sorted([b.name for b in arm.data.bones if b.name.startswith("cape_")])
for bn in caps:
    L=bone_frame(arm.data.bones[bn])[2]; rigid(bn,"CAPSULE",(0.03,max(L-0.03,0.02),0),1,1,mask_cape,mass=0.3,ld=0.8,ad=0.9)
def joint(a,b,name,rot_lim):
    ra,rb=RB[a],RB[b]; loc=M@arm.data.bones[b].head_local
    FnRigidBody.setup_joint_object(obj=FnRigidBody.new_joint_object(ctx,jg,FnModel.get_empty_display_size(root)),name=name,name_e=name,
        location=loc,rotation=Euler((0,0,0)),rigid_a=ra,rigid_b=rb,maximum_location=Vector((0,0,0)),minimum_location=Vector((0,0,0)),
        maximum_rotation=Euler(rot_lim),minimum_rotation=Euler([-x for x in rot_lim]),spring_angular=Vector((20,20,20)),spring_linear=Vector((0,0,0)))
cols=sorted({int(n.split("_")[1]) for n in caps}); segs=sorted({int(n.split("_")[2]) for n in caps})
lim=(math.radians(35),math.radians(10),math.radians(20))
for c in cols:
    joint("upper_body2",f"cape_{c}_0",f"マント{c+1}_1J",(math.radians(12),math.radians(5),math.radians(8)))
    for s in segs[1:]: joint(f"cape_{c}_{s-1}",f"cape_{c}_{s}",f"マント{c+1}_{s+1}J",lim)
# 横のつながり(隣の列の同じ節どうし、ゆるく)
for c in cols[:-1]:
    for s in segs:
        a,b=f"cape_{c}_{s}",f"cape_{c+1}_{s}"; ra,rb=RB[a],RB[b]
        FnRigidBody.setup_joint_object(obj=FnRigidBody.new_joint_object(ctx,jg,FnModel.get_empty_display_size(root)),name=f"マント横{c+1}_{s+1}",name_e=f"cape_h{c}_{s}",
            location=(ra.location+rb.location)/2,rotation=Euler((0,0,0)),rigid_a=ra,rigid_b=rb,maximum_location=Vector((0.02,0.02,0.02)),minimum_location=Vector((-0.02,-0.02,-0.02)),
            maximum_rotation=Euler((0.5,0.5,0.5)),minimum_rotation=Euler((-0.5,-0.5,-0.5)),spring_angular=Vector((5,5,5)),spring_linear=Vector((50,50,50)))
# 表示枠にマントを追加
fr=root.mmd_root.display_item_frames.add(); fr.name="マント"; fr.name_e="cape"
for bn in caps:
    it=fr.data.add(); it.type="BONE"; it.name=bn
bpy.ops.wm.save_as_mainfile(filepath=OUTF)
print("DONEP rigid",len(RB),"joints",len(jg.children))
