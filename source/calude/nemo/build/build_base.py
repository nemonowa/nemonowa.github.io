# 土台の服: 黒Yシャツ(前立て・ボタン・カフス・折り襟)とコンバットズボン(カーゴポケット・ニーパッド)
import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
S=sys.argv[sys.argv.index("--")+1]
arm=bpy.data.objects["Armature"]; wear=bpy.data.objects["wear"]; me=wear.data
B=lambda n: arm.data.bones[n].head_local
def mat(name,base,metal=0.0,rough=0.6):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True
    p=m.node_tree.nodes["Principled BSDF"]; p.inputs["Base Color"].default_value=(*base,1); p.inputs["Metallic"].default_value=metal; p.inputs["Roughness"].default_value=rough
    return m
def midx(m):
    if m.name not in me.materials: me.materials.append(m)
    return list(me.materials).index(m)
import os
W=os.environ.get("NEMO_OUTFIT")=="white"   # 服装B(白礼装)
if W:
    SHIRT=mat("shirt_black",(0.02,0.02,0.025),0,0.6)   # 下地(肌の代わり)用
    PLACKET=mat("shirt_placket",(0.70,0.68,0.64),0,0.55)
    BTN=mat("shirt_button",(0.55,0.47,0.28),0.9,0.3)
    PANTS=mat("pants",(0.74,0.72,0.68),0,0.6); POCKET=mat("pants_pocket",(0.66,0.64,0.60),0,0.6)
else:
    SHIRT=mat("shirt_black",(0.018,0.018,0.022),0,0.45); PLACKET=mat("shirt_placket",(0.03,0.03,0.036),0,0.7)
    BTN=mat("shirt_button",(0.10,0.10,0.11),0.3,0.25)
    PANTS=mat("pants",(0.035,0.038,0.05),0,0.75); POCKET=mat("pants_pocket",(0.045,0.048,0.06),0,0.75)
PAD=mat("kneepad",(0.10,0.10,0.11),0.5,0.35); STRAP=mat("strap",(0.018,0.016,0.014),0.1,0.55)

bm=bmesh.new(); bm.from_mesh(me); dl=bm.verts.layers.deform.active
gname={g.index:g.name for g in wear.vertex_groups}
def dom(v):
    d=v[dl]; return gname[max(d.items(),key=lambda kv:kv[1])[0]] if d else ""
def fdom(f):
    ds=[dom(v) for v in f.verts]; return max(set(ds),key=ds.count)
MN=lambda f: me.materials[f.material_index].name
C=lambda f: f.calc_center_median()
KZ=B("shin.L").z; HZ=B("hips").z; NZ=B("neck").z

# ---- 1. 旧衣装の削除 ----
dels=[f for f in bm.faces if MN(f)=="huku_bake" or (MN(f) in("armgear_plastic","wear_metal","glass","robo_face") and C(f).x<0.3)]
bmesh.ops.delete(bm,geom=dels,context="FACES")
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
SKIN={"body_bake","sleeve_red","shirt_black"}
skin=[f for f in bm.faces if MN(f) in SKIN]
TORSO=("hips","spine","chest","neck","shoulder")
# 下地の肌は隙間から見えても目立たない色に
iS=midx(SHIRT); iP=midx(PANTS)
for f in skin:
    d=fdom(f)
    if d.startswith(("thigh","shin")) or (d.startswith("hips") and C(f).z<HZ): f.material_index=iP
    elif d.startswith(TORSO+("upper_arm","forearm.R","forearm.twist.R")) and C(f).z<NZ+0.01: f.material_index=iS

def shell(faces,off,mi,smooth=4):
    r=bmesh.ops.duplicate(bm,geom=faces)
    nf=[e for e in r["geom"] if isinstance(e,bmesh.types.BMFace)]
    nv=list({v for f in nf for v in f.verts})
    bmesh.ops.remove_doubles(bm,verts=nv,dist=0.003)   # 素体の島の境目(股・肩など)をつなぐ
    nf=[f for f in nf if f.is_valid]; nv=list({v for f in nf for v in f.verts})
    inner=[v for v in nv if not v.is_boundary]
    for _ in range(smooth): bmesh.ops.smooth_vert(bm,verts=inner,factor=0.5,use_axis_x=True,use_axis_y=True,use_axis_z=True)
    bm.normal_update(); nrm={v:v.normal.copy() for v in nv}
    for v in nv: v.co+=nrm[v]*off
    for f in nf: f.material_index=mi; f.smooth=True
    return nf
