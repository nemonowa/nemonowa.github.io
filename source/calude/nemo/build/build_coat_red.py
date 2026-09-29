# 服装C(赤コート): 朱赤のロングコート(ダブルの前合わせ・高い立ち襟・肩当て・前が割れた長い裾+揺れ物ボーン)、
# 左腕は黒革の袖とベルト、義手は発光を消した黒い装甲+ベルトとリベット、丸いオレンジのサングラス。
# 土台は軍服と同じbuild_base(黒シャツ・コンバットパンツ・ブーツ)の出力 nemo_s2o.blend に重ねる。
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
COAT=mat("coat_vermilion",(0.52,0.045,0.018),0,0.88)       # 朱赤(sRGB 約#BE3B22)
LINING=mat("coat_lining_red",(0.16,0.006,0.004),0,0.85)     # 裏地・合わせ目の影
TRIM=mat("coat_trim_red",(0.30,0.02,0.01),0,0.85)          # 袖口・裾の縁
LEATHER=mat("leather_black",(0.012,0.012,0.014),0.1,0.35)  # 左腕の黒革
BTN=mat("button_black",(0.01,0.01,0.012),0.3,0.3)
SILVER=mat("rivet_silver",(0.6,0.6,0.63),1.0,0.25)
STRAP=bpy.data.materials["strap"]
# 義手: 発光を消して艶のある黒い装甲に
pro=bpy.data.materials["prosthetic"]; pn=pro.node_tree.nodes["Principled BSDF"]
for l in list(pro.node_tree.links):
    if l.to_socket==pn.inputs["Emission Strength"]: pro.node_tree.links.remove(l)
pn.inputs["Emission Strength"].default_value=0.0; pn.inputs["Base Color"].default_value=(0.02,0.02,0.024,1); pn.inputs["Metallic"].default_value=0.6; pn.inputs["Roughness"].default_value=0.38

bm=bmesh.new(); bm.from_mesh(me); dl=bm.verts.layers.deform.active
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

# ---- 0. 隠れる部品の削除: ズボンのベルト類、左前腕の発光ギア(画面・発光リング) ----
kill=[f for f in bm.faces if f.is_valid and (MN(f)=="buckle" or (MN(f) in("strap","pants","pants_pocket","pants_outer") and HZ+0.02<C(f).z<HZ+0.09 and abs(C(f).x)<0.25))]
kill+=[f for f in bm.faces if f.is_valid and MN(f) in("shirt_placket","gold","gem") and C(f).z>NZ-0.10 and abs(C(f).x)<0.12]   # シャツ襟・ブローチは高い襟の下に隠れる
_fa=B("forearm.L"); _dF=(B("hand.L")-_fa).normalized(); _lF=(B("hand.L")-_fa).length
def _on_forearm(c):
    q=(c-_fa).dot(_dF); return -0.02<q<_lF+0.02 and ((c-_fa)-_dF*q).length<0.12
kill+=[f for f in bm.faces if f.is_valid and MN(f) in("robo_face","armgear_plastic","green_emit","anim_logo","wear_metal","glass","huku_bake","backpack_metal","backpack_plastic","backpack_nm") and _on_forearm(C(f))]
bmesh.ops.delete(bm,geom=list(set(kill)),context="FACES")
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
# ---- 1. コート胴(シャツの上、両上腕+右前腕。前はダブルで閉じる) ----
def coat_ok(f):
    d=fdom(f); c=C(f)
    return d.startswith(("hips","spine","chest","shoulder","upper_arm","forearm.R","forearm.twist.R")) and c.z>HZ-0.01
iC=midx(COAT); iL=midx(LINING); iT=midx(TRIM); iK=midx(LEATHER)
shell([f for f in by(SHIRT) if coat_ok(f)],0.011,iC,3)
XO=0.045   # 前の重なり線(左前身頃が右に重なる)
for x in (XO,XO+0.005): cut(by({iC}),Vector((x,0,0)),Vector((1,0,0)))
for f in by({iC}):
    c=C(f)
    if c.y<-0.01 and XO<c.x<XO+0.005 and c.z<NZ-0.03: f.material_index=iL
def arm_cut(co,d,band,mi):
    cut(by({iC,iK,iT,midx(pro)}),co,d); cut(by({iC,iK,iT,midx(pro)}),co-d*band,d)
    bmesh.ops.delete(bm,geom=[f for f in by({iC,iK,iT}) if (C(f)-co).dot(d)>0 and (C(f)-co).length<0.15],context="FACES")
    for f in by({iC,iK,midx(pro)}):
        q=(C(f)-co).dot(d)
        if -band<q<=0 and (C(f)-co).length<0.12: f.material_index=mi
dR=(B("hand.R")-B("forearm.R")).normalized(); dL=(B("forearm.L")-B("upper_arm.L")).normalized()
arm_cut(B("hand.R")-dR*0.005,dR,0.035,iT)
iP=midx(pro)
# 左袖: 赤い袖が肘のすぐ上まで義手を覆い隠す(義手は上腕の下の方から始まり、袖口の下から肘の関節と前腕が出る)
uaL=B("upper_arm.L"); lenL=(B("forearm.L")-uaL).length
kz=B("forearm.L")-dL*0.012
arm_cut(kz,dL,0.022,iT)
for v in {v for f in by({iC,iT}) for v in f.verts}:   # 袖口を少し広げる
    q=(v.co-kz).dot(dL); rad=(v.co-kz)-dL*q
    if -0.07<q<=0.001 and rad.length<0.09 and v.co.x>0.2: v.co+=rad.normalized()*0.008*(1+q/0.07)
ZJ=HZ+0.10   # 胴の下端。裾はこの縁の頂点をそのまま共有して下へ伸ばす(一枚のメッシュなので継ぎ目の陰影も出ない)
cut(by({iC,iL}),Vector((0,0,ZJ)),Vector((0,0,1)))
bmesh.ops.delete(bm,geom=[f for f in by({iC,iL}) if C(f).z<ZJ and abs(C(f).x)<0.25],context="FACES")

