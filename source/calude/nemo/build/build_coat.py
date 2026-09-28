# 上着の段: 紅い軍服(前開き・長袖・裾)・刺繍ベスト・立ち襟・肩章・飾緒・金ボタン(土台build_baseの上に重ねる)
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
    COAT=mat("coat_white",(0.72,0.70,0.66),0,0.5); GOLD=mat("trim_dark",(0.16,0.12,0.09),0.2,0.5)   # 白地+濃い灰茶の縁取り
    bpy.data.materials["glove_black"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(0.78,0.77,0.74,1)   # 右手は白手袋
else:
    COAT=mat("coat_red",(0.2423,0.0021,0.0048),0,0.65); GOLD=bpy.data.materials["gold"]   # coat: sRGB #87070F
# ベスト用テクスチャ(赤地に金の唐草)
VW=512; yy,xx=np.mgrid[0:VW,0:VW]/VW
pat=np.abs(np.sin(yy*38+np.sin(np.abs(xx-0.5)*22)*2.6))<0.20
pat|=np.abs(np.sin(np.hypot((xx-0.5)*3,(yy*6)%1-0.5)*28))<0.14
pat&=np.abs(xx-0.5)<0.40
border=(np.abs(xx-0.5)>0.43)&(np.abs(xx-0.5)<0.47)
col=np.zeros((VW,VW,4),np.float32); col[...,3]=1; col[...,:3]=[0.36,0.012,0.022]
col[pat|border]=[0.78,0.52,0.15,1]
vimg=bpy.data.images.new("vest",VW,VW); vimg.pixels[:]=col.ravel(); vimg.pack()
VEST=mat("vest",(1,1,1),0.2,0.5); vn=VEST.node_tree.nodes; t=vn.new("ShaderNodeTexImage"); t.image=vimg
VEST.node_tree.links.new(t.outputs[0],vn["Principled BSDF"].inputs["Base Color"])

bm=bmesh.new(); bm.from_mesh(me); dl=bm.verts.layers.deform.active; uvl=bm.loops.layers.uv.active
gname={g.index:g.name for g in wear.vertex_groups}; gid={v:k for k,v in gname.items()}
def dom(v):
    d=v[dl]; return gname[max(d.items(),key=lambda kv:kv[1])[0]] if d else ""
def fdom(f):
    ds=[dom(v) for v in f.verts]; return max(set(ds),key=ds.count)
MN=lambda f: me.materials[f.material_index].name
C=lambda f: f.calc_center_median()
HZ=B("hips").z; NZ=B("neck").z
def shell(faces,off,mi,smooth=3):
    r=bmesh.ops.duplicate(bm,geom=faces)
    nf=[e for e in r["geom"] if isinstance(e,bmesh.types.BMFace)]
    nv=list({v for f in nf for v in f.verts})
    bmesh.ops.remove_doubles(bm,verts=nv,dist=0.003)
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
    bmesh.ops.bisect_plane(bm,geom=g,plane_co=co,plane_no=no)
def by(mis): return [f for f in bm.faces if f.is_valid and f.material_index in mis]
SHIRT={midx(bpy.data.materials[n]) for n in("shirt_outer","shirt_placket")}

# ---- 0. 上着に隠れるズボンのベルト・バックル・ベルト通しを削除 ----
kill=[f for f in bm.faces if f.is_valid and (MN(f)=="buckle" or (MN(f) in("strap","pants","pants_pocket","pants_outer") and HZ+0.02<C(f).z<HZ+0.09 and abs(C(f).x)<0.25))]
bmesh.ops.delete(bm,geom=kill,context="FACES")
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
# ---- 2. 軍服(シャツの上、胴+両上腕+右前腕。前は開く) ----
def coat_ok(f):
    d=fdom(f); c=C(f)
    return d.startswith(("hips","spine","chest","shoulder","upper_arm","forearm.R","forearm.twist.R")) and c.z>HZ-0.01
iC=midx(COAT); iG=midx(GOLD)
coat=shell([f for f in by(SHIRT) if coat_ok(f)],0.010,iC,3)
LINING=(mat("coat_edge",(0.45,0.43,0.40),0,0.6) if W else mat("coat_lining",(0.11,0.001,0.003),0,0.7)); iL=midx(LINING)
ZL=NZ-0.14; XO=0.0 if W else 0.045   # V字の下端 / 前の重なり線のx(左前身頃が右に重なる)
def in_v(c): return (not W) and c.y<-0.01 and c.z>ZL and abs(c.x-XO*0.4)<0.004+0.55*(c.z-ZL)
for sx in (() if W else (1,-1)): cut(by({iC}),Vector((XO*0.4+sx*0.004,0,ZL)),Vector((sx,0,-0.55)).normalized())
cut(by({iC}),Vector((0,0,ZL)),Vector((0,0,1)))
bmesh.ops.delete(bm,geom=[f for f in by({iC}) if in_v(C(f))],context="FACES")
for x in (XO,XO+0.005): cut(by({iC}),Vector((x,0,0)),Vector((1,0,0)))
for f in by({iC}):
    c=C(f)
    if c.y<-0.01 and XO<c.x<XO+0.005 and (c.z<ZL or W) and c.z<NZ-0.035: f.material_index=iL   # 重なりの影線
# 袖口: 骨に垂直な平面で切りそろえ、金帯も平面で区切る
def arm_cut(co,d,band):
    cut(by({iC,iG}),co,d); cut(by({iC,iG}),co-d*band,d)
    bmesh.ops.delete(bm,geom=[f for f in by({iC,iG}) if (C(f)-co).dot(d)>0 and (C(f)-co).length<0.15],context="FACES")
    for f in by({iC}):
        q=(C(f)-co).dot(d)
        if -band<q<=0 and (C(f)-co).length<0.12: f.material_index=iG
dR=(B("hand.R")-B("forearm.R")).normalized(); dL=(B("forearm.L")-B("upper_arm.L")).normalized()
arm_cut(B("hand.R")-dR*0.005,dR,0.028)
arm_cut(B("forearm.L")+dL*0.018,dL,0.025)
# 胴の下端は裾に任せる(ギザギザの境界を消す)
cut(by({iC,iL}),Vector((0,0,HZ+0.045)),Vector((0,0,1)))
bmesh.ops.delete(bm,geom=[f for f in by({iC,iL}) if C(f).z<HZ+0.045 and abs(C(f).x)<0.25],context="FACES")
# ---- 3. 裾(腰から太もも中ほど。前は開く) ----
pts=[v.co.copy() for f in by({iC,iL}) for v in f.verts if abs(v.co.x)<0.2 and abs(v.co.y)<0.2]
def radius(z,th):
    d=Vector((math.sin(th),-math.cos(th),0)); best=0.05
    for p in pts:
        if abs(p.z-z)<0.02:
            q=Vector((p.x,p.y,0))
            if q.dot(d)>best and (q-d*q.dot(d)).length<0.02: best=q.dot(d)
    return best
ZT=HZ+0.075; LV=9; ZB=HZ-(0.16 if W else 0.25)
from mathutils.bvhtree import BVHTree as _BVH
cbvh=_BVH.FromBMesh(bm)
CEN=Vector((0,0.005,ZT))
def coat_pt(t,z):
    d=Vector((math.sin(t),-math.cos(t),0)); o=Vector((CEN.x,CEN.y,z))
    h,n,_,_=cbvh.ray_cast(o+d*0.4,-d)
    return (h if h else o+d*0.13)
# 前の重なり線(x=XO)と一致する角度を探す
T0=min((abs(coat_pt(t,ZT+0.01).x-XO),t) for t in np.linspace(-0.3,1.2,300))[1]
NA=48; th=[T0+(2*math.pi+0.16)*i/NA for i in range(NA+1)]
top=[coat_pt(t,ZT+0.005) for t in th]
top=[Vector((p.x,p.y,ZT))+ (Vector((p.x,p.y,0))-Vector((CEN.x,CEN.y,0))).normalized()*0.002 for p in top]
for i,t in enumerate(th):
    if t>T0+2*math.pi: top[i]=CEN+(top[i]-CEN)*0.985; top[i].z=ZT   # 下前(内側に重なる部分)
r0=[(Vector((p.x,p.y,0))-Vector((CEN.x,CEN.y,0))).length for p in top]
# 各段の拡大率(横=x と 前後=y を別々に): 中の服を避けるのに必要な値を段ごとにまとめ、下へ単調増加
FX=[];FY=[];FB=[]
for j in range(LV):
    s_=j/(LV-1); z=ZT-(ZT-ZB)*s_; base=1+0.12*s_**1.6; fx=fy=fb=base
    if j>0:
        for p,t in zip(top,th):
            o=coat_pt(t,z); oo=Vector((o.x-CEN.x,o.y-CEN.y,0))
            if oo.length>0.22: continue
            px,py=p.x-CEN.x,p.y-CEN.y
            if abs(math.sin(t))>0.6 and abs(px)>1e-3: fx=max(fx,(abs(oo.x)+0.010)/abs(px))
            if abs(math.cos(t))>0.6 and abs(py)>1e-3:
                nf=(abs(oo.y)+0.010)/abs(py)
                if py<0: fy=max(fy,nf)
                else: fb=max(fb,nf)
    FX.append(fx); FY.append(fy); FB.append(fb)
for L_ in (FX,FY,FB):
    for j in range(1,LV): L_[j]=max(L_[j],L_[j-1])
    for _ in range(2): L_[1:]=[(L_[j-1]+2*L_[j]+L_[min(j+1,LV-1)])/4 for j in range(1,LV)]
    for j in range(1,LV): L_[j]=max(L_[j],L_[j-1])
rings=[]
for j in range(LV):
    s_=j/(LV-1); z=ZT-(ZT-ZB)*s_
    ring=[]
    for p in top:
        v=bm.verts.new((CEN.x+(p.x-CEN.x)*FX[j],CEN.y+(p.y-CEN.y)*(FY[j] if p.y<CEN.y else FB[j]),z))
        side=max(0,min(1,0.5+v.co.x/0.12)); wh=1-0.7*max(0,s_-0.25)/0.75
        v[dl][gid["hips"]]=wh; v[dl][gid["thigh.L"]]=(1-wh)*side; v[dl][gid["thigh.R"]]=(1-wh)*(1-side)
        ring.append(v)
    rings.append(ring)
facs=[(round(a,2),round(b,2),round(c,2)) for a,b,c in zip(FX,FY,FB)]
print("SKIRT facs",facs)
skirt=[]
for j in range(LV-1):
    for i in range(NA):
        f=bm.faces.new((rings[j][i],rings[j][i+1],rings[j+1][i+1],rings[j+1][i])); f.material_index=iC; f.smooth=True; skirt.append(f)
for f in skirt:
    if any(v in rings[-1] for v in f.verts): f.material_index=iG
    elif any(v is rings[k][0] for k in range(LV) for v in f.verts): f.material_index=iL   # 合わせ目の影線を裾まで通す
bmesh.ops.solidify(bm,geom=skirt,thickness=0.004)
bm.to_mesh(me); bm.free()

# ---- 4. 小物: 立ち襟・肩章・金ボタン・飾緒 ----
def new_obj(name):
    o=bpy.data.objects.new(name,bpy.data.meshes.new(name)); bpy.context.scene.collection.objects.link(o); return o
dg=bpy.context.evaluated_depsgraph_get(); bvh=BVHTree.FromObject(wear,dg)
def front_hit(x,z):
    loc,n,_,_=bvh.ray_cast(Vector((x,-1,z)),Vector((0,1,0))); return loc,n
parts=[]
def piece(fn,m,bone,name):
    o=new_obj(name); b2=bmesh.new(); fn(b2); b2.to_mesh(o.data); b2.free()
    for mm in (m if isinstance(m,list) else [m]): o.data.materials.append(mm)
    for p in o.data.polygons: p.use_smooth=True
    o.vertex_groups.new(name=bone).add(range(len(o.data.vertices)),1.0,"REPLACE"); parts.append(o); return o
# 立ち襟(シャツ襟の外側、前は大きく開く、上縁は金)
nk=B("neck"); ring=[v.co for v in me.vertices if abs(v.co.z-(nk.z-0.005))<0.008 and abs(v.co.x)<0.07]
R=max(math.hypot(p.x,p.y-nk.y) for p in ring)+0.012
def standcollar(b2):
    seg=32; gap=math.radians(10 if W else 95); rows=[]
    for k in range(seg+1):
        t=-math.pi/2+gap/2+(2*math.pi-gap)*k/seg
        if W:   # 下端は上着の表面に沿わせて肩の傾斜を覆う
            d=Vector((math.cos(t),math.sin(t)*0.95,0)).normalized(); zb=nk.z-0.05
            h,_,_,_=bvh.ray_cast(Vector((0,nk.y,zb))+d*0.3,-d)
            pb=(h if h and (h-Vector((0,nk.y,zb))).length<0.15 else Vector((0,nk.y,zb))+d*(R+0.02))+d*0.004
            rows.append([b2.verts.new(pb)]+[b2.verts.new((rr*math.cos(t),nk.y+rr*math.sin(t)*0.95,z)) for z,rr in ((nk.z+0.040,R+0.003),(nk.z+0.047,R+0.005))])
            continue
        rows.append([b2.verts.new((rr*math.cos(t),nk.y+rr*math.sin(t)*0.95,z)) for z,rr in (((nk.z-0.06,R+0.016),(nk.z+0.040,R+0.003),(nk.z+0.047,R+0.005)) if W else ((nk.z-0.045,R+0.012),(nk.z+0.022,R+0.002),(nk.z+0.030,R+0.004)))])
    for k in range(seg):
        for j in range(2):
            f=b2.faces.new((rows[k][j],rows[k+1][j],rows[k+1][j+1],rows[k][j+1])); f.material_index=j
    bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=0.003)