def cut(faces,co,no):
    faces=[f for f in faces if f.is_valid]
    g=list({v for f in faces for v in f.verts})+list({e for f in faces for e in f.edges})+faces
    r=bmesh.ops.bisect_plane(bm,geom=g,plane_co=co,plane_no=no)
def by_mat(mi): return [f for f in bm.faces if f.is_valid and f.material_index==mi]

# ---- 2. 黒Yシャツ(胴+両上腕+右前腕。裾はズボンに入れる) ----
def shirt_ok(f):
    c=C(f); d=fdom(f)
    return (d.startswith(TORSO+("upper_arm","forearm.R","forearm.twist.R")) and not d.startswith("neck")
            and c.z>HZ-0.02 and c.z<NZ-0.005)
iSh=midx(mat("shirt_outer",(0.76,0.74,0.70),0,0.55) if W else mat("shirt_outer",(0.022,0.022,0.027),0,0.8))
sh_src=[f for f in skin if shirt_ok(f)]
def in_v(c,m=0.0):   # 首元のY字開き(上ほど広い)。白礼装は詰め襟なので開けない
    if W: return False
    return c.y<-0.02 and c.z>NZ-0.07 and abs(c.x)<(0.003+0.45*(c.z-(NZ-0.07)))+m
shirt=shell(sh_src,0.006,iSh,2)
z0=NZ-0.07
for sx in (() if W else (1,-1)): cut(by_mat(iSh),Vector((sx*0.003,0,z0)),Vector((sx,0,-0.45)).normalized())
if not W: cut(by_mat(iSh),Vector((0,0,z0)),Vector((0,0,1)))
bmesh.ops.delete(bm,geom=[f for f in by_mat(iSh) if in_v(C(f))],context="FACES")
# 前立て(中心の帯)
for x in (-0.013,0.013): cut(by_mat(iSh),Vector((x,0,0)),Vector((1,0,0)))
iPk=midx(PLACKET)
for f in by_mat(iSh):
    c=C(f)
    if abs(c.x)<0.013 and c.y<-0.03: f.material_index=iPk
# 右手首のカフス
hr=B("hand.R")
cuff=[f for f in by_mat(iSh) if (C(f)-hr).length<0.075]
if cuff: shell(cuff,0.003,iPk,1)

# ---- 3. コンバットズボン(ゆったり、ウエストバンド) ----
pants_src=[f for f in bm.faces if f.is_valid and f.material_index==iP and (fdom(f).startswith(("thigh","shin")) or fdom(f).startswith("hips"))]
pants_src+= [f for f in skin if f.is_valid and fdom(f).startswith(("hips","spine")) and HZ-0.02<C(f).z<HZ+0.07 and f.material_index!=iSh]
iPo=midx(mat("pants_outer",(0.74,0.72,0.68),0,0.6) if W else mat("pants_outer",(0.035,0.038,0.05),0,0.75))
if W:   # 白礼装: 膝下の旧ブーツ面も元にして、足首まで1枚のズボンにする
    OLDN={"boot_red","boot_dark","gold"}
    pants_src+=[f for f in bm.faces if f.is_valid and me.materials[f.material_index].name in OLDN and 0.11<C(f).z<KZ and abs(C(f).x)<0.2]
pants_src=list(set(pants_src))
pants=shell(pants_src,0.008 if W else 0.012,iPo,6)
# 服の下になった肌は削除(透け防止)
bmesh.ops.delete(bm,geom=[f for f in set(sh_src)|set(pants_src) if f.is_valid and not in_v(C(f),0.02)],context="FACES")
for f in bm.faces:
    if f.is_valid and MN(f)=="shirt_black" and in_v(C(f),0.02): f.material_index=list(me.materials).index(bpy.data.materials["body_bake"])