# ---- 2. 裾(胴の下端の頂点を共有して一続きに脛の下まで。前は腰の下から割れて広がる)+揺れ物ボーン ----
cbvh=BVHTree.FromBMesh(bm)
ZB=0.27; NR=18
CEN=Vector((0,0.005,ZJ))
def hit_r(t,z,lim=0.30):   # 中心軸からtの向きに見た、いちばん外の面までの距離
    d=Vector((math.sin(t),-math.cos(t),0)); o=Vector((CEN.x,CEN.y,z))
    h,_,_,_=cbvh.ray_cast(o+d*0.5,-d,0.5)
    return (Vector((h.x,h.y,0))-Vector((CEN.x,CEN.y,0))).length if h and (Vector((h.x,h.y,0))-Vector((CEN.x,CEN.y,0))).length<lim else None
coatv={v for f in by({iC,iL}) for v in f.verts}
ring=[v for v in coatv if abs(v.co.z-ZJ)<1e-4 and abs(v.co.x)<0.25 and v.is_boundary]
ang=lambda p: math.atan2(p.x-CEN.x,-(p.y-CEN.y))
st=min((v for v in ring if v.co.y<0),key=lambda v: abs(v.co.x-XO))   # 前の重なり線(ここで裾が割れる)
Tc=ang(st.co)
ring.sort(key=lambda v:(ang(v.co)-Tc)%(2*math.pi))
ring=[v for i,v in enumerate(ring) if i==0 or (v.co-ring[i-1].co).length>0.002]
AR=[(ang(v.co)-Tc)%(2*math.pi) for v in ring]+[2*math.pi]
R0=[(Vector((v.co.x-CEN.x,v.co.y-CEN.y,0))).length for v in ring]; R0.append(R0[0])
NA=len(ring)
def gap(s): return 0.58*s**1.1   # 前の割れ(ラジアン、片側)。上端は閉じている
RR=[R0]; TT=[[Tc+a for a in AR]]
for j in range(1,NR+1):
    s_=j/NR; z=ZJ-(ZJ-ZB)*s_; g=gap(s_); th=[Tc+g+a*(2*math.pi-2*g)/(2*math.pi) for a in AR]; rr=[]
    for i,t in enumerate(th):
        r=R0[i]*(1+0.10*s_**1.3)+0.05*s_**1.5
        hr=hit_r(t,z)
        if hr is not None and j>1: r=max(r,hr+0.022)
        rr.append(max(r,RR[-1][i]))
    for _ in range(3): rr=[rr[0]]+[(rr[i-1]+2*rr[i]+rr[i+1])/4 for i in range(1,NA)]+[rr[NA]]
    RR.append([max(a,b) for a,b in zip(rr,RR[-1])]); TT.append(th)
KF=15   # 一周の折り山の数(テクスチャの陰影と位置をそろえるため3の倍数)
def fold(t,s_): return 1+0.05*min(1,s_*1.4)**1.2*math.cos(KF*t)
RR=[RR[0]]+[[r*fold(t,j/NR) for r,t in zip(RR[j],TT[j])] for j in range(1,NR+1)]
ZS=[ZJ-(ZJ-ZB)*j/NR for j in range(NR+1)]
NC,NSG=8,4
for c in range(NC):
    for sg in range(NSG): wear.vertex_groups.new(name=f"cape_{c}_{sg}")
gid={g.name:g.index for g in wear.vertex_groups}
def wgt(j,a):
    if j<=1: return {"hips":1.0}
    cf=min(NC-1-1e-6,a/(2*math.pi)*(NC-1)); c0=int(cf); wc=cf-c0
    sf=(j-1)/(NR-1)*NSG; out={}
    if sf<0.5:
        w=sf/0.5; out["hips"]=1-w
        for c,wcc in ((c0,1-wc),(c0+1,wc)):
            if wcc>0: out[f"cape_{c}_0"]=out.get(f"cape_{c}_0",0)+w*wcc
        return out
    sc=sf-0.5; s0=max(0,min(NSG-1,int(math.floor(sc)))); s1=min(NSG-1,s0+1); ws=max(0,min(1,sc-s0))
    for c,wcc in ((c0,1-wc),(c0+1,wc)):
        for sg,w_ in ((s0,1-ws),(s1,ws)):
            if wcc*w_>0: k=f"cape_{c}_{sg}"; out[k]=out.get(k,0)+wcc*w_
    return out
def setw(v,w):
    v[dl].clear()
    for k,x in w.items(): v[dl][gid[k]]=x
V=[ring+[ring[0]]]
for j in range(1,NR+1):
    row=[]
    for i in range(NA+1):
        t=TT[j][i]; r=RR[j][i]; v=bm.verts.new((CEN.x+math.sin(t)*r,CEN.y-math.cos(t)*r,ZS[j])); setw(v,wgt(j,AR[i])); row.append(v)
    V.append(row)
# 焼け焦げ・弾痕で裂けた裾: 列ごとに裾の縁を不規則に持ち上げ、V字の裂け目とギザギザを作る
# (面は抜かずに下の数段を縦に詰めるので、裂け目の縁も布の面のままなめらかにつながる)
import random
rnd=random.Random(11); LIFT=[0.0]*(NA+1)
for _ in range(10):   # 深い裂け目(V字)
    ic=rnd.uniform(3,NA-3); w=rnd.uniform(1.2,3.2); d=rnd.uniform(0.05,0.19)
    for i in range(NA+1):
        k=1-abs(i-ic)/w
        if k>0: LIFT[i]=max(LIFT[i],d*k**rnd.uniform(0.7,1.3))
for i in range(NA+1):   # 細かいほつれ(歯のようなギザギザ)
    LIFT[i]+=rnd.uniform(0,0.028)*(1 if i%2 else 0.35)
