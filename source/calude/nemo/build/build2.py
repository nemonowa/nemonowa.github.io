import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
S=sys.argv[sys.argv.index("--")+1]
arm=bpy.data.objects["Armature"]; wear=bpy.data.objects["wear"]; head=bpy.data.objects["head"]
B=lambda n: arm.data.bones[n]
def mat(name,base,metal=0.0,rough=0.6,emit=None):
    m=bpy.data.materials.new(name); m.use_nodes=True; p=m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value=(*base,1); p.inputs["Metallic"].default_value=metal; p.inputs["Roughness"].default_value=rough
    return m
def midx(obj,m):
    if m.name not in obj.data.materials: obj.data.materials.append(m)
    return list(obj.data.materials).index(m)
GOLD=mat("gold",(0.70,0.45,0.12),0.7,0.35)
BOOT=mat("boot_dark",(0.035,0.035,0.04),0.2,0.45); BOOTR=mat("boot_red",(0.50,0.022,0.035),0.0,0.5)
COAT=bpy.data.materials["sleeve_red"]

# ---------- 刺繍・ボタン(服テクスチャに描く) ----------
im=bpy.data.images["wear"]; a=np.array(im.pixels[:],dtype=np.float32).reshape(1024,1024,4)[::-1].copy()
yy,xx=np.mgrid[0:1024,0:1024].astype(np.float32)
CX=370
strip=(np.abs(xx-CX)<34)&(((yy>205)&(yy<298))|((yy>345)&(yy<455)))
u=(xx-CX)/34; pat=np.abs(np.sin(yy*0.21+np.sin(np.abs(u)*5.5)*2.2))<0.28
pat|=np.abs(np.sin(np.abs(u)*9+yy*0.07))<0.18
gold=np.array([0.80,0.55,0.16])
for c in range(3):
    a[...,c]=np.where(strip,np.where(pat,gold[c],[0.20,0.01,0.015][c]),a[...,c])
for bx in (CX-44,CX+44):
    for by in (220,258,292,362,405,445):
        d=np.hypot(xx-bx,yy-by)
        for c in range(3): a[...,c]=np.where(d<7,gold[c]*(1.1-d/14),np.where(d<9,[0.15,0.08,0.02][c],a[...,c]))
im.pixels[:]=a[::-1].ravel(); im.pack()

# ---------- ブーツ(脛・足の肌面をそのまま平滑化+外側へ押し出してブーツ化) ----------
me=wear.data; gname={g.index:g.name for g in wear.vertex_groups}
bm=bmesh.new(); bm.from_mesh(me); dl=bm.verts.layers.deform.active
def dom(v):
    d=v[dl]; return gname[max(d.items(),key=lambda kv:kv[1])[0]] if d else ""
LEG=("shin","foot","heel","toe")
knee_z=B("shin.L").head_local.z
src=[f for f in bm.faces if me.materials[f.material_index].name=="body_bake" and f.calc_center_median().z<knee_z-0.02
     and any(dom(v).startswith(LEG) for v in f.verts)]
nv=list({v for f in src for v in f.verts})
bmesh.ops.remove_doubles(bm,verts=nv,dist=0.002)
src=[f for f in src if f.is_valid]; nv=list({v for f in src for v in f.verts})
# 足先: 元の足面を削除し、足頂点の凸包でブーツの靴部分を作り直す(ウェイトは最近傍頂点からコピー)
from mathutils.kdtree import KDTree as KD
FZ=0.10
oldfeet=[f for f in src if all(v.co.z<FZ for v in f.verts)]
hullf=[]
for side in (1,-1):
    fv=[v for v in nv if v.co.z<FZ+0.03 and v.co.x*side>0]
    kd=KD(len(fv))
    for i,v in enumerate(fv): kd.insert(v.co,i)
    kd.balance()
    ch=bmesh.ops.convex_hull(bm,input=[bm.verts.new(v.co) for v in fv])
    fs=[f for f in ch["geom"] if isinstance(f,bmesh.types.BMFace)]
    hv={v for f in fs for v in f.verts}
    for v in hv:
        _,i,_=kd.find(v.co)
        for g,val in fv[i][dl].items(): v[dl][g]=val
    hullf+=fs
