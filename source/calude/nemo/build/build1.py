import bpy, bmesh, sys, colorsys
import numpy as np
from mathutils import Vector
S=sys.argv[sys.argv.index("--")+1]
arm=bpy.data.objects["Armature"]
for pb in arm.pose.bones: pb.matrix_basis.identity()

# ---- 1. 不要物の削除 ----
for o in list(bpy.data.objects):
    if o.name in ("robo_arm","Icosphere","hair_tail") or o.type=="EMPTY":
        bpy.data.objects.remove(o)
wear=bpy.data.objects["wear"]
DROP={"backpack_metal","backpack_nm","backpack_plastic","green_emit","anim_logo"}
bm=bmesh.new(); bm.from_mesh(wear.data)
dels=[f for f in bm.faces if wear.data.materials[f.material_index].name in DROP or (wear.data.materials[f.material_index].name in("robo_face","glass") and f.calc_center_median().y>0.05)]
bmesh.ops.delete(bm,geom=dels,context="FACES")
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
bm.to_mesh(wear.data); bm.free()
bpy.context.view_layer.objects.active=arm; bpy.ops.object.mode_set(mode="EDIT")
eb=arm.data.edit_bones
for b in list(eb):
    if b.name.startswith(("bag","robo_","hair_tail")): eb.remove(b)
bpy.ops.object.mode_set(mode="OBJECT")

hr=bpy.data.objects["hair"]; bm=bmesh.new(); bm.from_mesh(hr.data)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if hr.data.materials[f.material_index].name=="huku_bake"],context="FACES")
bm.to_mesh(hr.data); bm.free()
# ---- 2. 等身調整(脚・胴を伸ばし肩幅を広げ、全体を1.76mへ) ----
ZA,ZH,ZN=0.09,0.74,1.29; KL,KT,SX=1.14,1.05,1.07
def smooth(e0,e1,x):
    t=min(max((x-e0)/(e1-e0),0),1); return t*t*(3-2*t)
def F(p):
    x,y,z=p
    w=smooth(0.55,0.78,z)*(1-smooth(1.27,1.33,z))
    ax=abs(x); nx=ax*SX if ax<=0.14 else ax+0.14*(SX-1)
    x=np.sign(x)*(ax+(nx-ax)*w)
    if z<=ZA: nz=z
    elif z<=ZH: nz=ZA+(z-ZA)*KL
    elif z<=ZN: nz=ZA+(ZH-ZA)*KL+(z-ZH)*KT
    else: nz=z+(ZH-ZA)*(KL-1)+(ZN-ZH)*(KT-1)
    return Vector((x,y,nz))
top=F((0,0,1.575)).z; K=1.76/top
G=lambda p: F(p)*K
for o in bpy.data.objects:
    if o.type!="MESH": continue
    me=o.data
    if me.shape_keys:
        for kb in me.shape_keys.key_blocks:
            for d in kb.data: d.co=G(d.co)
    for v in me.vertices: v.co=G(v.co)
    me.update()
bpy.ops.object.mode_set(mode="EDIT")
for b in arm.data.edit_bones:
    h,t=G(b.head),G(b.tail); b.head=h; b.tail=t
bpy.ops.object.mode_set(mode="OBJECT")

# ---- 3. テクスチャの色替え ----
def load(name):
    im=bpy.data.images[name]; a=np.array(im.pixels[:],dtype=np.float32).reshape(im.size[1],im.size[0],4)
    return im,a[::-1].copy()   # 上原点に
def store(im,a): im.pixels[:]=a[::-1].ravel(); im.pack()
def hsv(a):
    r,g,b=a[...,0],a[...,1],a[...,2]; mx=np.max(a[...,:3],-1); mn=np.min(a[...,:3],-1); d=mx-mn+1e-6
    h=np.where(mx==r,((g-b)/d)%6,np.where(mx==g,(b-r)/d+2,(r-g)/d+4))/6
    return h,np.where(mx>0,d/(mx+1e-6),0),mx
def lum(a): return a[...,0]*0.3+a[...,1]*0.59+a[...,2]*0.11
def tint(a,mask,col,ref=0.85,gamma=1.0):
    L=np.clip(lum(a)/ref,0,1.15)**gamma
    for c in range(3): a[...,c]=np.where(mask,col[c]*L,a[...,c])
H,W=1024,1024; yy,xx=np.mgrid[0:H,0:W]
# 服
im,a=load("wear"); h,s,v=hsv(a)
blue=(h>0.45)&(h<0.62)&(s>0.35)
shirt=(yy<470)&(xx<670); pants=(yy>=470)&(yy<890)&(xx<670); gear=xx>=670
GOLD=(0.85,0.60,0.18); RED=(0.62,0.03,0.05); PANTS=(0.07,0.07,0.09); GUN=(0.10,0.10,0.11)
tint(a,shirt&~blue,RED); tint(a,pants&~blue,PANTS); tint(a,gear&~blue,GUN,gamma=1.3)
tint(a,blue&~gear,GOLD,ref=0.55); tint(a,blue&gear,(1.0,0.05,0.04),ref=0.55)
tint(a,(yy>890)&(xx>400)&(xx<600),PANTS)  # 裾の紐
store(im,a)
# 肌を色白に
im,a=load("body"); h,s,v=hsv(a)
skin=(h<0.12)&(s<0.5)&(v>0.55)
for c in range(3): a[...,c]=np.where(skin,a[...,c]*0.9+0.1*np.max(a[...,:3],-1)+0.01,a[...,c])
store(im,a)
# 瞳を薄紫、眉を黒に
im,a=load("faceparts"); h,s,v=hsv(a)
eye=(yy>150)&(yy<700)&(s>0.15)&((h<0.2)|(h>0.9))
brow=(yy<215)&(s>0.1)
nh=np.full_like(h,0.76); ns=np.clip(s*0.55,0,0.5); nv=np.clip(v*1.12,0,1)
import colorsys
rgb=np.stack(np.vectorize(colorsys.hsv_to_rgb)(nh,ns,nv),-1)
for c in range(3): a[...,c]=np.where(eye&~brow,rgb[...,c],a[...,c])
for c in range(3): a[...,c]=np.where(brow,v*0.35,a[...,c])
store(im,a)