LIFT[0]=min(LIFT[0],0.01); LIFT[NA]=min(LIFT[NA],0.01)
JS=NR-6
for i in range(NA+1):
    col=[V[j][i].co.copy() for j in range(JS,NR+1)]
    z0,z1=col[0].z,col[-1].z+LIFT[i]
    for jj,j in enumerate(range(JS,NR+1)):
        zt=z0+(z1-z0)*jj/(NR-JS)
        for k in range(len(col)-1):   # 元の縦の線に沿って、その高さの位置を取る
            if col[k].z>=zt>=col[k+1].z or k==len(col)-2:
                f_=(col[k].z-zt)/max(1e-6,col[k].z-col[k+1].z); V[j][i].co=col[k].lerp(col[k+1],min(1,max(0,f_))); break
skirt=[]
for j in range(NR):
    for i in range(NA):
        q=(V[j][i],V[j][i+1],V[j+1][i+1],V[j+1][i])
        if len(set(q))<4: continue
        f=bm.faces.new(q); f.smooth=True; skirt.append(f)
        f.material_index=iT if j==NR-1 else (iL if i in (0,NA-1) and j>=1 else iC)
bm.normal_update()
f0=skirt[len(skirt)//2]; c0_=f0.calc_center_median()
if f0.normal.dot(Vector((c0_.x-CEN.x,c0_.y-CEN.y,0)))<0: bmesh.ops.reverse_faces(bm,faces=skirt)
# 裏地: 裾の面を複製して4mm内側へ、向きを反転
r_=bmesh.ops.duplicate(bm,geom=[f for f in skirt])
inner=[e for e in r_["geom"] if isinstance(e,bmesh.types.BMFace)]; vm=r_["vert_map"]
for v in {v for f in inner for v in f.verts}:
    d=Vector((v.co.x-CEN.x,v.co.y-CEN.y,0)).normalized(); v.co-=d*0.007
bmesh.ops.reverse_faces(bm,faces=inner)
for f in inner: f.material_index=iL
# 厚手の布に見えるよう、前端と裾の切り口に厚みの面を張る
def wall(a,b,mi):
    try: f=bm.faces.new((a,b,vm[b],vm[a])); f.material_index=mi
    except (ValueError,KeyError): pass
BURN=mat("coat_burnt",(0.045,0.012,0.008),0,0.95); iB=midx(BURN)
for j in range(1,NR):   # 前端の切り口
    wall(V[j][0],V[j+1][0],iT); wall(V[j+1][NA],V[j][NA],iT)
for i in range(NA): wall(V[NR][i+1],V[NR][i],iB)   # 裾の裂けた縁は焦げ色の切り口
for f in skirt:   # 裾の最下段は焦げて黒ずむ
    if f.material_index==iT: f.material_index=iB
# 揺れ物ボーンの位置(各列の角度に最も近い頂点列)
colI=[min(range(NA+1),key=lambda i:abs(AR[i]-c/(NC-1)*2*math.pi)) for c in range(NC)]
segr=[1+int(round(s*(NR-1)/NSG)) for s in range(NSG+1)]
BP=[[V[j][i].co.copy() for j in range(NR+1)] for i in colI]
bm.to_mesh(me); bm.free()
bpy.context.view_layer.objects.active=arm; bpy.ops.object.mode_set(mode="EDIT")
E=arm.data.edit_bones
def outp(p,k=0.012):
    d=Vector((p.x-CEN.x,p.y-CEN.y,0)).normalized(); return p+d*k
for c in range(NC):
    prev=E["hips"]
    for sg in range(NSG):
        b=E.new(f"cape_{c}_{sg}"); b.head=outp(BP[c][segr[sg]]); b.tail=outp(BP[c][segr[sg+1]]); b.parent=prev; b.use_connect=(sg>0); prev=b
bpy.ops.object.mode_set(mode="OBJECT")
print("SKIRT ring",NA)

# ---- 3. 小物 ----
def new_obj(name):
    o=bpy.data.objects.new(name,bpy.data.meshes.new(name)); bpy.context.scene.collection.objects.link(o); return o
dg=bpy.context.evaluated_depsgraph_get(); bvh=BVHTree.FromObject(wear,dg)
def front_hit(x,z):
    loc,n,_,_=bvh.ray_cast(Vector((x,-1,z)),Vector((0,1,0))); return loc,n
parts=[]
def piece(fn,m,bone,name,weights=None):
    o=new_obj(name); b2=bmesh.new(); fn(b2); b2.to_mesh(o.data); b2.free()
    for mm in (m if isinstance(m,list) else [m]): o.data.materials.append(mm)
    for p in o.data.polygons: p.use_smooth=True
    if weights:
        for v in o.data.vertices:
            for bn,w in weights(v.co):
                if w>0: (o.vertex_groups.get(bn) or o.vertex_groups.new(name=bn)).add([v.index],w,"REPLACE")
    else: o.vertex_groups.new(name=bone).add(range(len(o.data.vertices)),1.0,"REPLACE")
    parts.append(o); return o
# 高い立ち襟(前は少し開き、上へ向かって外に開く。内側は濃い赤)
nk=B("neck"); ring=[v.co for v in me.vertices if abs(v.co.z-(nk.z-0.005))<0.008 and abs(v.co.x)<0.07]
R=max(math.hypot(p.x,p.y-nk.y) for p in ring)+0.014
# 頭・髪・首の肌(襟が食い込まないように押し出す相手)
_hb=bmesh.new()
for on in ("head","hair"):
    _t=bmesh.new(); _t.from_object(bpy.data.objects[on],dg); _t.transform(bpy.data.objects[on].matrix_world)
    _m=bpy.data.meshes.new("_tmp"); _t.to_mesh(_m); _hb.from_mesh(_m); _t.free(); bpy.data.meshes.remove(_m)
_t=bmesh.new(); _t.from_mesh(me)
bmesh.ops.delete(_t,geom=[f for f in _t.faces if not (me.materials[f.material_index].name in("body_bake","body_nm") and f.calc_center_median().z>NZ-0.08)],context="FACES")
_m=bpy.data.meshes.new("_tmp"); _t.to_mesh(_m); _hb.from_mesh(_m); _t.free(); bpy.data.meshes.remove(_m)
HBV=BVHTree.FromBMesh(_hb); _hb.free()
def clear_head(p,clr=0.013):
    for _ in range(4):   # 首の軸から水平に外へ押し出す
        loc,n,_,dist=HBV.find_nearest(p)
        if loc is None or dist>=clr: break
        d=Vector((p.x,p.y-nk.y,0)).normalized(); p=p+d*(clr-dist+0.002)
    return p
def collar(b2):
    seg=40; gp=math.radians(22); rows_=[]
    for k in range(seg+1):
        t=-math.pi/2+gp/2+(2*math.pi-gp)*k/seg
        d=Vector((math.cos(t),math.sin(t)*0.95,0)); zb=nk.z-0.05
        h,_,_,_=bvh.ray_cast(Vector((0,nk.y,zb))+d*0.3,-d)
        pb=(h if h and (h-Vector((0,nk.y,zb))).length<0.15 else Vector((0,nk.y,zb))+d*(R+0.02))+d*0.004
        fr=abs(math.sin(t)); ff=max(0.0,-math.sin(t))   # 前後で外へ開く / 前(あごの下)は低く
        rows_.append([b2.verts.new(pb)]+[b2.verts.new(clear_head(Vector((0,nk.y,z))+d*rr)) for z,rr in ((nk.z+0.035-0.012*ff,R+0.008),(nk.z+0.058+0.008*fr-0.040*ff**1.5,R+0.026+0.012*fr))])
    for k in range(seg):
        for j in range(2):
            f=b2.faces.new((rows_[k][j],rows_[k+1][j],rows_[k+1][j+1],rows_[k][j+1])); f.material_index=0
    b2.normal_update()
    r_=bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=0.004)
    for f in b2.faces:
        c=f.calc_center_median(); d=Vector((c.x,c.y-nk.y,0))
        if f.normal.dot(d)<0: f.material_index=1
