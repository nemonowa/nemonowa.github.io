# 服装の作り込み: 黒Yシャツ・刺繍ベスト・紅い軍服(長袖/前開き/裾)・長ズボン・ニーパッド・ベルト類・飾緒
import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
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
COAT=mat("coat_red",(0.50,0.018,0.03),0,0.6); GOLD=bpy.data.materials["gold"]
SHIRT=bpy.data.materials["shirt_black"]; PANTS=mat("pants",(0.028,0.03,0.042),0,0.7)
PAD=mat("kneepad",(0.11,0.11,0.12),0.6,0.35); STRAP=mat("strap",(0.018,0.016,0.014),0.1,0.55)
GEM=mat("gem",(0.05,0.55,0.5),0.2,0.15)
# ベスト用テクスチャ(赤地に金の唐草)
VW=512; yy,xx=np.mgrid[0:VW,0:VW]/VW
pat=np.abs(np.sin(yy*38+np.sin(np.abs(xx-0.5)*22)*2.6))<0.22
pat|=np.abs(np.sin(np.hypot((xx-0.5)*3,(yy*6)%1-0.5)*28))<0.16
pat&=np.abs(xx-0.5)<0.42
border=(np.abs(xx-0.5)>0.44)&(np.abs(xx-0.5)<0.48)
col=np.zeros((VW,VW,4),np.float32); col[...,3]=1
col[...,:3]=[0.30,0.012,0.02]
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

# ---- 1. 旧衣装の削除(チュニック・七分丈ズボン・ベルト・右手首の装備) ----
dels=[f for f in bm.faces if MN(f)=="huku_bake" or (MN(f) in("armgear_plastic","wear_metal","glass","robo_face") and f.calc_center_median().x<0)]
bmesh.ops.delete(bm,geom=dels,context="FACES")
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
SKIN={"body_bake","sleeve_red","shirt_black"}
TORSO=("hips","spine","chest","neck","shoulder")
KZ=B("shin.L").z; HZ=B("hips").z; NZ=B("neck").z
# ---- 2. 黒シャツ: 胴の肌を黒に ----
iS=midx(SHIRT)
for f in bm.faces:
    if MN(f) in SKIN and fdom(f).startswith(TORSO) and f.calc_center_median().z<NZ+0.01: f.material_index=iS

def shell(faces,off,mi,smooth=4):
    """facesを複製して平滑化+法線方向にoffし、マテリアルmiを割り当てる(ウェイトは複製で引き継ぐ)"""
    r=bmesh.ops.duplicate(bm,geom=faces)
    nf=[e for e in r["geom"] if isinstance(e,bmesh.types.BMFace)]
    nv=list({v for f in nf for v in f.verts})
    inner=[v for v in nv if not v.is_boundary]
    for _ in range(smooth): bmesh.ops.smooth_vert(bm,verts=inner,factor=0.5,use_axis_x=True,use_axis_y=True,use_axis_z=True)
    bm.normal_update()
    nrm={v:v.normal.copy() for v in nv}
    for v in nv: v.co+=nrm[v]*off
    for f in nf: f.material_index=mi; f.smooth=True
    return nf
skin=[f for f in bm.faces if MN(f) in SKIN|{"shirt_black"}]
def C(f): return f.calc_center_median()

# ---- 3. 刺繍ベスト(胸〜腰の前面) ----
vest_src=[f for f in skin if fdom(f).startswith(("hips","spine","chest")) and C(f).y<-0.02 and abs(C(f).x)<0.075 and HZ-0.02<C(f).z<1.36]
vest=shell(vest_src,0.006,midx(VEST),2)
zs=[v.co.z for f in vest for v in f.verts]; z0,z1=min(zs),max(zs)
for f in vest:
    for l in f.loops: l[uvl].uv=((l.vert.co.x+0.08)/0.16,(l.vert.co.z-z0)/(z1-z0))
