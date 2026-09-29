# 白礼装のマント: 襟元の後ろから膝上まで垂れる半円マント(外=白、裏=黒地に花柄)+揺れ物ボーン(5列×4節)
import bpy, bmesh, sys, math, random
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
S=sys.argv[sys.argv.index("--")+1]
arm=bpy.data.objects["Armature"]; wear=bpy.data.objects["wear"]
B=lambda n: arm.data.bones[n].head_local
NZ=B("neck").z; HZ=B("hips").z
def mat(name,base,metal=0.0,rough=0.6):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True
    p=m.node_tree.nodes["Principled BSDF"]; p.inputs["Base Color"].default_value=(*base,1); p.inputs["Metallic"].default_value=metal; p.inputs["Roughness"].default_value=rough
    return m
TRIM=bpy.data.materials.get("trim_dark") or mat("trim_dark",(0.16,0.12,0.09),0.2,0.5)
def outer_mat(name,edges_u=True):
    W_=512; yy_,xx_=np.mgrid[0:W_,0:W_]/W_; v_=1-yy_   # v=0が裾
    im_=np.zeros((W_,W_,4),np.float32); im_[...,3]=1; im_[...,:3]=[0.74,0.72,0.68]
    def band(d,a,b): return (d>a)&(d<b)
    for dist in ([v_] + ([xx_,1-xx_] if edges_u else [])):
        m1=band(dist,0.010,0.022); m2=band(dist,0.032,0.038)
        im_[m1]=[0.42,0.36,0.28,1]; im_[m2]=[0.55,0.50,0.42,1]
    img_=bpy.data.images.new(name,W_,W_); img_.pixels[:]=im_[::-1].ravel(); img_.pack()
    m=mat(name,(1,1,1),0,0.5); nn=m.node_tree.nodes; tt=nn.new("ShaderNodeTexImage"); tt.image=img_
    m.node_tree.links.new(tt.outputs[0],nn["Principled BSDF"].inputs["Base Color"]); return m
OUT=outer_mat("cape_outer")
# 裏地テクスチャ: 黒地に灰色と金の花、うっすら菱形
TW,TH=512,1024; yy,xx=np.mgrid[0:TH,0:TW].astype(np.float32)
img=np.zeros((TH,TW,4),np.float32); img[...,3]=1
dia=(np.abs(((xx/64)%1)-0.5)+np.abs(((yy/96)%1)-0.5))
img[...,:3]=np.where((np.abs(dia-0.5)<0.02)[...,None],[0.10,0.09,0.08],[0.03,0.028,0.035])
random.seed(7)
for _ in range(38):
    cx,cy=random.uniform(0,TW),random.uniform(0,TH); R=random.uniform(28,70); gold=random.random()<0.35
    ang=np.arctan2(yy-cy,xx-cx); r=np.hypot(xx-cx,yy-cy)
    petal=R*(0.62+0.38*np.abs(np.cos(ang*2.5+random.uniform(0,3))))
    m=r<petal; core=r<R*0.22; edge=(r<petal)&(r>petal-2.5)
    col=np.array([0.55,0.42,0.16]) if gold else np.array([0.20,0.20,0.22])
    img[...,:3]=np.where(m[...,None],col*(0.55+0.45*(1-r/np.maximum(petal,1)))[...,None],img[...,:3])
    img[...,:3]=np.where(edge[...,None],col*0.4,img[...,:3])
    img[...,:3]=np.where(core[...,None],np.array([0.75,0.6,0.25]),img[...,:3])
limg=bpy.data.images.new("cape_lining",TW,TH); limg.pixels[:]=img[::-1].ravel(); limg.pack()
LIN=mat("cape_lining",(1,1,1),0.1,0.55); n=LIN.node_tree.nodes; t=n.new("ShaderNodeTexImage"); t.image=limg
LIN.node_tree.links.new(t.outputs[0],n["Principled BSDF"].inputs["Base Color"])

