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
dels=[f for f in bm.faces if MN(f)=="huku_bake" or (MN(f) in("armgear_plastic","wear_metal","glass","robo_face") and C(f).x<0)]
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
iSh=midx(mat("shirt_outer",(0.022,0.022,0.027),0,0.8))
sh_src=[f for f in skin if shirt_ok(f)]
def in_v(c,m=0.0):   # 首元のY字開き(上ほど広い)
    return c.y<-0.02 and c.z>NZ-0.13 and abs(c.x)<(0.004+0.30*(c.z-(NZ-0.13)))+m
shirt=shell(sh_src,0.006,iSh,2)
z0=NZ-0.13
for sx in (1,-1): cut(by_mat(iSh),Vector((sx*0.004,0,z0)),Vector((sx,0,-0.30)).normalized())
cut(by_mat(iSh),Vector((0,0,z0)),Vector((0,0,1)))
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
iPo=midx(mat("pants_outer",(0.035,0.038,0.05),0,0.75))
pants_src=list(set(pants_src))
pants=shell(pants_src,0.012,iPo,6)
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
# カーゴポケット(外もも)
for sd,s_ in ((1,"L"),(-1,"R")):
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
# シャツ襟: 首回りの台襟 + 外へ折り返す襟(前は尖る)
nk=B("neck"); ring=[v.co for v in me.vertices if abs(v.co.z-(nk.z-0.005))<0.008 and abs(v.co.x)<0.07]
R=max(math.hypot(p.x,p.y-nk.y) for p in ring)+0.004
def collar(b2):
    seg=40; gap=math.radians(58); rows=[]
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
# ネクタイ(結び目+首元を覆う大剣)
def tie(b2):
    loc,n=front_hit(0,NZ-0.02); top=loc+Vector((0,-0.006,0))
    bmesh.ops.create_cone(b2,cap_ends=True,segments=8,radius1=0.007,radius2=0.012,depth=0.022,matrix=Matrix.Translation(top)@Matrix.Diagonal((1,0.7,1,1)))
    L=0.20; rows=[]
    for i in range(11):
        t=i/10; z=top.z-0.01-L*t
        h,_=front_hit(0,z); y=(h.y if h else top.y)-0.013
        w=0.012+0.016*t
        rows.append([b2.verts.new((-w,y,z)),b2.verts.new((w,y,z))])
    tip=b2.verts.new((0,rows[-1][0].co.y,top.z-0.01-L-0.018))
    for a,b in zip(rows,rows[1:]): b2.faces.new((a[0],a[1],b[1],b[0]))
    b2.faces.new((rows[-1][0],rows[-1][1],tip))
    bmesh.ops.solidify(b2,geom=[f for f in b2.faces if len(f.verts)!=8 or True],thickness=0.002)
piece(tie,mat("tie",(0.03,0.028,0.034),0.1,0.22),"chest","necktie")
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
# ベルト通し
for ang in (-70,-30,30,70,150,210):
    t=math.radians(ang); d=Vector((math.sin(t),-math.cos(t),0))
    o=Vector((0,0.0,HZ+0.05))+d*0.5
    loc,n,_,_=bvh.ray_cast(o,-d)
    if loc: piece(lambda b2,loc=loc,d=d: bmesh.ops.create_cube(b2,size=1,matrix=Matrix.Translation(loc+d*0.002)@Matrix.Rotation(math.atan2(d.x,-d.y),4,'Z')@Matrix.Diagonal((0.012,0.004,0.04,1))),PANTS,"hips",f"loop{ang}")
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
        P=legpts(zz,sd)
        if not P: continue
        cx=sum(p.x for p in P)/len(P); cy=sum(p.y for p in P)/len(P)
        rx=sorted(abs(p.x-cx) for p in P)[int(len(P)*0.9)]+0.002; ry=sorted(abs(p.y-cy) for p in P)[int(len(P)*0.9)]+0.002
        piece(lambda b2,cx=cx,cy=cy,rx=rx,ry=ry,zz=zz:(bmesh.ops.create_cone(b2,cap_ends=False,segments=24,radius1=1,radius2=1,depth=0.018,matrix=Matrix.Translation((cx,cy,zz))@Matrix.Diagonal((rx,ry,1,1))),bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=0.003)),STRAP,bone,f"band{s_}{zz:.2f}")
bpy.ops.object.select_all(action="DESELECT")
for o in parts: o.select_set(True)
wear.select_set(True); bpy.context.view_layer.objects.active=wear; bpy.ops.object.join()

# ---- 5. ブーツ: 脛上部はズボン、脛中〜足首に赤カバー、金帯 ----
bm=bmesh.new(); bm.from_mesh(me)
names=[m.name for m in me.materials]
BOOTS={names.index(n) for n in("boot_red","boot_dark","gold") if n in names}
bf=lambda: [f for f in bm.faces if f.material_index in BOOTS and f.calc_center_median().z<KZ and all(abs(v.co.x)<0.2 for v in f.verts)]
for z in (0.155,0.135):
    g=bf(); bmesh.ops.bisect_plane(bm,geom=list({v for f in g for v in f.verts})+list({e for f in g for e in f.edges})+g,plane_co=(0,0,z),plane_no=(0,0,1))
iR=names.index("boot_red"); iB=names.index("boot_dark"); iG=names.index("gold")
for f in bf():
    z=f.calc_center_median().z
    if z>0.155: f.material_index=iPo
    elif z>0.135: f.material_index=iG
    elif z>0.06 and f.material_index!=iR: f.material_index=iB
bm.to_mesh(me); bm.free()
# 裾のたるみ(ブーツに被さるリング)
hems=[]
for s_,sd in (("L",1),("R",-1)):
    P=[v.co for v in me.vertices if abs(v.co.z-0.17)<0.01 and (v.co.x>0)==(sd>0) and abs(v.co.x)<0.2]
    if not P: continue
    cx=sum(p.x for p in P)/len(P); cy=sum(p.y for p in P)/len(P)
    rx=max(abs(p.x-cx) for p in P); ry=max(abs(p.y-cy) for p in P)
    o=bpy.data.objects.new("hem"+s_,bpy.data.meshes.new("hem"+s_)); bpy.context.scene.collection.objects.link(o)
    b2=bmesh.new(); bmesh.ops.create_cone(b2,cap_ends=False,segments=28,radius1=1.25,radius2=1.0,depth=0.05,matrix=Matrix.Translation((cx,cy,0.165))@Matrix.Diagonal((rx+0.004,ry+0.004,1,1)))
    bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=0.003); b2.to_mesh(o.data); b2.free()
    o.data.materials.append(PANTS); o.vertex_groups.new(name=f"shin.{s_}").add(range(len(o.data.vertices)),1.0,"REPLACE"); hems.append(o)
bpy.ops.object.select_all(action="DESELECT")
for o in hems: o.select_set(True)
wear.select_set(True); bpy.context.view_layer.objects.active=wear; bpy.ops.object.join()
bpy.ops.wm.save_as_mainfile(filepath=S+"/nemo_s2o.blend")
print("DONEB")