# ---- 4. 腰ベルトとバックル ----
belt_src=[f for f in skin if fdom(f).startswith(("hips","spine")) and abs(C(f).z-(HZ+0.045))<0.022]
shell(belt_src,0.010,midx(STRAP),1)

# ---- 5. 軍服(胴+袖。前は開く) ----
def coat_ok(f):
    c=C(f); d=fdom(f)
    if d.startswith(TORSO) or d.startswith(("upper_arm","forearm.R","forearm.twist.R")):
        if c.z<HZ-0.04: return False
        if d.startswith("neck"): return False
        return True
    return False
coat_src=[f for f in skin if coat_ok(f)]
iC=midx(COAT); coat=shell(coat_src,0.014,iC,3)
iG=midx(GOLD)
def cut(faces,co,no):
    g=list({v for f in faces for v in f.verts})+list({e for f in faces for e in f.edges})+list(faces)
    bmesh.ops.bisect_plane(bm,geom=g,plane_co=co,plane_no=no)
def coatfaces(): return [f for f in bm.faces if f.material_index in(iC,iG) and f.is_valid]
for x in (0.058,0.071,-0.058,-0.071): cut(coatfaces(),Vector((x,0,0)),Vector((1,0,0)))
cut(coatfaces(),Vector((0,0,NZ-0.03)),Vector((0,0,1)))
front=lambda c: c.y<-0.01 and c.z<NZ-0.03
bmesh.ops.delete(bm,geom=[f for f in coatfaces() if front(C(f)) and abs(C(f).x)<0.058],context="FACES")
for f in coatfaces():
    c=C(f)
    if front(c) and abs(c.x)<0.071: f.material_index=iG
# 袖口の金帯(境界に接する面)
for f in coatfaces():
    c=C(f)
    if any(v.is_boundary for v in f.verts) and ((c-B("hand.R")).length<0.06 or (c-B("forearm.L")).length<0.05): f.material_index=iG
# ---- 6. 裾(腰から太もも中ほどまで広がる。前は開く) ----
kd=KDTree(len(bm.verts))
for v in bm.verts: kd.insert(v.co,v.index)
bm.verts.ensure_lookup_table(); kd.balance()
body=[v.co.copy() for f in skin for v in f.verts]
def radius(z,th):
    d=Vector((math.sin(th),-math.cos(th),0)); best=0.05
    for p in body:
        if abs(p.z-z)<0.02:
            q=Vector((p.x,p.y-0.0,0))
            if q.dot(d)>best and (q-d*q.dot(d)).length<0.02: best=q.dot(d)
    return best
ZT=HZ+0.07; LV=8; ZB=HZ-0.25; GAP=math.radians(22); NA=36
th=[GAP+(2*math.pi-2*GAP)*i/NA for i in range(NA+1)]
r0=[radius(ZT,t)+0.021 for t in th]
rings=[]
for j in range(LV):
    s=j/(LV-1); z=ZT-(ZT-ZB)*s; fl=1+0.38*max(0,s-0.2)
    ring=[]
    for t,r in zip(th,r0):
        v=bm.verts.new((math.sin(t)*r*fl,-math.cos(t)*r*fl*0.95+0.01,z))
        side=max(0,min(1,0.5+v.co.x/0.12))
        wh=1-0.7*max(0,s-0.25)/0.75
        v[dl][gid["hips"]]=wh; v[dl][gid["thigh.L"]]=(1-wh)*side; v[dl][gid["thigh.R"]]=(1-wh)*(1-side)
        ring.append(v)
    rings.append(ring)
skirt=[]
for j in range(LV-1):
    for i in range(NA):
        f=bm.faces.new((rings[j][i],rings[j][i+1],rings[j+1][i+1],rings[j+1][i])); f.material_index=iC; f.smooth=True; skirt.append(f)