dg=bpy.context.evaluated_depsgraph_get(); bvh=BVHTree.FromObject(wear,dg)
CEN=Vector((0,0.01,0))
def surf(t,z):
    d=Vector((math.sin(t),-math.cos(t),0)); o=Vector((CEN.x,CEN.y,z))
    h,_,_,_=bvh.ray_cast(o+d*0.45,-d)
    return h if h and (Vector((h.x,h.y,0))-Vector((CEN.x,CEN.y,0))).length<0.3 else o+d*0.12
TA,TB=0.66*math.pi,1.34*math.pi   # 背中側の範囲(前は開く。左右対称)
NA=28; NR=12; ZTOP=NZ-0.15; ZBOT=0.56
angs=[TA+(TB-TA)*i/NA for i in range(NA+1)]
top=[surf(a,ZTOP) for a in angs]
def rad(p): return (Vector((p.x,p.y,0))-Vector((CEN.x,CEN.y,0))).length
pts=[]
for r in range(NR+1):
    f=r/NR; row=[]
    for a,p in zip(angs,top):
        lf=0.0   # 非対称な流れは再現しない(左右対称)
        z=ZTOP-(ZTOP-(ZBOT-0.10*lf))*f
        d=Vector((math.sin(a),-math.cos(a),0))
        rr=rad(p)+0.008+(0.14+0.16*lf)*f**0.9
        o=surf(a,z); rr=max(rr,rad(o)+0.015)   # 体・上着より外へ
        row.append(Vector((CEN.x,CEN.y,z))+d*rr)
    pts.append(row)
# 縦方向に半径をならす(でこぼこ防止)
for i in range(NA+1):
    col=[pts[r][i] for r in range(NR+1)]
    rs=[rad(p) for p in col]
    for r in range(1,NR+1): rs[r]=max(rs[r],rs[r-1])
    for r in range(NR+1):
        d=Vector((col[r].x-CEN.x,col[r].y-CEN.y,0)).normalized(); pts[r][i]=Vector((CEN.x,CEN.y,col[r].z))+d*rs[r]
# ---- 揺れ物ボーン: 5列×4節(胸の子) ----
NC,NSG=5,4
cols=[int(round(k*NA/(NC-1))) for k in range(NC)]
segrows=[int(round(s*NR/NSG)) for s in range(NSG+1)]
bpy.context.view_layer.objects.active=arm; bpy.ops.object.mode_set(mode="EDIT")
E=arm.data.edit_bones
for c,ci in enumerate(cols):
    prev=E["chest"]
    for s in range(NSG):
        b=E.new(f"cape_{c}_{s}"); b.head=pts[segrows[s]][ci]; b.tail=pts[segrows[s+1]][ci]; b.parent=prev; b.use_connect=(s>0); prev=b
bpy.ops.object.mode_set(mode="OBJECT")
# ---- メッシュ(外=白、裏=花柄、裾の縁=濃い縁取り)。ウェイトは列と節の補間 ----
o=bpy.data.objects.new("cape",bpy.data.meshes.new("cape")); bpy.context.scene.collection.objects.link(o)
bm=bmesh.new(); V=[[bm.verts.new(p) for p in row] for row in pts]
uv=bm.loops.layers.uv.new()
for r in range(NR):
    for i in range(NA):
        f=bm.faces.new((V[r][i],V[r][i+1],V[r+1][i+1],V[r+1][i])); f.smooth=True
        f.material_index=0
        for l,(rr,ii) in zip(f.loops,((r,i),(r,i+1),(r+1,i+1),(r+1,i))): l[uv].uv=(ii/NA,1-rr/NR)
bm.normal_update()
nf=len(bm.faces)
res=bmesh.ops.solidify(bm,geom=bm.faces[:],thickness=0.008)
for f in bm.faces:   # 内側を向く面は裏地
    c=f.calc_center_median(); rd=Vector((c.x-CEN.x,c.y-CEN.y,0)).normalized()
    if f.normal.dot(rd)<-0.3 and f.material_index!=2: f.material_index=1
bm.to_mesh(o.data); bm.free()
for m_ in (OUT,LIN,TRIM): o.data.materials.append(m_)
vg={}
def g(name):
    if name not in vg: vg[name]=o.vertex_groups.new(name=name)
    return vg[name]