cut(by_mat(iPo),Vector((0,0,HZ+0.035)),Vector((0,0,1)))
cut(by_mat(iPo),Vector((0,0,HZ+0.062)),Vector((0,0,1)))
bmesh.ops.delete(bm,geom=[f for f in by_mat(iPo) if C(f).z>HZ+0.062],context="FACES")
iWB=midx(POCKET)
for f in by_mat(iPo):
    if C(f).z>HZ+0.035: f.material_index=iWB
# ズボンの下端(膝下)を直線にそろえる(下はブーツ側のズボン色の面が続く)
if not W:
    cut(by_mat(iPo),Vector((0,0,KZ-0.05)),Vector((0,0,1)))
    bmesh.ops.delete(bm,geom=[f for f in by_mat(iPo) if C(f).z<KZ-0.05],context="FACES")
# シャツの袖口を骨に垂直な平面でそろえる(右: 手首、左: ひじ=義手の手前)
def arm_cut(mis,co,d):
    cut([f for f in bm.faces if f.is_valid and f.material_index in mis],co,d)
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.is_valid and f.material_index in mis and (C(f)-co).dot(d)>0 and (C(f)-co).length<0.15],context="FACES")
dR=(B("hand.R")-B("forearm.R")).normalized(); dL=(B("forearm.L")-B("upper_arm.L")).normalized()
arm_cut({iSh,midx(PLACKET)},B("hand.R")-dR*0.012,dR)
arm_cut({iSh,midx(PLACKET)},B("forearm.L")-dL*0.015,dL)
# 義手の上端をひじで直線にそろえる(袖の中に隠れる位置)
iPr=list(me.materials).index(bpy.data.materials["prosthetic"])
coP=B("forearm.L")+dL*0.004
cut([f for f in bm.faces if f.is_valid and f.material_index==iPr],coP,dL)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.is_valid and f.material_index==iPr and (C(f)-coP).dot(dL)<0 and (C(f)-coP).length<0.12],context="FACES")
# カーゴポケット(外もも)。白礼装にはない
for sd,s_ in (() if W else ((1,"L"),(-1,"R"))):
    k=B(f"shin.{s_}"); z0,z1=k.z+0.10,k.z+0.24
    region=[f for f in by_mat(iPo) if C(f).x*sd>0 and z0-0.03<C(f).z<z1+0.03]
    cx=sum(C(f).x for f in region)/max(1,len(region))
    for co,no in ((Vector((0,0,z0)),Vector((0,0,1))),(Vector((0,0,z1)),Vector((0,0,1))),(Vector((0,k.y-0.035,0)),Vector((0,1,0))),(Vector((0,k.y+0.035,0)),Vector((0,1,0)))):
        cut(by_mat(iPo),co,no)
    pk=[f for f in by_mat(iPo) if C(f).x*sd>abs(k.x)+0.035 and z0<C(f).z<z1 and abs(C(f).y-k.y)<0.035]
    if pk:
        shell(pk,0.006,iWB,1)
        flap=[f for f in by_mat(iWB) if C(f).x*sd>abs(k.x)+0.04 and z1-0.035<C(f).z<z1]
        if flap: shell(flap,0.004,iWB,0)
bm.to_mesh(me); bm.free()

# ---- 4. 小物: 襟・ボタン・ベルト通し・ニーパッド ----
def new_obj(name):
    o=bpy.data.objects.new(name,bpy.data.meshes.new(name)); bpy.context.scene.collection.objects.link(o); return o
dg=bpy.context.evaluated_depsgraph_get(); bvh=BVHTree.FromObject(wear,dg)
def front_hit(x,z,y0=-1):
    loc,n,_,_=bvh.ray_cast(Vector((x,y0,z)),Vector((0,1,0))); return loc,n
parts=[]
def piece(fn,m,bone,name):
    o=new_obj(name); b2=bmesh.new(); fn(b2); b2.to_mesh(o.data); b2.free(); o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth=True
    o.vertex_groups.new(name=bone).add(range(len(o.data.vertices)),1.0,"REPLACE"); parts.append(o)