for f in skirt:
    if any(v in rings[-1] for v in f.verts) or any(v in (rings[k][0],rings[k][1],rings[k][-1],rings[k][-2]) for k in range(1,LV) for v in f.verts if f.verts[0] not in rings[0]): f.material_index=iG
bmesh.ops.solidify(bm,geom=skirt,thickness=0.004)
bmesh.ops.recalc_face_normals(bm,faces=skirt)

# ---- 7. 長ズボン(太もも〜脛上部。ブーツのレッグカバーに差し込む) ----
pants_src=[f for f in skin if fdom(f).startswith(("thigh","shin")) and C(f).z>0.30] + \
          [f for f in skin if fdom(f).startswith("hips") and C(f).z<HZ+0.02]
pants=shell(pants_src,0.009,midx(PANTS),3)
# 脚の肌は隙間から見えないようズボン色に
iP0=midx(PANTS)
for f in bm.faces:
    if MN(f) in SKIN and fdom(f).startswith(("thigh","shin")): f.material_index=iP0
bm.to_mesh(me); bm.free()

# ---- 8. ボタン・バックル・宝石・飾緒(剛体の小物はボーンへ1:1ウェイト) ----
def new_obj(name):
    o=bpy.data.objects.new(name,bpy.data.meshes.new(name)); bpy.context.scene.collection.objects.link(o); return o
from mathutils.bvhtree import BVHTree
dg=bpy.context.evaluated_depsgraph_get(); bvh=BVHTree.FromObject(wear,dg)
def front_hit(x,z):
    loc,n,_,_=bvh.ray_cast(Vector((x,-1,z)),Vector((0,1,0))); return loc,n
parts=[]
def piece(bmfunc,mat,bone,name):
    o=new_obj(name); b2=bmesh.new(); bmfunc(b2); b2.to_mesh(o.data); b2.free(); o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth=True
    o.vertex_groups.new(name=bone).add(range(len(o.data.vertices)),1.0,"REPLACE"); parts.append(o)
def ball(r,loc,sc=(1,1,1)):
    return lambda b2: bmesh.ops.create_uvsphere(b2,u_segments=12,v_segments=8,radius=r,matrix=Matrix.Translation(loc)@Matrix.Diagonal((*sc,1)))
for sx in (1,-1):
    for i,z in enumerate(np.linspace(1.33,1.02,5)):
        loc,n=front_hit(sx*0.072,z)
        if loc: piece(ball(0.0075,loc-Vector((0,0.002,0)),(1,0.6,1)),GOLD,"chest" if z>1.2 else "spine",f"btn{sx}{i}")
loc,n=front_hit(0,HZ+0.045)
if loc: piece(lambda b2: bmesh.ops.create_cube(b2,size=1,matrix=Matrix.Translation(loc-Vector((0,0.004,0)))@Matrix.Diagonal((0.05,0.012,0.034,1))),GOLD,"hips","buckle")
loc,n=front_hit(0,NZ-0.035)
if loc:
    piece(ball(0.013,loc-Vector((0,0.006,0)),(1,0.55,1.3)),GOLD,"chest","brooch")
    piece(ball(0.009,loc-Vector((0,0.012,0)),(1,0.6,1.3)),GEM,"chest","gem")
# 飾緒: 左肩から胸へ2本の弧
def cord(p0,p1,sag,r=0.0035):
    def f(b2):
        pts=[p0.lerp(p1,t)+Vector((0,-0.012*math.sin(math.pi*t),-sag*math.sin(math.pi*t))) for t in np.linspace(0,1,24)]
        prev=None
        for i,p in enumerate(pts):
            tg=(pts[min(i+1,23)]-pts[max(i-1,0)]).normalized(); a=tg.orthogonal().normalized(); b=tg.cross(a)
            ring=[b2.verts.new(p+(a*math.cos(k*math.pi/3)+b*math.sin(k*math.pi/3))*r) for k in range(6)]
            if prev:
                for k in range(6): b2.faces.new((prev[k],prev[(k+1)%6],ring[(k+1)%6],ring[k]))
            prev=ring
    return f