def collar_w(co):
    t=max(0,min(1,(co.z-(nk.z-0.02))/0.06)); return (("chest",1-0.4*t),("neck",0.4*t))
piece(collar,[COAT,LINING],"chest","coat_collar",collar_w)
# 肩当て: 肩の上に沿う2枚重ねのフラップ(左右)
def flap(sx):
    def f(b2):
        sh=B("upper_arm.L" if sx>0 else "upper_arm.R"); NU,NV=9,7
        G=[]
        for iu in range(NU+1):
            row=[]
            for iv in range(NV+1):
                x=sx*(0.105+(abs(sh.x)+0.085-0.105)*iu/NU); y=-0.085+0.17*iv/NV
                h,_,_,_=bvh.ray_cast(Vector((x,y,NZ+0.02)),Vector((0,0,-1)),0.3)
                z=(h.z if h else (row[-1].co.z if row else NZ-0.06))+0.012
                if iu>0: z=min(z,G[iu-1][iv].co.z+0.004)   # 外へ向かって上がらない
                row.append(b2.verts.new((x,y,z)))
            G.append(row)
        for iu in range(NU):
            for iv in range(NV):
                q=(G[iu][iv],G[iu+1][iv],G[iu+1][iv+1],G[iu][iv+1]); b2.faces.new(q if sx>0 else q[::-1])
        # 外側の縁は腕の側面へ垂らす
        for iv in range(NV+1):
            v=G[NU][iv]; v.co.z-=0.02; v.co.x+=sx*0.006
        b2.normal_update(); bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=0.004)
    return f
for sx in (1,-1):
    s_="L" if sx>0 else "R"; shx=abs(B("upper_arm."+s_).x)
    piece(flap(sx),COAT,None,"flap"+s_,lambda co,s_=s_,shx=shx: (("shoulder."+s_,1-max(0,min(1,(abs(co.x)-shx+0.02)/0.08))),("upper_arm."+s_,max(0,min(1,(abs(co.x)-shx+0.02)/0.08)))))
# ---- 共布のストラップ(布を縛る・留める飾り)。重なる相手(肩・裾)の頂点ウェイトを写して一緒に動かす ----
from mathutils.kdtree import KDTree
KDW=KDTree(len(me.vertices))
for v in me.vertices: KDW.insert(v.co,v.index)
KDW.balance(); GN={g.index:g.name for g in wear.vertex_groups}
def near_w(co):
    _,i,_=KDW.find(co); return [(GN[g.group],g.weight) for g in me.vertices[i].groups if g.weight>0.01]
def strap(pts,nrms,w,name,wfn=None,btn=(0,),t=0.003):
    def f(b2):
        L=[]
        for i,(p,n) in enumerate(zip(pts,nrms)):
            tg=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized(); sd=n.cross(tg).normalized()*w/2
            L.append((b2.verts.new(p-sd),b2.verts.new(p+sd)))
        for i in range(len(L)-1): b2.faces.new((L[i][0],L[i+1][0],L[i+1][1],L[i][1]))
        # 先端は剣先に
        tip=b2.verts.new(pts[-1]+(pts[-1]-pts[-2]).normalized()*w*0.55); b2.faces.new((L[-1][0],tip,L[-1][1]))
        bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=t)
    piece(f,COAT,None,name,wfn or near_w)
    for k in btn:
        q=pts[k]+nrms[k]*(t+0.002)
        piece(lambda b2,q=q,n=nrms[k]: bmesh.ops.create_cone(b2,cap_ends=True,segments=10,radius1=0.0065,radius2=0.0035,depth=0.005,matrix=Matrix.Translation(q)@Vector((0,0,1)).rotation_difference(n).to_matrix().to_4x4()),BTN,None,f"{name}_btn{k}",wfn or near_w)