if not W:
    # シャツ襟: 首回りの台襟 + 外へ折り返す襟(前は尖る)
    nk=B("neck"); ring=[v.co for v in me.vertices if abs(v.co.z-(nk.z-0.005))<0.008 and abs(v.co.x)<0.07]
    R=max(math.hypot(p.x,p.y-nk.y) for p in ring)+0.004
    def collar(b2):
        seg=40; gap=math.radians(40); rows=[]
        prof=[(nk.z-0.030,R),(nk.z+0.010,R+0.001),(nk.z+0.016,R+0.007),(nk.z-0.006,R+0.026),(nk.z-0.028,R+0.040)]
        for k in range(seg+1):
            t=-math.pi/2+gap/2+(2*math.pi-gap)*k/seg
            fr=max(0,math.cos(t-(-math.pi/2)))   # 前ほど1
            col=[]
            for j,(z,r) in enumerate(prof):
                if j>=3: z-=0.05*fr**4; r+=0.004*fr**4     # 前の襟先を下へ尖らせる
                col.append(b2.verts.new((r*math.cos(t),nk.y+r*math.sin(t)*0.95,z)))
            rows.append(col)
        for k in range(seg):
            for j in range(len(prof)-1):
                b2.faces.new((rows[k][j],rows[k+1][j],rows[k+1][j+1],rows[k][j+1]))
        bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=0.0025)
    piece(collar,PLACKET,"neck","shirt_collar")
    for i,z in enumerate(np.linspace(NZ-0.05,HZ+0.07,6)):
        loc,n=front_hit(0,z)
        if loc: piece(lambda b2,loc=loc: bmesh.ops.create_uvsphere(b2,u_segments=10,v_segments=6,radius=0.0045,matrix=Matrix.Translation(loc-Vector((0,0.0015,0)))@Matrix.Diagonal((1,0.45,1,1))),BTN,"chest" if z>1.2 else "spine",f"sbtn{i}")
if not W:
    # 首元のブローチ(金の楕円枠+ティールの宝石)をY字の下端に表面に沿わせて付ける
    loc,n=front_hit(0,NZ-0.066)
    if loc:
        rot=Vector((0,0,1)).rotation_difference(-n if n.y>0 else n).to_matrix().to_4x4()
        rot=Vector((0,0,1)).rotation_difference(Vector((0,-1,0.15)).normalized()).to_matrix().to_4x4()
        base=Matrix.Translation(loc+Vector((0,-0.003,0)))@rot
        def frame(b2):
            bmesh.ops.create_cone(b2,cap_ends=True,segments=24,radius1=0.016,radius2=0.013,depth=0.004,matrix=base@Matrix.Diagonal((0.8,1.1,1,1)))
        piece(frame,mat("gold",(0.70,0.45,0.12),0.7,0.35),"chest","brooch")
        def gem(b2):
            bmesh.ops.create_uvsphere(b2,u_segments=16,v_segments=10,radius=1,matrix=base@Matrix.Translation((0,0,0.003))@Matrix.Diagonal((0.0095,0.013,0.005,1)))
        piece(gem,mat("gem",(0.03,0.45,0.42),0.2,0.1),"chest","gem")
if not W:
    # ズボンのベルト+バックル
    P=[v.co for v in me.vertices if abs(v.co.z-(HZ+0.048))<0.01 and me.materials[0] is not None]
    def belt(b2):
        seg=48; rows=[]
        for zz in (HZ+0.034,HZ+0.062):
            r=[]
            for k in range(seg):
                t=2*math.pi*k/seg; d=Vector((math.sin(t),-math.cos(t),0))
                h,_,_,_=bvh.ray_cast(Vector((0,0.01,zz))+d*0.5,-d)
                p=(h if h else Vector((0,0.01,zz))+d*0.12)+d*0.004
                r.append(b2.verts.new(p))
            rows.append(r)
        for k in range(seg): b2.faces.new((rows[0][k],rows[0][(k+1)%seg],rows[1][(k+1)%seg],rows[1][k]))
        bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=0.003)
    piece(belt,STRAP,"hips","belt")
    loc,n=front_hit(0,HZ+0.048)
    if loc: piece(lambda b2: bmesh.ops.create_cube(b2,size=1,matrix=Matrix.Translation(loc-Vector((0,0.009,0)))@Matrix.Diagonal((0.045,0.006,0.034,1))),mat("buckle",(0.6,0.6,0.62),1.0,0.25),"hips","buckle")