piece(standcollar,[COAT,GOLD],"chest","coat_collar")
# 肩章(左肩)
ua=B("upper_arm.L"); o=ua+Vector((0.01,0,0.3))
hit,nrm,_,_=bvh.ray_cast(o,(ua-o).normalized())
if hit is None: hit,nrm=ua+Vector((0,0,0.05)),Vector((0,0,1))
rot=Vector((0,0,1)).rotation_difference(nrm).to_matrix().to_4x4()
def epaulette(b2):
    bmesh.ops.create_cone(b2,cap_ends=True,segments=28,radius1=0.048,radius2=0.042,depth=0.008,matrix=Matrix.Translation((0,0,0.004))@Matrix.Diagonal((1.3,0.9,1,1)))
    for k in range(11):
        t=math.radians(-75+150*k/10); p=Vector((math.cos(t)*0.048*1.3,math.sin(t)*0.048*0.9,-0.014))
        bmesh.ops.create_cone(b2,cap_ends=True,segments=6,radius1=0.0033,radius2=0.0028,depth=0.032,matrix=Matrix.Translation(p))
    bmesh.ops.transform(b2,matrix=Matrix.Translation(hit+nrm*0.002)@rot@Matrix.Rotation(math.atan2(nrm.x,nrm.z)*0,4,'Z'),verts=b2.verts)