for v in o.data.vertices:
    a=math.atan2(v.co.x-CEN.x,-(v.co.y-CEN.y)); a=a if a>0 else a+2*math.pi
    cf=max(0,min(NC-1-1e-6,(a-TA)/(TB-TA)*(NC-1))); c0=int(cf); wc=cf-c0
    fz=max(0,min(1,(ZTOP-v.co.z)/(ZTOP-ZBOT))); sf=fz*NSG
    if sf<0.35:   # 付け根は胸に固定
        w=sf/0.35; g("chest").add([v.index],1-w,"REPLACE")
        for c,wcc in ((c0,1-wc),(c0+1,wc)):
            if wcc>0: g(f"cape_{c}_0").add([v.index],w*wcc,"ADD")
        continue
    # 節の中心で1、隣の節へなめらかに移る
    sc=sf-0.5; s0=max(0,min(NSG-1,int(math.floor(sc)))); s1=min(NSG-1,s0+1); ws=max(0,min(1,sc-s0))
    for c,wcc in ((c0,1-wc),(c0+1,wc)):
        if wcc<=0: continue
        for s_,w_ in ((s0,1-ws),(s1,ws)):
            if w_>0: g(f"cape_{c}_{s_}").add([v.index],wcc*w_,"ADD")
md=o.modifiers.new("Armature","ARMATURE"); md.object=arm; o.parent=arm
# ==== 肩ケープ(襟元で束ね、両肩〜上腕を覆う。胸・上腕に追従) ====
OUTc=outer_mat("capelet_outer"); LINc=LIN.copy(); LINc.name="capelet_lining"
CA,CB=0.075*math.pi,1.925*math.pi; NCA=56; NCR=10
nk=B("neck"); ring=[v.co for v in wear.data.vertices if abs(v.co.z-(nk.z-0.005))<0.008 and abs(v.co.x)<0.09]
RC=max(math.hypot(p.x,p.y-nk.y) for p in ring)+0.022
ZC0=NZ-0.035; ZC1=NZ-0.25   # ZC1はUV用の旧基準(未使用)
# 各列を首元から外へ「布を掛ける」ように1本ずつ伸ばす: 肩・上腕の上面に乗るあいだは沿わせ、
# 支えが無くなれば重力で垂らす。長さは一定なので腕の上では短く止まり、腕は裾の下から出る。
CL=0.15; STEP=CL/NCR; CLR=0.022
# 支え判定用: 首より下の体・服だけ(頭や髪に引っかからないように)
_bm=bmesh.new(); _bm.from_object(wear,dg)
bmesh.ops.delete(_bm,geom=[f for f in _bm.faces if max(v.co.z for v in f.verts)>NZ-0.01],context="FACES")
bvh=BVHTree.FromBMesh(_bm); _bm.free()
def settle(p):
    h,_,_,_=bvh.ray_cast(p+Vector((0,0,0.12)),Vector((0,0,-1)),0.12)   # 真上から見た支え(肩・腕の上面)
    if h is not None and p.z<h.z+CLR: p=Vector((p.x,p.y,h.z+CLR))
    d=Vector((p.x,p.y-nk.y,0)); L=d.length
    if L>1e-4:   # 外側から首の軸へ水平に撃ち、いちばん外の面より内に入った点は外へ出す
        d/=L; h,_,_,_=bvh.ray_cast(Vector((0,nk.y,p.z))+d*0.6,-d,0.6)
        if h is not None:
            Lh=(Vector((h.x,h.y-nk.y,0))).length
            if L<Lh+CLR: p=Vector((0,nk.y,p.z))+d*(Lh+CLR)
    return p
cang=[CA+(CB-CA)*i/NCA for i in range(NCA+1)]
ccols=[]
for a_ in cang:
    d=Vector((math.sin(a_),-math.cos(a_)*0.97,0))
    p=settle(Vector((0,nk.y,ZC0))+d*(RC+0.012)); col=[p]; dr=(d+Vector((0,0,-0.45))).normalized()
    for r in range(NCR):
        q=settle(p+dr*STEP)
        dr=(q-p).normalized(); dr=(dr+Vector((0,0,-0.35))).normalized()   # 少しずつ垂れる
        q=p+(q-p).normalized()*STEP; q=settle(q); col.append(q); p=q
    ccols.append(col)