if not W:
    # ベルト通し
    for ang in (-70,-30,30,70,150,210):
        t=math.radians(ang); d=Vector((math.sin(t),-math.cos(t),0))
        o=Vector((0,0.0,HZ+0.05))+d*0.5
        loc,n,_,_=bvh.ray_cast(o,-d)
        if loc: piece(lambda b2,loc=loc,d=d: bmesh.ops.create_cube(b2,size=1,matrix=Matrix.Translation(loc+d*0.002)@Matrix.Rotation(math.atan2(d.x,-d.y),4,'Z')@Matrix.Diagonal((0.012,0.004,0.04,1))),PANTS,"hips",f"loop{ang}")
if not W:
    # ニーパッド+留めベルト
    def legpts(z,sd): return [v.co for v in me.vertices if abs(v.co.z-z)<0.012 and (v.co.x>0)==(sd>0) and abs(v.co.x)<0.2]
    for s_,sd in (("L",1),("R",-1)):
        k=B(f"shin.{s_}"); loc,n=front_hit(k.x,k.z-0.005)
        if loc:
            def pad(b2,loc=loc):
                bmesh.ops.create_uvsphere(b2,u_segments=20,v_segments=12,radius=1.0)
                for v in list(b2.verts):
                    if v.co.y>0.15: b2.verts.remove(v)
                bmesh.ops.transform(b2,matrix=Matrix.Translation(loc+Vector((0,0.012,0)))@Matrix.Diagonal((0.052,0.028,0.07,1)),verts=b2.verts)
                bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=-0.004)
            piece(pad,PAD,f"shin.{s_}",f"kneepad{s_}")
        for zz,bone in ((k.z+0.075,f"thigh.{s_}"),(k.z-0.08,f"shin.{s_}")):
            c0=Vector((k.x,k.y,zz))
            def band(b2,c0=c0,zz=zz):
                seg=32; rows=[]
                for dz in (-0.009,0.009):
                    r=[]
                    for i in range(seg):
                        t=2*math.pi*i/seg; d=Vector((math.sin(t),-math.cos(t),0))
                        h,_,_,_=bvh.ray_cast(c0+Vector((0,0,dz))+d*0.2,-d)
                        r.append(b2.verts.new((h if h and (h-c0).length<0.12 else c0+d*0.06)+d*0.0035))
                    rows.append(r)
                for i in range(seg): b2.faces.new((rows[0][i],rows[0][(i+1)%seg],rows[1][(i+1)%seg],rows[1][i]))
                bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=0.003)
            piece(band,STRAP,bone,f"band{s_}{zz:.2f}")
if W:
    k=B("shin.R"); zz=k.z+0.20; c0=Vector((k.x,k.y,zz))
    def tband(b2):
        seg=32; rows=[]
        for dz in (-0.011,0.011):
            r=[]
            for i in range(seg):
                t=2*math.pi*i/seg; d=Vector((math.sin(t),-math.cos(t),0))
                h,_,_,_=bvh.ray_cast(c0+Vector((0,0,dz))+d*0.2,-d)
                r.append(b2.verts.new((h if h and (h-c0).length<0.12 else c0+d*0.07)+d*0.003))
            rows.append(r)
        for i in range(seg): b2.faces.new((rows[0][i],rows[0][(i+1)%seg],rows[1][(i+1)%seg],rows[1][i]))
        bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=0.003)
    piece(tband,STRAP,"thigh.R","thigh_belt")
    loc,n=front_hit(k.x-0.02,zz)
    if loc: piece(lambda b2: bmesh.ops.create_cube(b2,size=1,matrix=Matrix.Translation(loc-Vector((0,0.006,0)))@Matrix.Diagonal((0.022,0.006,0.026,1))),mat("buckle",(0.6,0.6,0.62),1.0,0.25),"thigh.R","thigh_buckle")
bpy.ops.object.select_all(action="DESELECT")
for o in parts: o.select_set(True)
wear.select_set(True); bpy.context.view_layer.objects.active=wear; bpy.ops.object.join()