def on_radial(t,z,lift,cen=Vector((0,0.005,0))):   # 体の軸から見た一番外の面(裾など)
    d=Vector((math.sin(t),-math.cos(t),0)); o=Vector((cen.x,cen.y,z))
    h,_,_,_=bvh.ray_cast(o+d*0.3,-d,0.3); h=h or o+d*0.16; return h+d*lift,d   # 0.3より外(手など)は拾わない
# 肩のタブ(肩当ての上を首元から肩先へ)
for sx in (1,-1):
    P=[];N=[]
    for x in np.linspace(0.13,0.215,7):
        h,_,_,_=bvh.ray_cast(Vector((sx*x,0.0,NZ+0.1)),Vector((0,0,-1)),0.3)
        h=h or Vector((sx*x,0.0,NZ-0.05)); P.append(h+Vector((0,0,0.020))); N.append(Vector((0,0,1)))
    strap(P,N,0.028,f"shtab{sx}",lambda co,sx=sx: (("shoulder."+("L" if sx>0 else "R"),1.0),),btn=(0,))
# 襟の喉元を留めるストラップ(前の開きをまたぐ)
zq=nk.z-0.006; rq=R+0.030
P=[clear_head(Vector((0,nk.y,zq))+Vector((math.cos(t),math.sin(t)*0.95,0))*rq,0.018) for t in np.linspace(-math.pi/2-0.55,-math.pi/2+0.40,9)]
N=[Vector((p.x,p.y-nk.y,0)).normalized() for p in P]
strap(P,N,0.022,"throat",lambda co:(("chest",0.8),("neck",0.2)),btn=(0,len(P)-1))
# 裾の前身頃: 割れ目の縁から横へ掛けたストラップ(左右2段ずつ)
for z in (HZ-0.30,):
    s_=(ZJ-z)/(ZJ-ZB); g=gap(s_)
    for side,t0 in ((1,Tc+g+0.05),(-1,Tc+2*math.pi-g-0.05)):
        P=[];N=[]
        for t in np.linspace(t0,t0+side*0.38,9):
            p,d=on_radial(t,z,0.004); P.append(p); N.append(d)
        strap(P,N,0.03,f"sktab{side}{int(z*100)}",btn=(0,))
# 腰回りの共布の帯
NBt=72; ZW=ZJ+0.012
def bz(t): return ZW-0.018*math.sin(t)   # t=+π/2(左)側が下がる
# 左右の脇からそれぞれ別の共布の帯が出て、前で斜めに重なって結い留める(一周するベルトではない)
cen_=Vector((0,0.005,0))
def band_strap(a0,a1,z0,z1,lift,w,name):
    P=[];N=[]
    for t_ in np.linspace(0,1,30):
        a=a0+(a1-a0)*t_; z=z0+(z1-z0)*t_-0.012*math.sin(math.pi*t_)   # 少したるませる
        p,d=on_radial(a,z,lift); P.append(p); N.append(d)
    RQ=[(Vector((p.x,p.y,0))-cen_).length for p in P]   # 前の割れ目で落ち込まないよう、くぼみを埋める
    for _ in range(30): RQ=[RQ[0]]+[max(RQ[i],(RQ[i-1]+RQ[i+1])/2) for i in range(1,len(RQ)-1)]+[RQ[-1]]
    P=[Vector((cen_.x,cen_.y,p.z))+n*r for p,n,r in zip(P,N,RQ)]
    strap(P,N,w,name,btn=(0,len(P)-1),t=0.004)
band_strap(Tc+1.75,Tc-0.55,ZW+0.010,ZW-0.050,0.006,0.040,"band_L")   # 左脇から前を横切って右下へ
band_strap(Tc-1.75,Tc+0.60,ZW-0.030,ZW-0.110,0.012,0.036,"band_R")   # 右脇から前を横切って左下へ(上に重なる)
# ダブルの黒ボタン(前の重なりの左右に2列、胸から腰まで)
for i,z in enumerate(np.linspace(NZ-0.07,ZJ+0.07,6)):
    for bx in (XO+0.032,XO-0.042):
        loc,n=front_hit(bx,z)
        if loc: piece(lambda b2,loc=loc: bmesh.ops.create_cone(b2,cap_ends=True,segments=10,radius1=0.0075,radius2=0.004,depth=0.006,matrix=Matrix.Translation(loc-Vector((0,0.004,0)))@Matrix.Rotation(math.pi/2,4,'X')),BTN,"chest" if z>1.2 else "spine",f"btn{i}{bx}")
# 左腕(義手): 装甲の継ぎ目の金属帯、銀のバックル付きの黒革ベルト、外側に並ぶリベット列
ARMV={i for p_ in me.polygons if me.materials[p_.material_index].name in("leather_black","prosthetic") for i in p_.vertices}
JM=mat("joint_metal",(0.03,0.03,0.035),0.9,0.3)
def section(c,d,lim=0.07):   # 断面の形: 角度ごとに一番外の頂点までの距離
    up=d.cross(Vector((0,1,0))).normalized(); side=d.cross(up)
    pts=[me.vertices[i].co-c for i in ARMV if abs((me.vertices[i].co-c).dot(d))<0.012]
    pts=[q-d*q.dot(d) for q in pts]; pts=[q for q in pts if q.length<lim]
    NS=28; RS=[]
    for k in range(NS):
        t=2*math.pi*k/NS; u=up*math.cos(t)+side*math.sin(t)
        near=[q.dot(u) for q in pts if q.length>1e-4 and q.normalized().dot(u)>0.93]
        RS.append(max(near) if near else None)
    ok=[r for r in RS if r]; avg=sum(ok)/max(1,len(ok)); RS=[r if r else avg for r in RS]
    for _ in range(2): RS=[(RS[k-1]+2*RS[k]+RS[(k+1)%NS])/4 for k in range(NS)]
    return up,side,RS