cp=[[ccols[i][r] for i in range(len(cang))] for r in range(NCR+1)]
for it in range(3):   # 隣の列とならして段差をなくす
    new=[row[:] for row in cp]
    for r in range(1,NCR+1):
        for i in range(1,len(cang)-1):
            new[r][i]=settle(cp[r][i].lerp((cp[r][i-1]+cp[r][i+1])*0.5,0.4))
    cp=new
co=bpy.data.objects.new("capelet",bpy.data.meshes.new("capelet")); bpy.context.scene.collection.objects.link(co)
bm=bmesh.new(); V=[[bm.verts.new(p) for p in row] for row in cp]
for r in range(NCR):
    for i in range(NCA):
        f_=bm.faces.new((V[r][i],V[r][i+1],V[r+1][i+1],V[r+1][i])); f_.smooth=True
# 立ち襟(肩ケープの首元に立つ、上縁は縁取り色)
top=V[0]; cr=[]
for i,a_ in enumerate(cang):
    d=Vector((math.sin(a_),-math.cos(a_)*0.97,0)); cr.append([bm.verts.new(Vector((0,nk.y,NZ+0.03))+d*(RC-0.004)),bm.verts.new(Vector((0,nk.y,NZ+0.04))+d*(RC-0.002))])
for i in range(NCA):
    f_=bm.faces.new((top[i],top[i+1],cr[i+1][0],cr[i][0])); f_.smooth=True
    f_=bm.faces.new((cr[i][0],cr[i+1][0],cr[i+1][1],cr[i][1])); f_.material_index=2
# 裏地: 表を複製して内側へ5mm寄せ、向きを反転。ケープ本体は格子から求めた法線、襟は首の軸への放射方向
bm.normal_update(); bm.verts.index_update(); vn={v:v.normal.copy() for v in bm.verts}
outer=bm.faces[:]
r_=bmesh.ops.duplicate(bm,geom=outer)
inner=[e for e in r_["geom"] if isinstance(e,bmesh.types.BMFace)]
vmap=r_["vert_map"]
for src,dst in vmap.items():
    if not isinstance(src,bmesh.types.BMVert) or src not in vn or dst in vn: continue
    d=Vector((src.co.x,src.co.y-nk.y,0)).normalized(); rr=src.index//(NCA+1) if src.index<(NCR+1)*(NCA+1) else -1
    n_=vn[src]
    if n_.dot(d)<0: n_=-n_
    w_=0.0 if rr<0 else min(1.0,rr/2)   # 襟と付け根は放射方向、そこから下は面の法線へ徐々に切り替え
    dst.co=src.co-(d.lerp(n_,w_)).normalized()*0.004
bmesh.ops.reverse_faces(bm,faces=inner)
for f_ in inner:
    if f_.material_index!=2: f_.material_index=1