# ---- 5. 戦闘用ブーツ(すね中丈・厚いゴム底・つま先補強・靴紐とアイレット)に作り直す ----
from mathutils.kdtree import KDTree
BOOT_TOP=0.12 if W else 0.21
if W:
    LEATHER=mat("boot_leather",(0.78,0.76,0.72),0,0.35); TOE=mat("boot_toecap",(0.80,0.78,0.74),0,0.25)
    SOLE=mat("boot_sole",(0.10,0.07,0.05),0,0.7); LACE=mat("boot_lace",(0.12,0.08,0.05),0,0.7)
else:
    LEATHER=mat("boot_leather",(0.016,0.015,0.015),0,0.5); TOE=mat("boot_toecap",(0.02,0.019,0.019),0,0.3)
    SOLE=mat("boot_sole",(0.03,0.03,0.03),0,0.85); LACE=mat("boot_lace",(0.012,0.012,0.012),0,0.7)
EYE=mat("boot_eyelet",(0.35,0.35,0.36),1.0,0.3); EYE=mat("boot_eyelet",(0.35,0.35,0.36),1.0,0.3)
EYE=mat("boot_eyelet",(0.35,0.35,0.36),1.0,0.3)
iLe,iTo,iSo=midx(LEATHER),midx(TOE),midx(SOLE)
bm=bmesh.new(); bm.from_mesh(me); dl=bm.verts.layers.deform.active
names=[m.name for m in me.materials]
OLD={names.index(n) for n in("boot_red","boot_dark","gold") if n in names}
legf=[f for f in bm.faces if f.calc_center_median().z<BOOT_TOP+0.03 and all(abs(v.co.x)<0.2 for v in f.verts) and (f.material_index in OLD or f.material_index==iPo or me.materials[f.material_index].name in ("body_bake","pants"))]
src=[(v.co.copy(),dict(v[dl])) for v in {v for f in legf for v in f.verts}]
kd=KDTree(len(src))
for i,(co,_) in enumerate(src): kd.insert(co,i)
kd.balance()
bmesh.ops.delete(bm,geom=[f for f in legf if f.calc_center_median().z<BOOT_TOP],context="FACES")
for f in bm.faces:   # 旧ブーツ面・脚に残った肌のうち筒より上はズボン色に
    if f.is_valid and (f.material_index in OLD or (me.materials[f.material_index].name=="body_bake" and f.calc_center_median().z<KZ and abs(f.calc_center_median().x)<0.2)): f.material_index=iPo
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
bm.to_mesh(me); bm.free()
boots_info={}; boot_objs=[]
def mk(name,fn):
    o=bpy.data.objects.new(name,bpy.data.meshes.new(name)); bpy.context.scene.collection.objects.link(o)
    b2=bmesh.new(); fn(b2); bmesh.ops.recalc_face_normals(b2,faces=b2.faces[:]); b2.to_mesh(o.data); b2.free(); return o