sh,_=front_hit(0.15,1.39); ch,_=front_hit(0.072,1.26)
if sh and ch:
    for sag in (0.03,0.06,0.09): piece(cord(sh+Vector((0,-0.01,0)),ch+Vector((0,-0.008,0)),sag),GOLD,"chest",f"cord{sag}")
# ニーパッド(ドーム形の装甲)と太もものベルト(輪)
def legpts(z,side):
    return [v.co for v in wear.data.vertices if abs(v.co.z-z)<0.012 and (v.co.x>0)==(side>0) and abs(v.co.x)<0.2]
for s_,sd in (("L",1),("R",-1)):
    k=B(f"shin.{s_}")
    loc,n=front_hit(k.x,k.z-0.005)
    if loc:
        def pad(b2,loc=loc):
            bmesh.ops.create_uvsphere(b2,u_segments=20,v_segments=12,radius=1.0)
            for v in list(b2.verts):
                if v.co.y>0.15: b2.verts.remove(v)
            bmesh.ops.transform(b2,matrix=Matrix.Translation(loc+Vector((0,0.012,0)))@Matrix.Diagonal((0.052,0.028,0.07,1)),verts=b2.verts)
            bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=-0.004)
        piece(pad,PAD,f"shin.{s_}",f"kneepad{s_}")
        # 上下の留めベルト
    for zz,bone in ((k.z+0.075,f"thigh.{s_}"),(k.z-0.08,f"shin.{s_}")):
        P=legpts(zz,sd)
        if not P: continue
        cx=sum(p.x for p in P)/len(P); cy=sum(p.y for p in P)/len(P)
        rx=max(abs(p.x-cx) for p in P)+0.013; ry=max(abs(p.y-cy) for p in P)+0.013
        def band(b2,cx=cx,cy=cy,rx=rx,ry=ry,zz=zz):
            bmesh.ops.create_cone(b2,cap_ends=False,segments=24,radius1=1,radius2=1,depth=0.018,matrix=Matrix.Translation((cx,cy,zz))@Matrix.Diagonal((rx,ry,1,1)))
            bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=0.003)
        piece(band,STRAP,bone,f"band{s_}{zz:.2f}")
bpy.ops.object.select_all(action="DESELECT")
for o in parts: o.select_set(True)
wear.select_set(True); bpy.context.view_layer.objects.active=wear; bpy.ops.object.join()

# ---- 9. ブーツ: 脛上部は削除(ズボンを見せる)、脛中〜足首は赤いレッグカバー、足首上に金帯 ----
bm=bmesh.new(); bm.from_mesh(me)
BOOTS={list(me.materials).index(bpy.data.materials[n]) for n in("boot_red","boot_dark")}|{iG}
bf=lambda: [f for f in bm.faces if f.material_index in BOOTS and f.calc_center_median().z<KZ and all(abs(v.co.x)<0.2 for v in f.verts)]
for z in (0.34,0.20,0.175):
    g=bf(); bmesh.ops.bisect_plane(bm,geom=list({v for f in g for v in f.verts})+list({e for f in g for e in f.edges})+g,plane_co=(0,0,z),plane_no=(0,0,1))
iP=list(me.materials).index(PANTS)
for f in bf():
    if f.calc_center_median().z>0.34: f.material_index=iP
iR=list(me.materials).index(bpy.data.materials["boot_red"]); iB=list(me.materials).index(bpy.data.materials["boot_dark"])
for f in bf():
    z=f.calc_center_median().z
    if z>0.34: continue
    if z>0.20: f.material_index=iR
    elif z>0.175: f.material_index=iG
    elif z>0.06 and f.material_index!=iR: f.material_index=iB
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=S+"/nemo_s2o.blend")
print("DONEO")