bmesh.ops.delete(bm,geom=oldfeet,context="FACES")
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
src=[f for f in src if f.is_valid]+hullf
for f in hullf: f.material_index=0; f.smooth=True
nv=list({v for f in src for v in f.verts})
for _ in range(6): bmesh.ops.smooth_vert(bm,verts=[v for v in nv if v.co.z>FZ],factor=0.5,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bm.normal_update()
for v in nv: v.co+=v.normal*(0.016 if v.co.z<0.12 else 0.010)
hem=min(v.co.z for f in bm.faces if me.materials[f.material_index].name=="huku_bake" and f.calc_center_median().z<0.7 for v in f.verts)
iB,iR,iG=midx(wear,BOOT),midx(wear,BOOTR),midx(wear,GOLD)
for f in src: f.material_index=iB
def cut(co,no):
    g=list({v for f in bm.faces if f.material_index in(iB,iR,iG) for v in f.verts})+list({e for f in bm.faces if f.material_index in(iB,iR,iG) for e in f.edges})+[f for f in bm.faces if f.material_index in(iB,iR,iG)]
    bmesh.ops.bisect_plane(bm,geom=g,plane_co=co,plane_no=no)
cut(Vector((0,0,hem-0.035)),Vector((0,0,1))); cut(Vector((0,0,hem-0.05)),Vector((0,0,1)))
TOE=Vector((0,-0.5,-1)).normalized()
fy=min(v.co.y for f in bm.faces if f.material_index==iB for v in f.verts)
cut(Vector((0,fy+0.07,0.0)),Vector((0,-1,0.35)))
for f in bm.faces:
    if f.material_index not in(iB,iR,iG): continue
    c=f.calc_center_median(); z=c.z
    f.material_index=iR if z>hem-0.035 else (iG if z>hem-0.05 else iB)
    if (c-Vector((0,fy+0.07,0))).dot(Vector((0,-1,0.35)))>0 and z<0.1: f.material_index=iR   # つま先
bm.to_mesh(me); bm.free()

# ---------- 肩章(左肩)・立ち襟: 別メッシュを作ってwearへ結合 ----------
def new_obj(name):
    m=bpy.data.meshes.new(name); o=bpy.data.objects.new(name,m); bpy.context.scene.collection.objects.link(o); return o
wpts=[v.co.copy() for v in me.vertices]
def top_z(x,y0=-0.05,y1=0.07):
    zs=[p.z for p in wpts if abs(p.x-x)<0.006 and y0<p.y<y1 and 1.2<p.z<1.5]
    return max(zs)
xs=B("upper_arm.L").head_local.x
za,zb=top_z(xs-0.035),top_z(xs+0.035); ang=math.atan2(zb-za,0.07)
ep=new_obj("epaulette"); bm=bmesh.new()
bmesh.ops.create_cone(bm,cap_ends=True,segments=28,radius1=0.052,radius2=0.046,depth=0.01,matrix=Matrix.Diagonal((1.3,0.9,1,1)))
for k in range(11):
    t=math.radians(-75+150*k/10); p=Vector((math.cos(t)*0.052*1.3,math.sin(t)*0.052*0.9,-0.022))
    bmesh.ops.create_cone(bm,cap_ends=True,segments=6,radius1=0.004,radius2=0.0035,depth=0.04,matrix=Matrix.Translation(p))
ctr=Vector((xs,B("upper_arm.L").head_local.y,(za+zb)/2+0.008))
bmesh.ops.transform(bm,matrix=Matrix.Translation(ctr)@Matrix.Rotation(ang,4,'Y').inverted(),verts=bm.verts)
bm.to_mesh(ep.data); bm.free(); ep.data.materials.append(GOLD)
vg=ep.vertex_groups.new(name="shoulder.L"); vg.add(range(len(ep.data.vertices)),1.0,"REPLACE")
# 立ち襟(下が広がった円錐台。前は開き)
nk=B("neck").head_local
ring=[p for p in wpts if abs(p.z-nk.z)<0.01 and abs(p.x)<0.08]
r=max(math.hypot(p.x,p.y-nk.y) for p in ring) if ring else 0.05
col=new_obj("collar"); bm=bmesh.new()
seg=28; gap=math.radians(34); vs=[]
for k in range(seg+1):
    t=-math.pi/2+gap/2+(2*math.pi-gap)*k/seg
    for z,rr in ((nk.z-0.05,r+0.035),(nk.z+0.03,r+0.006)):
        vs.append(bm.verts.new((rr*math.cos(t),nk.y+rr*math.sin(t)*0.95,z)))
for k in range(seg): bm.faces.new((vs[2*k],vs[2*k+2],vs[2*k+3],vs[2*k+1]))
bmesh.ops.solidify(bm,geom=bm.faces[:],thickness=0.004)
bm.to_mesh(col.data); bm.free(); col.data.materials.append(COAT); col.data.materials.append(GOLD)
for p in col.data.polygons:
    if p.center.z>nk.z+0.022: p.material_index=1
vg=col.vertex_groups.new(name="chest"); vg.add(range(len(col.data.vertices)),1.0,"REPLACE")
bpy.ops.object.select_all(action="DESELECT")
# 肩章・立ち襟は上着の段(build_coat)で作り直すため、ここでは結合せず破棄する
for o in (ep,col): bpy.data.objects.remove(o)

# ---------- 左目の縦一文字の傷(レイキャストで顔表面のUVを求めて描く) ----------
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
hm=head.data; hm.calc_loop_triangles(); uvl=hm.uv_layers.active.data
tris=[t for t in hm.loop_triangles if hm.materials[t.material_index].name in("body_bake","eye")]
bvh=BVHTree.FromPolygons([tuple(hm.vertices[i].co for i in t.vertices) for t in tris] and [hm.vertices[i].co for i in range(len(hm.vertices))],[tuple(t.vertices) for t in tris])
iris=[p for p in hm.polygons if hm.materials[p.material_index].name=="eye" and p.center.x>0.01
      and 0.3<uvl[p.loop_indices[0]].uv.y<0.85]
ec=sum((p.center for p in iris),Vector())/len(iris)
img=bpy.data.images["body"]; W,H=img.size; a=np.array(img.pixels[:],dtype=np.float32).reshape(H,W,4)
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
pts=[]
for t in np.linspace(0,1,60):
    z=ec.z+0.036-t*0.078; x=ec.x+0.004*(t-0.5)
    loc,nrm,i,d=bvh.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
    if i is None: pts.append(None); continue
    tr=tris[i]
    if hm.materials[tr.material_index].name!="body_bake": pts.append(None); continue
    P=[hm.vertices[k].co for k in tr.vertices]; U=[uvl[k].uv.to_3d() for k in tr.loops]
    pts.append((barycentric_transform(loc,*P,*U).to_2d(),t))
for p,q in zip(pts,pts[1:]):
    if p is None or q is None: continue
    (p,t),(q,_)=p,q; px,py,qx,qy=p.x*W,p.y*H,q.x*W,q.y*H
    if abs(px-qx)+abs(py-qy)>30: continue   # UVシーム跨ぎは描かない
    tt=np.clip(((xx-px)*(qx-px)+(yy-py)*(qy-py))/((qx-px)**2+(qy-py)**2+1e-6),0,1)
    dist=np.hypot(xx-(px+tt*(qx-px)),yy-(py+tt*(qy-py)))
    wdt=0.8+2.4*math.sin(math.pi*t)
    m=np.clip((wdt-dist)/1.0,0,1)[...,None]*0.8
    a[...,:3]=a[...,:3]*(1-m)+np.array([0.60,0.27,0.28])*m
img.pixels[:]=a.ravel(); img.pack()
print("SCAR eye",ec,"hits",sum(p is not None for p in pts))
bpy.ops.wm.save_as_mainfile(filepath=S+"/nemo_s2.blend")
print("DONE2")