for s_,sd in (("L",1),("R",-1)):
    foot=[co for co,_ in src if co.x*sd>0 and co.z<0.10]
    cx=sum(p.x for p in foot)/len(foot)
    toe_y=min(p.y for p in foot); heel_y=max(p.y for p in foot)
    ZB=0.018 if W else 0.028; L=heel_y-toe_y
    def halfw(y):
        W=[abs(p.x-cx) for p in foot if abs(p.y-y)<0.025]
        return (max(W) if W else 0.04)*0.92+0.004
    def hgt(sv): return min(ZB+0.012+0.030*math.sqrt(min(sv/0.14,1))+0.095*max(0,(sv-0.30)/0.45)**1.3,BOOT_TOP-0.004 if W else 9)
    def footfn(b2):
        NS=16; NU=14; secs=[]
        for i in range(NS+1):
            sv=0.02+0.93*i/NS; y=toe_y+L*sv; w=halfw(y)*(0.75+0.25*math.sqrt(min(sv/0.1,1))); h=hgt(sv)
            secs.append([b2.verts.new((cx+math.cos(math.pi*k/NU)*w,y,ZB-0.003+math.sin(math.pi*k/NU)*(h-ZB+0.003))) for k in range(NU+1)])
        for i in range(NS):
            for k in range(NU): b2.faces.new((secs[i][k],secs[i][k+1],secs[i+1][k+1],secs[i+1][k]))
            b2.faces.new((secs[i][0],secs[i+1][0],secs[i+1][NU],secs[i][NU]))
        tip=b2.verts.new((cx,toe_y+L*0.005,ZB+0.012))
        for k in range(NU): b2.faces.new((secs[0][k+1],secs[0][k],tip))
        b2.faces.new(secs[-1])
    RINGS=[]
    for zz in ((0.09,BOOT_TOP) if W else (0.10,0.14,0.18,BOOT_TOP)):
        Lr=[co for co,_ in src if co.x*sd>0 and abs(co.z-zz)<0.012]
        if W:   # 白礼装: 靴の上の脚(ズボン)の太さを基準にする
            Lr=[v.co.copy() for v in me.vertices if (v.co.x>0)==(sd>0) and abs(v.co.x)<0.2 and abs(v.co.z-0.15)<0.01]
            Lr=[Vector((p.x,p.y,zz)) for p in Lr]
        if Lr:
            lx=sum(p.x for p in Lr)/len(Lr); ly=sum(p.y for p in Lr)/len(Lr)
            RINGS.append((zz,lx,ly,max(abs(p.x-lx) for p in Lr)+0.009,max(abs(p.y-ly) for p in Lr)+0.009))
    z0,lx,ly,rx,ry=RINGS[0]
    RINGS=[(ZB+0.003,lx,ly+0.006,rx*1.05,ry*1.12),(0.06,lx,ly+0.004,rx*1.03,ry*1.08)]+RINGS
    def shaftfn(b2):
        NR=24; rr=[[b2.verts.new((lx+math.cos(2*math.pi*k/NR)*rx,ly+math.sin(2*math.pi*k/NR)*ry,zz)) for k in range(NR)] for zz,lx,ly,rx,ry in RINGS]
        for a_,b_ in zip(rr,rr[1:]):
            for k in range(NR): b2.faces.new((a_[k],a_[(k+1)%NR],b_[(k+1)%NR],b_[k]))
        b2.faces.new(rr[0][::-1]); b2.faces.new(rr[-1])
    def union(base_fn,op_fn,solver):
        a_=mk("bootA"+s_,base_fn); b_=mk("bootB"+s_,op_fn)
        md=a_.modifiers.new("u","BOOLEAN"); md.operation="UNION"; md.object=b_; md.solver=solver
        bpy.context.view_layer.objects.active=a_; bpy.ops.object.modifier_apply(modifier="u"); bpy.data.objects.remove(b_)
        zs=[v.co.z for v in a_.data.vertices]; ys=[v.co.y for v in a_.data.vertices]
        ok=zs and sum(1 for z in zs if z>BOOT_TOP-0.003)>=16 and min(ys)<toe_y+0.02
        if not ok: bpy.data.objects.remove(a_)
        return a_ if ok else None
    fo=union(footfn,shaftfn,"EXACT") or union(shaftfn,footfn,"EXACT") or union(footfn,shaftfn,"FAST")
    print("BOOT",s_,"ok" if fo else "FAILED")
    # 履き口の上面(蓋)は削除してズボンに差し込む形に
    b2=bmesh.new(); b2.from_mesh(fo.data)
    bmesh.ops.delete(b2,geom=[f for f in b2.faces if f.normal.z>0.9 and f.calc_center_median().z>BOOT_TOP-0.003],context="FACES")
    b2.to_mesh(fo.data); b2.free()
    fo.data.materials.clear(); fo.data.materials.append(LEATHER); fo.data.materials.append(TOE)
    for pl in fo.data.polygons:   # ブーリアンで素材番号が不定になる面があるため全面を明示的に割り当てる
        pl.use_smooth=True
        pl.material_index=1 if (pl.center.y<toe_y+L*0.28 and pl.center.z<0.08) else 0
    # ゴム底
    fp=[v.co.copy() for v in fo.data.vertices if v.co.z<ZB+0.005]
    sole=mk("sole"+s_,lambda b2:bmesh.ops.convex_hull(b2,input=[b2.verts.new((cx+(p.x-cx)*(1.03 if W else 1.06),p.y*1.0+(0.004 if p.y>ly else -0.004),z)) for p in fp for z in ((0.0 if W else -0.004),ZB+0.006)]))
    sole.data.materials.append(SOLE)
    for o in (fo,sole):
        groups={}
        for v in o.data.vertices:
            _,i,_=kd.find(v.co)
            for g,w in src[i][1].items():
                nm=gname.get(g)
                if nm is None: continue
                if nm not in groups: groups[nm]=o.vertex_groups.get(nm) or o.vertex_groups.new(name=nm)
                groups[nm].add([v.index],w,"REPLACE")
        boot_objs.append(o)
    E=[]
    for sv in (0.42,0.52,0.62):
        y=toe_y+L*sv; E.append((y,hgt(sv)+0.003,Vector((0,-0.35,1)).normalized()))
    if not W:
        zl,lxl,lyl,rxl,ryl=RINGS[-3]
        for zz in (0.13,0.165,BOOT_TOP-0.012): E.append((lyl-ryl-0.002,zz,Vector((0,-1,0))))
    boots_info[s_]=(cx,E)