def band(c,d,bone,name,w,off,m):
    up,side,RS=section(c,d); NS=len(RS)
    U=lambda k: up*math.cos(2*math.pi*k/NS)+side*math.sin(2*math.pi*k/NS)
    def f(b2):
        rows_=[[b2.verts.new(c+d*h+U(k)*(RS[k]+off)) for k in range(NS)] for h in (-w/2,w/2)]
        for k in range(NS): b2.faces.new((rows_[0][k],rows_[0][(k+1)%NS],rows_[1][(k+1)%NS],rows_[1][k]))
        bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=0.002)
    piece(f,m,bone,name); return up,side,RS,U
def belt(c,d,bone,name):
    up,side,RS,U=band(c,d,bone,name,0.013,0.0025,STRAP)
    k=len(RS)//4; p=c+U(k)*(RS[k]+0.006); n=U(k)   # 外側にバックル
    rot=Vector((0,0,1)).rotation_difference(n).to_matrix().to_4x4()@Matrix.Rotation(math.atan2(d.dot(up.cross(n)),d.dot(n.cross(up.cross(n))))*0,4,'Z')
    M_=Matrix.Translation(p)@rot
    def buckle(b2):   # 角の丸い枠+中央の留め棒
        for sx_,sy_,dx_,dy_ in ((0.017,0.003,0,0.007),(0.017,0.003,0,-0.007),(0.003,0.017,0.007,0),(0.003,0.017,-0.007,0),(0.002,0.014,0,0)):
            bmesh.ops.create_cube(b2,size=1,matrix=M_@Matrix.Translation((dx_,dy_,0))@Matrix.Diagonal((sx_,sy_,0.003,1)))
    piece(buckle,SILVER,bone,name+"_buckle")
fa=B("forearm.L"); ha=B("hand.L"); dF=(ha-fa).normalized(); lenF=(ha-fa).length
for k,t in enumerate((0.14,0.40,0.66,0.90)): band(fa+dF*lenF*t,dF,"forearm.L",f"fseam{k}",0.005,0.0015,JM)
for k,t in enumerate((0.27,0.53,0.78)): belt(fa+dF*lenF*t,dF,"forearm.L",f"fbelt{k}")
# 外側のリベット列(腕の上面に沿って並ぶ)
for c0,d,L,t0,t1,bone in ((fa,dF,lenF,0.06,0.95,"forearm.L"),):
    for k,t in enumerate(np.linspace(t0,t1,int((t1-t0)*L/0.022)+1)):
        c=c0+d*L*t; up,side,RS=section(c,d)
        for kk in (0,2):   # 真上と少し前
            u=up*math.cos(2*math.pi*kk/28)+side*math.sin(2*math.pi*kk/28); p=c+u*(RS[kk]+0.0015)
            piece(lambda b2,p=p: bmesh.ops.create_uvsphere(b2,u_segments=8,v_segments=6,radius=0.0026,matrix=Matrix.Translation(p)),SILVER,bone,f"rv{bone}{k}_{kk}")
# 袖口を縛る共布のストラップ(右手首・左の肘上の袖口)
ARMV={i for p_ in me.polygons if me.materials[p_.material_index].name in("coat_vermilion","coat_trim_red") and abs(p_.center.x)>0.2 for i in p_.vertices}
for c_,d_,bn,nm in ((B("hand.R")-dR*0.075,dR,"forearm.R","cuffR"),(kz-dL*0.045,dL,"upper_arm.L","cuffL")):
    up,side,RS,U=band(c_,d_,bn,nm,0.026,0.004,COAT)
    q=c_+U(0)*(RS[0]+0.009)
    piece(lambda b2,q=q,n=U(0): bmesh.ops.create_cone(b2,cap_ends=True,segments=10,radius1=0.0065,radius2=0.0035,depth=0.005,matrix=Matrix.Translation(q)@Vector((0,0,1)).rotation_difference(n).to_matrix().to_4x4()),BTN,bn,nm+"_btn")
# 左ひじ: 上腕の装甲から前腕へすぼまる金属ジョイント
el=B("forearm.L")
proR=[v.co for v in me.vertices if abs((v.co-el).dot(dL)-0.03)<0.01 and ((v.co-el)-dL*(v.co-el).dot(dL)).length<0.06]
rj=max(((p-el)-dL*(p-el).dot(dL)).length for p in proR) if proR else 0.035
slv=[v.co for v in me.vertices if abs((v.co-el).dot(dL))<0.008 and ((v.co-el)-dL*(v.co-el).dot(dL)).length<0.09]
rs=max(((p-el)-dL*(p-el).dot(dL)).length for p in slv) if slv else rj+0.012
rotL=Vector((0,0,1)).rotation_difference(dL).to_matrix().to_4x4()
JM=mat("joint_metal",(0.03,0.03,0.035),0.9,0.3)
def joint(b2):
    bmesh.ops.create_cone(b2,cap_ends=False,segments=32,radius1=rs-0.004,radius2=rj+0.002,depth=0.05,matrix=Matrix.Translation(el+dL*0.012)@rotL)
    bmesh.ops.create_cone(b2,cap_ends=False,segments=32,radius1=rj+0.005,radius2=rj+0.005,depth=0.008,matrix=Matrix.Translation(el+dL*0.036)@rotL)
    bmesh.ops.solidify(b2,geom=b2.faces[:],thickness=0.002)