if not W: piece(epaulette,GOLD,"shoulder.L","epaulette")
# 金ボタン(前端の両側)
for bx in ((0.016,) if W else (XO+0.025,-XO+0.02)):
    for i,z in enumerate(np.linspace(NZ-0.06,HZ+0.11,6) if W else np.linspace(ZL-0.02,HZ+0.11,4)):
        sx=bx; loc,n=front_hit(bx,z)
        if loc: piece(lambda b2,loc=loc: bmesh.ops.create_uvsphere(b2,u_segments=12,v_segments=8,radius=0.007,matrix=Matrix.Translation(loc-Vector((0,0.002,0)))@Matrix.Diagonal((1,0.6,1,1))),GOLD,"chest" if z>1.2 else "spine",f"cbtn{sx}{i}")
# 飾緒: 左肩から胸の金ボタンへ3本の弧
def cord(p0,p1,sag,r=0.0032):
    def f(b2):
        P=[p0.lerp(p1,t)+Vector((0,-0.010*math.sin(math.pi*t),-sag*math.sin(math.pi*t))) for t in np.linspace(0,1,24)]
        prev=None
        for i,p in enumerate(P):
            tg=(P[min(i+1,23)]-P[max(i-1,0)]).normalized(); a=tg.orthogonal().normalized(); b=tg.cross(a)
            rg=[b2.verts.new(p+(a*math.cos(k*math.pi/3)+b*math.sin(k*math.pi/3))*r) for k in range(6)]
            if prev:
                for k in range(6): b2.faces.new((prev[k],prev[(k+1)%6],rg[(k+1)%6],rg[k]))
            prev=rg
    return f