bpy.ops.object.select_all(action="DESELECT")
for o in boot_objs: o.select_set(True)
wear.select_set(True); bpy.context.view_layer.objects.active=wear; bpy.ops.object.join()
# 靴紐とアイレット
n0=len(parts)
dg=bpy.context.evaluated_depsgraph_get(); bvhB=BVHTree.FromObject(wear,dg)
for s_,(cx,EL) in boots_info.items():
    E={}
    for i,(y,z,n) in enumerate(EL):
        for side in (-1,1): E[(i,side)]=(Vector((cx+side*0.012,y,z)),n)
    for (i,side),(h,n) in E.items():
        piece(lambda b2,h=h: bmesh.ops.create_uvsphere(b2,u_segments=8,v_segments=6,radius=0.003,matrix=Matrix.Translation(h)),EYE,f"shin.{s_}" if h.z>0.1 else f"foot.{s_}",f"eye{s_}{i}{side}")
    def laces(b2,E=E,n_=len(EL)):
        for i in range(n_-1):
            for a,b in (((i,-1),(i+1,1)),((i,1),(i+1,-1))):
                p0=E[a][0]+E[a][1]*0.002; p1=E[b][0]+E[b][1]*0.002
                d=p1-p0; rot=Vector((0,0,1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
                bmesh.ops.create_cone(b2,cap_ends=True,segments=6,radius1=0.0017,radius2=0.0017,depth=d.length,matrix=Matrix.Translation((p0+p1)/2)@rot)
    piece(laces,LACE,f"shin.{s_}","laces"+s_)
bpy.ops.object.select_all(action="DESELECT")
for o in parts[n0:]: o.select_set(True)
wear.select_set(True); bpy.context.view_layer.objects.active=wear; bpy.ops.object.join()
# 裾のたるみ(ブーツに被さるリング)
hems=[]
for s_,sd in (("L",1),("R",-1)):
    P=[v.co for v in me.vertices if abs(v.co.z-(0.15 if W else BOOT_TOP+0.005))<0.01 and (v.co.x>0)==(sd>0) and abs(v.co.x)<0.2]
    if not P: continue
    cx=sum(p.x for p in P)/len(P); cy=sum(p.y for p in P)/len(P)
    rx=max(abs(p.x-cx) for p in P)+(0.012 if W else 0); ry=max(abs(p.y-cy) for p in P)+(0.012 if W else 0)
    o=bpy.data.objects.new("hem"+s_,bpy.data.meshes.new("hem"+s_)); bpy.context.scene.collection.objects.link(o)
    b2=bmesh.new(); bmesh.ops.create_cone(b2,cap_ends=False,segments=28,radius1=(1.12 if W else 1.12),radius2=1.0,depth=0.045,matrix=Matrix.Translation((cx,cy,BOOT_TOP+0.01))@Matrix.Diagonal((rx+0.004,ry+0.004,1,1)))
    bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=0.003); b2.to_mesh(o.data); b2.free()
    o.data.materials.append(PANTS); o.vertex_groups.new(name=f"shin.{s_}").add(range(len(o.data.vertices)),1.0,"REPLACE"); hems.append(o)
bpy.ops.object.select_all(action="DESELECT")
for o in hems: o.select_set(True)
wear.select_set(True); bpy.context.view_layer.objects.active=wear; bpy.ops.object.join()
bpy.ops.wm.save_as_mainfile(filepath=S+"/nemo_s2o.blend")
print("DONEB")