piece(joint,JM,"forearm.L","elbow_joint")
# 丸いオレンジのサングラス(頭に追従)
LENS=bpy.data.materials.new("lens_orange"); LENS.use_nodes=True; lp=LENS.node_tree.nodes["Principled BSDF"]
lp.inputs["Base Color"].default_value=(1.0,0.55,0.06,1); lp.inputs["Alpha"].default_value=0.55; lp.inputs["Roughness"].default_value=0.1
LENS.blend_method="BLEND"; LENS.shadow_method="NONE"; LENS.show_transparent_back=False
FRAME=mat("glasses_frame",(0.22,0.22,0.24),1.0,0.3)   # ガンメタル
head=bpy.data.objects["head"]; hme=head.data; ei=[i for i,m in enumerate(hme.materials) if m.name=="eye"][0]
ev={v for p in hme.polygons if p.material_index==ei for v in p.vertices}
EY=[]
for sx in (1,-1):
    Q=[hme.vertices[i].co for i in ev if hme.vertices[i].co.x*sx>0]; c=sum(Q,Vector())/len(Q); EY.append(c)
EZ=(EY[0].z+EY[1].z)/2; EX=(abs(EY[0].x)+abs(EY[1].x))/2
hco=[v.co for v in hme.vertices if abs(v.co.z-EZ)<0.012]
FRONT=min(p.y for p in hco if abs(p.x)<0.02); SIDE=max(abs(p.x) for p in hco)
LR=0.022; LY=min(p.y for p in hco if abs(abs(p.x)-EX)<0.01)-0.012
def glasses(b2):   # ヴァッシュ風: 丸レンズ・上半分の太いリム・波(W)形に折れたつる・黒い先セル
    def rod(P,rr=0.0012,mi=0,closed=False):
        prev=None; first=None
        for i,p in enumerate(P):
            tg=(P[(i+1)%len(P)]-P[i-1]).normalized() if closed else (P[min(i+1,len(P)-1)]-P[max(i-1,0)]).normalized()
            a=tg.orthogonal().normalized(); b=tg.cross(a)
            rg=[b2.verts.new(p+(a*math.cos(k*math.pi/3)+b*math.sin(k*math.pi/3))*rr) for k in range(6)]
            if prev:
                for k in range(6): f=b2.faces.new((prev[k],prev[(k+1)%6],rg[(k+1)%6],rg[k])); f.material_index=mi
            else: first=rg
            prev=rg
        if closed:
            for k in range(6): f=b2.faces.new((prev[k],prev[(k+1)%6],first[(k+1)%6],first[k])); f.material_index=mi
    for sx in (1,-1):
        c=Vector((sx*EX,LY,EZ-0.004)); rot=Matrix.Rotation(math.pi/2,4,'X')
        r=bmesh.ops.create_circle(b2,cap_ends=True,segments=32,radius=LR,matrix=Matrix.Translation(c)@rot)
        for f in b2.faces:
            if all(v in r["verts"] for v in f.verts): f.material_index=1
        ring=lambda t,rr=LR+0.0008: c+Vector((math.cos(t)*rr,0,math.sin(t)*rr))
        rod([ring(2*math.pi*k/40) for k in range(40)],0.0007,closed=True)          # 細い全周リム
        rod([ring(math.pi*k/24,LR+0.0012) for k in range(25)],0.0016)             # 上半分の太いリム
        # 鼻あて
        bmesh.ops.create_uvsphere(b2,u_segments=8,v_segments=6,radius=0.0028,matrix=Matrix.Translation(c+Vector((-sx*(LR*0.8),0.006,-LR*0.55)))@Matrix.Diagonal((0.6,1,1.3,1)))
        # つる: レンズの外側上から、縦に波打つW字を経て耳へ。耳の後ろは黒い先セル
        # 智(ヒンジ): レンズ外側のやや上のリムから水平に短く出る金具
        h0=ring(math.radians(8) if sx>0 else math.pi-math.radians(8),LR+0.0012)
        h1=h0+Vector((sx*0.004,0.001,0))
        rod([h0,h1],0.0016)
        bmesh.ops.create_cube(b2,size=1,matrix=Matrix.Translation(h1+Vector((sx*0.0015,0.002,0)))@Matrix.Diagonal((0.004,0.005,0.004,1)))
        # つるの波: 始点と終点が同じ高さで、下へ2回・上へ1回折れるW字(4本の直線)
        e=Vector((sx*(SIDE+0.004),h1.y+0.032,h1.z)); A=0.016
        W=[h1]
        for k,dz in ((1,-A),(2,0.0),(3,-A),(4,0.0)):
            W.append(h1.lerp(e,k/4)+Vector((0,0,dz)))
        rod(W,0.0011)
        back=[W[-1],Vector((sx*(SIDE+0.007),0.0,EZ+0.005))]; rod(back,0.0011)
        rod([back[-1],Vector((sx*(SIDE+0.006),0.022,EZ-0.004)),Vector((sx*(SIDE+0.002),0.036,EZ-0.016))],0.0019,mi=2)
    rod([Vector((-(EX-LR-0.001)+2*(EX-LR-0.001)*t,LY-0.001,EZ+0.001+0.005*math.sin(math.pi*t))) for t in np.linspace(0,1,10)],0.0013)
g_=piece(glasses,[FRAME,LENS,mat("glasses_tip",(0.015,0.015,0.017),0,0.4)],"head 1","glasses")
print("GLASSES EX",round(EX,3),"EZ",round(EZ,3),"LY",round(LY,3),"SIDE",round(SIDE,3))
bpy.ops.object.select_all(action="DESELECT")
for o in parts: o.select_set(True)
wear.select_set(True); bpy.context.view_layer.objects.active=wear; bpy.ops.object.join()
# ---- 4. 使用感のテクスチャ(陰影・汚れ・擦れ・破れ) ----
# 周期的なノイズ(FFTで作るので横方向に継ぎ目なく繰り返せる)。縦(v)は高さに対応させ、裾ほど汚れる
rng=np.random.default_rng(7); TS=1024
def noise(lu,lv=None):   # lu/lv: 横/縦の模様の大きさ(ピクセル)
    lv=lv or lu
    fy=np.fft.fftfreq(TS)[:,None]; fx=np.fft.fftfreq(TS)[None,:]
    F=np.exp(-((fx*lu)**2+(fy*lv)**2)*4)
    n=np.real(np.fft.ifft2(np.fft.fft2(rng.standard_normal((TS,TS)))*F)); n-=n.mean(); return n/(n.std()+1e-9)