sh,_=front_hit(0.15,1.40); ch,_=front_hit(XO+0.025,ZL-0.02)
if W:   # 白礼装: 襟の両脇から胸元へ垂れる飾り紐(クリーム色)
    CORD=mat("cord",(0.78,0.72,0.58),0.1,0.5)
    for sx,sag in ():   # 飾り紐はマントの結び目に置き換え
        a_,_=front_hit(sx*0.045,NZ-0.035); b_,_=front_hit(0.016,NZ-0.11)
        if a_ and b_: piece(cord(a_+Vector((0,-0.006,0)),b_+Vector((0,-0.008,0)),sag),CORD,"chest",f"wcord{sx}{sag}")
    sh=None
if sh and ch:
    for sag in (0.025,0.05,0.075): piece(cord(sh+Vector((0,-0.006,0)),ch+Vector((0,-0.006,0)),sag),GOLD,"chest",f"cord{sag}")
# ラペル(V字の両側に折り返した襟。表は赤、見えている面は裏地の濃い赤、縁は金)
for sx in (() if W else (1,-1)):
    cx=XO*0.4
    def lapel(b2,sx=sx,cx=cx):
        ztop=NZ-0.03; w=0.004+0.55*(ztop-ZL)
        prof=[(0.004,ZL-0.004),(w,ztop),(w+0.05,ztop-0.03),(0.05,ZL+0.03)]
        pts=[]
        for dx,z in prof:
            x=cx+sx*dx; loc,n=front_hit(x,z); pts.append((loc if loc else Vector((x,-0.1,z)))-Vector((0,0.005,0)))
        vs=[b2.verts.new(p) for p in pts]; b2.faces.new(vs if sx>0 else vs[::-1])
        bmesh.ops.subdivide_edges(b2,edges=b2.edges[:],cuts=4,use_grid_fill=True)
        for v in b2.verts:   # 表面に沿わせる
            h,_=front_hit(v.co.x,v.co.z)
            if h: v.co.y=h.y-0.005
        bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=0.003)
    piece(lapel,LINING,"chest",f"lapel{sx}")