bm.to_mesh(co.data); bm.free()
for m_ in (OUTc,LINc,TRIM): co.data.materials.append(m_)
rowf=co.data.attributes.new("capelet_row","FLOAT","POINT")
nrow=(NCR+1)*(NCA+1)
for v in co.data.vertices:
    k=v.index%(len(co.data.vertices)//2) if v.index>=nrow else v.index
    rowf.data[v.index].value=(k//(NCA+1))/NCR if k<nrow else 0.0
cvg={}
def cg(nm):
    if nm not in cvg: cvg[nm]=co.vertex_groups.new(name=nm)
    return cvg[nm]
shx=abs(B("upper_arm.L").x)
for v in co.data.vertices:
    wa=max(0,min(1,(abs(v.co.x)-shx+0.03)/0.08))*0.9; bone="upper_arm.L" if v.co.x>0 else "upper_arm.R"
    cg("chest").add([v.index],1-wa,"REPLACE")
    if wa>0: cg(bone).add([v.index],wa,"REPLACE")
md2=co.modifiers.new("Armature","ARMATURE"); md2.object=arm; co.parent=arm
# 紐の結び目と房(襟元の前)
CORD=bpy.data.materials.get("cord") or mat("cord",(0.78,0.72,0.58),0.1,0.5)
def tube(b2,P,r=0.0028):
    prev_=None
    for i,p in enumerate(P):
        tg=(P[min(i+1,len(P)-1)]-P[max(i-1,0)]).normalized(); a1=tg.orthogonal().normalized(); b1=tg.cross(a1)
        rg=[b2.verts.new(p+(a1*math.cos(k*math.pi/3)+b1*math.sin(k*math.pi/3))*r) for k in range(6)]
        if prev_:
            for k in range(6): b2.faces.new((prev_[k],prev_[(k+1)%6],rg[(k+1)%6],rg[k]))
        prev_=rg
kn=Vector((0,nk.y-RC*0.97-0.012,NZ-0.03))
L_=Vector((math.sin(CA),-math.cos(CA)*0.97,0))*(RC+0.004)+Vector((0,nk.y,NZ-0.02)); R_=Vector((-L_.x,L_.y,L_.z))
ko=bpy.data.objects.new("cape_knot",bpy.data.meshes.new("cape_knot")); bpy.context.scene.collection.objects.link(ko)
b2=bmesh.new()
for e in (L_,R_): tube(b2,[e.lerp(kn,t)+Vector((0,-0.004*math.sin(math.pi*t),-0.012*math.sin(math.pi*t))) for t in np.linspace(0,1,10)])
for sx in (1,-1):   # 蝶結びの輪
    P=[kn+Vector((sx*0.022*math.sin(math.pi*t),-0.004,0.010*math.sin(2*math.pi*t))) for t in np.linspace(0,1,14)]; tube(b2,P,0.0025)
bmesh.ops.create_uvsphere(b2,u_segments=10,v_segments=8,radius=0.009,matrix=Matrix.Translation(kn))
for dx,ln in ((-0.006,0.085),(0.007,0.07)):
    P=[kn+Vector((dx*t*2,-0.004*t,-ln*t)) for t in np.linspace(0,1,10)]; tube(b2,P)
    bmesh.ops.create_cone(b2,cap_ends=True,segments=8,radius1=0.007,radius2=0.003,depth=0.022,matrix=Matrix.Translation(P[-1]+Vector((0,0,-0.008))))
b2.to_mesh(ko.data); b2.free(); ko.data.materials.append(CORD)
for p_ in ko.data.polygons: p_.use_smooth=True
ko.vertex_groups.new(name="chest").add(range(len(ko.data.vertices)),1.0,"REPLACE")
ko.modifiers.new("Armature","ARMATURE").object=arm; ko.parent=arm
EXTRA=[co,ko]
bpy.ops.object.select_all(action="DESELECT"); o.select_set(True)
for e_ in EXTRA: e_.select_set(True)
wear.select_set(True); bpy.context.view_layer.objects.active=wear; bpy.ops.object.join()
# 結合時にUVが引き継がれないため、結合後にマントの面へ角度と高さからUVを割り当てる
me=wear.data; uvd=me.uv_layers.active.data; capem={i for i,m in enumerate(me.materials) if m and m.name in("cape_outer","cape_lining")}; capc={i for i,m in enumerate(me.materials) if m and m.name in("capelet_outer","capelet_lining")}
for p_ in me.polygons:
    if p_.material_index in capc:
        for li in p_.loop_indices:
            co_=me.vertices[me.loops[li].vertex_index].co
            a_=math.atan2(co_.x,-(co_.y-nk.y)); a_=a_ if a_>0 else a_+2*math.pi
            uvd[li].uv=((a_-CA)/(CB-CA),min(0.5,1-me.attributes['capelet_row'].data[me.loops[li].vertex_index].value))
        continue
    if p_.material_index in capem:
        for li in p_.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co
            a_=math.atan2(co.x-CEN.x,-(co.y-CEN.y)); a_=a_ if a_>0 else a_+2*math.pi
            uvd[li].uv=((a_-TA)/(TB-TA),1-(ZTOP-co.z)/(ZTOP-ZBOT))
bpy.ops.wm.save_as_mainfile(filepath=S+"/nemo_s2k_white.blend")
print("DONEK",len(cols),"cols")