low=noise(260); folds=noise(45,500); mid=noise(90); fine=noise(3); tears=noise(10,50); spots=noise(25,120)
yy,xx=np.mgrid[0:TS,0:TS]; v=1-yy/TS   # v=0が足元、1が頭上
twill=np.sign(np.sin((xx*1.0+yy*0.2)*2*np.pi/5))*0.5   # 綾織りの斜めの畝(はっきりした段)
rib=np.sin(yy*2*np.pi/3)*0.5
_a=xx/TS*2*np.pi/3; _z=v*1.8; _s=np.clip((HZ+0.10-_z)/(HZ+0.10-0.27),0,1)
foldsh=np.cos(15*_a)*np.minimum(1,_s*1.4)**1.2   # 裾の折り山の陰影
def wear_tex(name,col,grime=(0.23,0.17,0.12),dmg=1.0,dust=0.0):
    c=np.array(col,np.float32)[None,None,:]*np.ones((TS,TS,1),np.float32)
    shade=1+0.05*low+0.05*folds+0.02*fine+0.05*twill+0.03*rib   # まだらの陰影・縦の折り皺・太い綾織り
    shade*=1+0.16*foldsh   # ドレープの折り山は明るく谷は暗い(形状の折り目と同じ位置)
    c*=shade[...,None]
    g=np.clip((0.30-v)/0.30,0,1)**1.4*(0.65+0.35*np.tanh(mid))   # 裾ほど砂埃と汚れ
    c=c*(1-0.55*g[...,None])+np.array(grime)[None,None,:]*0.55*g[...,None]
    worn=np.clip((mid-1.2)*0.8,0,1)*0.30   # 擦れて色が抜けたところ
    c=c*(1-worn[...,None])+(c.mean(-1,keepdims=True)*1.25)*worn[...,None]
    st=np.clip((spots-2.0)*1.2,0,1)*0.35   # しみ
    c*=(1-st[...,None])
    if dmg:
        th=2.9-0.8*np.clip((0.35-v)/0.35,0,1)   # 裂け目・焦げ(裾ほど多い)
        tr=np.clip((tears-th)*4,0,1)*dmg
        edge=np.clip((tears-th+0.25)*4,0,1)*(1-tr)*0.35*dmg
        c=c*(1-edge[...,None])+np.array(col)[None,None,:]*1.3*edge[...,None]
        c=c*(1-tr[...,None])+np.array((0.05,0.02,0.02))[None,None,:]*tr[...,None]
        for _ in range(int(14*dmg)):   # 弾痕(焦げ縁の小さな穴)
            cx,cy,r=rng.integers(0,TS),rng.integers(int(TS*0.25),TS),rng.uniform(3,7)
            d=np.hypot(((xx-cx+TS/2)%TS)-TS/2,yy-cy)
            c[d<r]=(0.03,0.015,0.015); ring=(d>=r)&(d<r*2.4); c[ring]*=0.55
    if dust:
        dd=np.clip((0.22-v)/0.22,0,1)*dust*(0.6+0.4*np.tanh(low))
        c=c*(1-dd[...,None])+np.array((0.42,0.36,0.28))[None,None,:]*dd[...,None]
    for zz in (0.27+0.018,0.27+0.028):   # 裾の2本ステッチ
        row=int((1-zz/1.8)*TS); c[row,::2]*=0.55; c[row,1::4]*=1.35
    img=bpy.data.images.new(name,TS,TS); px=np.ones((TS,TS,4),np.float32); px[...,:3]=np.clip(c,0,1)
    img.pixels[:]=px[::-1].ravel(); img.pack(); return img
def use_tex(m,img):
    nt=m.node_tree; t=nt.nodes.new("ShaderNodeTexImage"); t.image=img
    nt.links.new(t.outputs[0],nt.nodes["Principled BSDF"].inputs["Base Color"])
use_tex(COAT,wear_tex("coat_tex",(0.66,0.20,0.11)))   # 少し落ち着いた厚手の朱赤
use_tex(LINING,wear_tex("lining_tex",(0.40,0.07,0.05),dmg=0.5))
use_tex(TRIM,wear_tex("trim_tex",(0.55,0.12,0.07),dmg=0.6))
PNT=bpy.data.materials["pants_outer"]; use_tex(PNT,wear_tex("pants_tex",(0.19,0.20,0.24),grime=(0.30,0.26,0.20),dmg=0.3,dust=0.7))
# UV: 胴・裾・襟は体の周りの角度×高さ、腕は腕の周りの角度×腕に沿った距離
me=wear.data; uvd=me.uv_layers.active.data
TEXM={i for i,m in enumerate(me.materials) if m and m.name in("coat_vermilion","coat_lining_red","coat_trim_red","pants_outer")}
for p_ in me.polygons:
    if p_.material_index not in TEXM: continue
    cc=p_.center; is_arm=abs(cc.x)>0.24 and cc.z>1.0
    L_=list(p_.loop_indices); P_=[me.vertices[me.loops[li].vertex_index].co for li in L_]
    if is_arm:
        A_=[math.atan2(co.z-1.33,co.y-0.01) for co in P_]; per=2*math.pi
    else:
        A_=[math.atan2(co.x,-(co.y-0.005)) for co in P_]; per=2*math.pi
    if max(A_)-min(A_)>math.pi: A_=[a_+per if a_<0 else a_ for a_ in A_]   # 継ぎ目をまたぐ面は片側にそろえる
    for li,co,a_ in zip(L_,P_,A_):
        uvd[li].uv=(abs(co.x)*2.2,0.68+a_/per*0.06) if is_arm else (a_/per*3,co.z/1.8)
bpy.ops.wm.save_as_mainfile(filepath=S+"/nemo_s2c_red.blend")
print("DONEC")