# 腰ベルト(上着の上、胴と裾の境目を隠す)
BZ0,BZ1=ZT-0.040,ZT+0.014
band_pts=[Vector((v.co.x,v.co.y-0.01,0)) for v in me.vertices if BZ0-0.01<v.co.z<BZ1+0.01 and abs(v.co.x)<0.25 and abs(v.co.y)<0.25]
def outer(t):
    d=Vector((math.sin(t),-math.cos(t)*0.95,0)).normalized(); best=0.08
    for q in band_pts:
        k=q.dot(d)
        if k>best and (q-d*k).length<0.03: best=k
    return best
NB=64; RB=[outer(2*math.pi*k/NB)+0.006 for k in range(NB)]
def cbelt(b2):
    rows=[[b2.verts.new((math.sin(2*math.pi*k/NB)*RB[k],-math.cos(2*math.pi*k/NB)*RB[k]*0.95+0.01,zz)) for k in range(NB)] for zz in (BZ0,BZ1)]
    for k in range(NB): b2.faces.new((rows[0][k],rows[0][(k+1)%NB],rows[1][(k+1)%NB],rows[1][k]))
    bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=0.003)
piece(cbelt,bpy.data.materials["strap"],"hips","coat_belt")
loc=Vector((0.0,-RB[0]*0.95+0.01-0.004,(BZ0+BZ1)/2))
BUCK=mat("buckle",(0.6,0.6,0.62),1.0,0.25) if W else GOLD
if loc: piece(lambda b2: bmesh.ops.create_cube(b2,size=1,matrix=Matrix.Translation(loc-Vector((0,0.009,0)))@Matrix.Diagonal((0.05,0.006,0.038,1))),BUCK,"hips","coat_buckle")
if W:   # 右腰のホルスター(黒革のケース+留め金)
    k=int(NB*0.75)%NB; t=2*math.pi*k/NB; d=Vector((math.sin(t),-math.cos(t)*0.95,0)).normalized()
    hp=Vector((math.sin(t)*RB[k],-math.cos(t)*RB[k]*0.95+0.01,BZ0-0.045))+d*0.02
    rot=Matrix.Rotation(math.atan2(d.x,-d.y),4,'Z')
    piece(lambda b2: bmesh.ops.create_cube(b2,size=1,matrix=Matrix.Translation(hp)@rot@Matrix.Diagonal((0.06,0.03,0.12,1))),bpy.data.materials["strap"],"thigh.R","holster")
    piece(lambda b2: bmesh.ops.create_cube(b2,size=1,matrix=Matrix.Translation(hp+Vector((0,0,0.055))+d*0.016)@rot@Matrix.Diagonal((0.05,0.004,0.02,1))),BUCK,"thigh.R","holster_clip")