# ---- 4. 部位別マテリアル(義手・手袋・袖) ----
def mat(name,base,metal=0.0,rough=0.6,emit=None):
    m=bpy.data.materials.new(name); m.use_nodes=True; p=m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value=(*base,1); p.inputs["Metallic"].default_value=metal; p.inputs["Roughness"].default_value=rough
    return m
glove=mat("glove_black",(0.015,0.015,0.017),0.0,0.45)
sleeve=mat("sleeve_red",(0.46,0.02,0.035),0.0,0.65)
# 義手: 黒い装甲 + Voronoiのパネルラインが赤く発光
pro=mat("prosthetic",(0.02,0.02,0.025),0.85,0.3); nt=pro.node_tree; N=nt.nodes; Lk=nt.links
tc=N.new("ShaderNodeTexCoord"); vo=N.new("ShaderNodeTexVoronoi"); vo.feature="DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value=45
mr=N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value=0.0; mr.inputs["From Max"].default_value=0.025; mr.inputs["To Min"].default_value=1; mr.inputs["To Max"].default_value=0
Lk.new(tc.outputs["Generated"],vo.inputs["Vector"]); Lk.new(vo.outputs["Distance"],mr.inputs["Value"])
p=N["Principled BSDF"]; p.inputs["Emission Color"].default_value=(1,0.02,0.02,1)
Lk.new(mr.outputs["Result"],p.inputs["Emission Strength"])
shirt=mat("shirt_black",(0.02,0.02,0.025),0.0,0.6)
NECKZ=arm.data.bones["neck"].head_local.z
for m in (glove,sleeve,pro,shirt): wear.data.materials.append(m)
idx={m.name:i for i,m in enumerate(wear.data.materials)}
gname={g.index:g.name for g in wear.vertex_groups}
def dom(v):
    return gname[max(v.groups,key=lambda g:g.weight).group] if v.groups else ""
LEFT_LOW=("forearm.L","forearm.twist.L","hand.L","palm","f_","thumb")
me=wear.data
for f in me.polygons:
    mname=me.materials[f.material_index].name
    ds=[dom(me.vertices[i]) for i in f.vertices]; b=max(set(ds),key=ds.count)
    cx=f.center.x
    if mname in ("body_bake","body_nm","wear_metal","armgear_plastic") and cx>0 and (b.startswith(LEFT_LOW) and (b.endswith(".L"))):
        f.material_index=idx["prosthetic"] if mname in("body_bake","body_nm") else f.material_index
    elif mname in ("body_bake","body_nm") and cx<0 and b.endswith(".R") and b.startswith(("hand","palm","f_","thumb")):
        f.material_index=idx["glove_black"]
    elif mname=="huku_bake" and any((0.17<me.uv_layers.active.data[li].uv.x<0.23 or 0.43<me.uv_layers.active.data[li].uv.x<0.48) and me.uv_layers.active.data[li].uv.y>0.95 for li in f.loop_indices) and f.center.y<-0.03:
        for li in f.loop_indices: me.uv_layers.active.data[li].uv=(0.117,0.805)   # 胸のヘックスロゴ→服の無地部分を参照
    elif mname=="body_bake" and b in("chest","spine","neck","shoulder.L","shoulder.R") and f.center.z<NECKZ-0.015:
        f.material_index=idx["shirt_black"] if f.center.z>NECKZ-0.09 else idx["sleeve_red"]   # 襟元は黒インナー、胸の窓(ロゴ)は赤
    elif mname=="body_nm":
        f.material_index=idx["sleeve_red"]
# 装備の金属・ガラスも義手意匠に
for n,(c,e) in {"wear_metal":((0.05,0.05,0.055),None),"armgear_plastic":((0.03,0.03,0.035),None),"glass":((0.3,0,0),(1,0.03,0.02)),"robo_face":((0.02,0.02,0.02),None)}.items():
    m=bpy.data.materials[n]; p=m.node_tree.nodes.get("Principled BSDF")
    if not p: continue
    for l in list(p.inputs["Base Color"].links): m.node_tree.links.remove(l)
    p.inputs["Base Color"].default_value=(*c,1); p.inputs["Metallic"].default_value=0.8; p.inputs["Roughness"].default_value=0.35
    if e: p.inputs["Emission Color"].default_value=(*e,1); p.inputs["Emission Strength"].default_value=3
bpy.ops.wm.save_as_mainfile(filepath=S+"/nemo_s1.blend")
print("DONE height",max((o.matrix_world@Vector(c)).z for o in bpy.data.objects if o.type=="MESH" for c in o.bound_box))