# 左ひじ: 義手と上腕をつなぐ金属ジョイント(袖口の内側から義手へ)
el=B("forearm.L"); dL=(el-B("upper_arm.L")).normalized()
proR=[v.co for v in me.vertices if me.materials and abs((v.co-el).dot(dL)-0.03)<0.01 and ((v.co-el)-dL*(v.co-el).dot(dL)).length<0.06]
rj=max(((p-el)-dL*(p-el).dot(dL)).length for p in proR) if proR else 0.035
slv=[v.co for v in me.vertices if abs((v.co-el).dot(dL)-0.0)<0.008 and ((v.co-el)-dL*(v.co-el).dot(dL)).length<0.09]
rs=max(((p-el)-dL*(p-el).dot(dL)).length for p in slv) if slv else rj+0.012
rotL=Vector((0,0,1)).rotation_difference(dL).to_matrix().to_4x4()
JM=mat("joint_metal",(0.03,0.03,0.035),0.9,0.3); JR=bpy.data.materials.get("prosthetic")
def joint(b2):
    # 袖の内側(太い)から義手(細い)へすぼまる筒+段差のリング
    bmesh.ops.create_cone(b2,cap_ends=False,segments=32,radius1=rs-0.004,radius2=rj+0.002,depth=0.05,matrix=Matrix.Translation(el+dL*0.012)@rotL)
    bmesh.ops.create_cone(b2,cap_ends=False,segments=32,radius1=rj+0.005,radius2=rj+0.005,depth=0.008,matrix=Matrix.Translation(el+dL*0.036)@rotL)
    bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=0.002)
piece(joint,JM,"forearm.L","elbow_joint")
print("JOINT rj",round(rj,4),"rs",round(rs,4))
bpy.ops.object.select_all(action="DESELECT")
for o in parts: o.select_set(True)
wear.select_set(True); bpy.context.view_layer.objects.active=wear; bpy.ops.object.join()
bpy.ops.wm.save_as_mainfile(filepath=S+"/nemo_s2c.blend")
print("DONEC")
