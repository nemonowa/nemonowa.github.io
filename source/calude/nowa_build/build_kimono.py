# Nowa着物版 工程2: 着物の衣装を作る。
#  - 半透明水色の袖なし着物トップ(くらげ柄)+内側の裏地、立ち襟(紺フリル)・チョーカー、前合わせの紺フリル、肩口の白フリル
#  - 袖(別パーツ): 上腕に紺フリル帯+橙のビーズ5個、広い半透明の振り袖(くらげ柄)、手首は紺フリルの袖口
#  - 帯(赤)+前右の水色の大きな蝶結び(赤い玉)+垂れ
#  - 短い着物スカート(星空の紫青、前が少し開く、裾に白フリル+橙ビーズ)
#  - 素足(元のモデルは足の甲が無いので作る)+黒い鼻緒の下駄風サンダル+足首の青フリルとビーズ
#  - 揺れ物ボーン: 袖(左右3列x2節)・帯の垂れ(2本x3節)・スカート(8列x3節)。剛体は build_physics.py で付ける。
# 元の服のパーツは build_strip.py で撤去済みの nowa_s1.blend に重ねる。
# 使い方: blender -b nowa_s1.blend -P build_kimono.py -- <作業ディレクトリ>
import bpy, bmesh, sys, math, os, random
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
S=sys.argv[sys.argv.index("--")+1]
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kimono_tex as KT
bpy.ops.preferences.addon_enable(module="mmd_tools")
bpy.context.preferences.filepaths.save_version=0
from mmd_tools.core.material import FnMaterial
arm=bpy.data.objects["Nowa_Mel_v1_2_arm"]; body=bpy.data.objects["Nowa_Mel_v1_2_mesh"]; root=bpy.data.objects["Nowa_Mel_v1_2"]
B=lambda n: Vector(arm.data.bones[n].head_local)
Tl=lambda n: Vector(arm.data.bones[n].tail_local)
TEX=S+"/tex_out"; os.makedirs(TEX,exist_ok=True)
Z=Vector((0,0,1))
def sstep(x,a,b):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3-2*t)
def lerp(a,b,t): return a+(b-a)*t
def mx(p): return Vector((-p.x,p.y,p.z))     # 左→右のミラー

# ================= 1. マテリアル(mmd_tools形式。生成した画像はファイル化してPMXへテクスチャを同梱) =================
def img_from(name,arr):
    im=bpy.data.images.new(name,arr.shape[1],arr.shape[0]); im.pixels[:]=arr.ravel()
    fn=f"{TEX}/{name}.png"; im.filepath_raw=fn; im.file_format="PNG"; im.save(); im.filepath=fn; im.source="FILE"; im.reload()
    return im
def mk(name,name_j,tex=None,col=(1,1,1),alpha=1.0,shin=5.0,spec=0.0,edge=False,blend=None):
    im=img_from("k_"+name,tex if tex is not None else KT.solid_tex(col))
    m=bpy.data.materials.new(name); m.use_nodes=True
    tn=m.node_tree.nodes.new("ShaderNodeTexImage"); tn.image=im
    m.node_tree.links.new(tn.outputs[0],m.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    FnMaterial.convert_to_mmd_material(m,bpy.context)
    mm=m.mmd_material; mm.name_j=name_j; mm.name_e=name; mm.diffuse_color=(1,1,1); mm.ambient_color=(0.55,0.55,0.55)
    mm.specular_color=(spec,spec,spec); mm.shininess=shin; mm.alpha=alpha; mm.is_double_sided=True; mm.enabled_toon_edge=edge
    m.blend_method=blend or ("BLEND" if alpha<1 else "OPAQUE"); m.show_transparent_back=False
    return m
M={}
M["bodice"]=mk("kimono_bodice","着物トップ",tex=KT.bodice_tex(),alpha=0.80,blend="BLEND")   # 胴用(くらげを胸の位置に配置)
M["jelly"]=mk("kimono_jelly","着物くらげ",tex=KT.jelly_tex(),alpha=0.76,blend="BLEND")   # 半透明の青い着物地(重なる所は濃くなる)
M["lining"]=mk("kimono_lining","着物の縁",tex=KT.lining_tex())                      # 前合わせの重なりの厚み(縁の側面)
M["shade"]=mk("kimono_shade","重なりの影",col=(0.0,0.02,0.22),alpha=0.34,blend="BLEND")   # 上前の下に落ちる薄い影
M["navy"]=mk("kimono_navy","紺フリル",tex=KT.navy_tex(),shin=8)
M["white"]=mk("kimono_white","白フリル",col=(0.97,0.97,1.0))
M["obi"]=mk("kimono_obi","帯",tex=KT.obi_tex(),shin=14,spec=0.12)
M["bow"]=mk("kimono_bow","蝶結び",tex=KT.bow_tex(),alpha=0.90,blend="BLEND",shin=10)
M["bowdark"]=mk("kimono_bowdark","蝶結び内側",tex=KT.bow_tex(dark=True),alpha=0.92,blend="BLEND",shin=10)
M["bead"]=mk("kimono_bead","橙ビーズ",col=(0.98,0.62,0.10),shin=40,spec=0.5)
M["jewel"]=mk("kimono_jewel","赤玉",col=(0.85,0.05,0.12),shin=60,spec=0.6)
M["skirt"]=mk("kimono_skirt","星空スカート",tex=KT.skirt_tex(),shin=6)
M["lilac"]=mk("kimono_lilac","ラベンダーフリル",col=(0.78,0.66,0.96))
M["sandal"]=mk("kimono_sandal","下駄",col=(0.03,0.03,0.035),shin=20,spec=0.2)
M["bfrill"]=mk("kimono_bfrill","青フリル",tex=KT.navy_tex(col=(0.16,0.34,0.90),edge=(0.75,0.92,1.0),seed=11),shin=8)
# 素足: 元の肌マテリアルを複製(body.pngの肌色の1点を指すUVで塗る)
skin=bpy.data.materials["Skin"].copy(); skin.name="Skin_fill"; skin.mmd_material.name_j="肌補完"; skin.mmd_material.name_e="skin fill (feet/torso)"
M["skin"]=skin
skinf=bpy.data.materials["Face"].copy(); skinf.name="Skin_neck_fill"; skinf.mmd_material.name_j="首補完"; skinf.mmd_material.name_e="neck fill"
M["skinface"]=skinf
for _m in (skin,skinf): _m.mmd_material.is_double_sided=True; _m.use_backface_culling=False   # 穴埋め面は裏からも見える/向きに依存しない
MATORDER=["jelly","lining","navy","white","obi","bow","bead","jewel","skirt","lilac","sandal","bfrill","skin","shade","bowdark","bodice","skinface"]
MI={k:i for i,k in enumerate(MATORDER)}

# ================= 2. 体の参照(レイキャスト用BVH・ウェイトコピー用KDTree) =================
bmref=bmesh.new(); bmref.from_mesh(body.data)
mnames=[m.name for m in body.data.materials]
keep={mnames.index(n) for n in ("Skin","Swimsuit","Face")}
bmesh.ops.delete(bmref,geom=[f for f in bmref.faces if f.material_index not in keep],context="FACES")
bmesh.ops.delete(bmref,geom=[v for v in bmref.verts if not v.link_faces],context="VERTS")
bmref.verts.ensure_lookup_table()
bvh=BVHTree.FromBMesh(bmref)
gname={g.index:g.name for g in body.vertex_groups}; dl0=bmref.verts.layers.deform.active
kd=KDTree(len(bmref.verts))
for v in bmref.verts: kd.insert(v.co,v.index)
kd.balance()
VW=[{gname[k]:w for k,w in v[dl0].items() if not gname[k].startswith("mmd")} for v in bmref.verts]
# 肌テクスチャの肌色を拾うUV: すねの上(z=0.32付近)の面のUV。左右で別の場所を指していることがあるので左右それぞれ拾う
uvl=body.data.uv_layers["UVMap"].data; SUV={}; best={1:1e9,-1:1e9}
for p in body.data.polygons:
    if p.material_index==mnames.index("Skin"):
        c=p.center; sg=1 if c.x>0 else -1
        if 0.03<abs(c.x)<0.12 and abs(c.z-0.33)<best[sg]:
            best[sg]=abs(c.z-0.33); SUV[sg]=Vector(sum((uvl[l].uv for l in p.loop_indices),Vector((0,0)))/len(p.loop_indices))
print("skin uv",dict(SUV))
def _poly_uv(p): return Vector(sum((uvl[l].uv for l in p.loop_indices),Vector((0,0)))/len(p.loop_indices))
def _nearest_uv(matname,target):
    best_=1e9; uv_=Vector((0.5,0.5))
    for p in body.data.polygons:
        if p.material_index==mnames.index(matname):
            d_=(p.center-target).length
            if d_<best_: best_=d_; uv_=_poly_uv(p)
    return uv_
SUV_T=_nearest_uv("Skin",Vector((0,-0.09,1.2)))      # 胸の肌の色(穴埋め用)
SUV_N=_nearest_uv("Face",Vector((0,-0.03,1.30)))     # 首の肌の色(顔マテリアルの首の下端)
print("fill uv torso",tuple(SUV_T),"neck",tuple(SUV_N))
# 元のすねの下端は(ブーツで隠れていたため)UVが影色の部分を指していて、素足にすると紫がかった帯になる → 上の肌色の1点へ貼り直す
for p in body.data.polygons:
    if p.material_index==mnames.index("Skin") and p.center.z<0.33 and 0.03<abs(p.center.x)<0.16:
        for l in p.loop_indices: uvl[l].uv=SUV[1 if p.center.x>0 else -1]

# ================= 3. メッシュ蓄積クラス =================
class Acc:
    def __init__(s):
        s.bm=bmesh.new(); s.uv=s.bm.loops.layers.uv.new("UVMap"); s.dl=s.bm.verts.layers.deform.verify(); s.gi={}
    def gid(s,n):
        if n not in s.gi: s.gi[n]=len(s.gi)
        return s.gi[n]
    def vert(s,co,w):
        v=s.bm.verts.new(co)
        for n,x in w.items():
            if x>1e-5: v[s.dl][s.gid(n)]=x
        return v
    def face(s,vs,mat,uvs,smooth=True):
        try: f=s.bm.faces.new(vs)
        except ValueError: return None
        f.material_index=MI[mat]; f.smooth=smooth
        for l,uv in zip(f.loops,uvs): l[s.uv].uv=uv
        return f
    def grid(s,P,wf,mat,uvf,closed=False,flip=False,ref=None,smooth=True):
        """P[r][c]の格子。wf(co,r,c)->ウェイト辞書。uvf(r,c)->(u,v)。closedなら列方向に輪になる。refは外向き判定用の基準点関数。"""
        R=len(P); C=len(P[0])
        V=[[s.vert(P[r][c],wf(P[r][c],r,c)) for c in range(C)] for r in range(R)]
        nc=C if closed else C-1
        for r in range(R-1):
            for c in range(nc):
                c2=(c+1)%C
                vs=[V[r][c],V[r][c2],V[r+1][c2],V[r+1][c]]; uvs=[uvf(r,c),uvf(r,c+1),uvf(r+1,c+1),uvf(r+1,c)]
                if flip: vs=vs[::-1]; uvs=uvs[::-1]
                f=s.face(vs,mat,uvs,smooth)
                if f is not None and ref is not None:
                    ctr=f.calc_center_median()
                    if f.normal.dot(ctr-ref(ctr))<0: f.normal_flip()
        return V
    def sphere(s,pos,rad,mat,w,sc=(1,1,1),seg=10,rings=7):
        bmq=bmesh.new(); bmesh.ops.create_uvsphere(bmq,u_segments=seg,v_segments=rings,radius=1.0)
        mt=Matrix.Translation(pos)@Matrix.Diagonal((rad*sc[0],rad*sc[1],rad*sc[2],1))
        vm={}
        for v in bmq.verts: vm[v]=s.vert(mt@v.co,w)
        for f in bmq.faces:
            s.face([vm[v] for v in f.verts],mat,[(0.5,0.5)]*len(f.verts))
        bmq.free()
acc=Acc()

def norm_w(w):
    t=sum(w.values()); return {k:v/t for k,v in w.items()} if t>1e-9 else {"upper_body2":1.0}
def add_w(d,k,x):
    if x>1e-6: d[k]=d.get(k,0)+x

# ---- フリル(ひだ布): 経路に沿って幅方向へ波打つ帯を作る ----
def ruffle(acc,pts,nrm,dirs,width,amp,lam,mat,wf,closed=False,rows=3,uv_s=0.1,flip=False,phase=0.0,ref=None,soft=False):
    """pts:経路の点列 nrm:布の外向き法線 dirs:帯が伸びる向き。lam:波の長さ。ひだは法線方向の正弦波で表す。"""
    n0=len(pts); L=[0.0]
    for i in range(1,n0): L.append(L[-1]+(pts[i]-pts[i-1]).length)
    tot=L[-1]+((pts[0]-pts[-1]).length if closed else 0)
    nw=max(2,round(tot/lam)); lam2=tot/nw
    per=10 if soft else 8                        # 1波あたりの分割
    N=nw*per+(0 if closed else 1)
    def at(t):                                   # 経路上の位置(0..tot)を補間
        if closed: t=t%tot
        t=min(t,L[-1]) if not closed else t
        for i in range(1,n0+1):
            if i==n0:
                if not closed: return pts[-1],nrm[-1],dirs[-1]
                a,b=n0-1,0; l0=L[-1]; ln=(pts[0]-pts[-1]).length
            else:
                a,b=i-1,i; l0=L[a]; ln=L[b]-L[a]
            if t<=l0+ln or i==n0:
                f=(t-l0)/max(ln,1e-9); return pts[a].lerp(pts[b],f),nrm[a].lerp(nrm[b],f).normalized(),dirs[a].lerp(dirs[b],f).normalized()
    P=[]
    for i in range(N):
        t=tot*i/(nw*per); p,n,d=at(t); ph=2*math.pi*(t/lam2)+phase; row=[]
        for j in range(rows):
            f=j/(rows-1)
            if soft:   # やわらかい丸いひだ: 波は2次の高調波を混ぜた丸い山谷、自由端は丸いスカラップ(ギザギザの歯にならない)
                td=n.cross(d)
                row.append(p+d*width*f*(1-0.10*(0.5-0.5*math.cos(ph+0.5)))+n*amp*(f**1.3)*(math.sin(ph)+0.28*math.sin(2*ph+0.8))+td*amp*0.45*f*math.cos(ph))
            else:
                row.append(p+d*width*f*(0.86+0.14*math.cos(ph+1.0))+n*amp*f*math.sin(ph))
        P.append(row)
    # 格子はP[i][j]: i=経路方向,j=幅方向 → 転置して使う
    G=[[P[i][j] for i in range(N)] for j in range(rows)]
    uvf=lambda r,c:((c/(nw*per))*(tot/uv_s),r/(rows-1))
    return acc.grid(G,lambda co,r,c:wf(co,r,c),mat,uvf,closed=closed,flip=flip,ref=ref,smooth=True)

# ================= 4. 胴まわり(着物トップ・帯・スカート)の形状関数 =================
CY=-0.005                                         # 体の軸のy
def dirv(th): return Vector((math.sin(th),-math.cos(th),0))     # th=0が正面(-y)、+π/2が左(+x)
PROF=[(0.80,0.115,0.085,0.085),(0.90,0.105,0.078,0.075),(1.00,0.080,0.076,0.050),(1.08,0.082,0.085,0.045),
      (1.16,0.115,0.108,0.058),(1.22,0.125,0.070,0.055),(1.28,0.060,0.050,0.045)]   # z, 半幅, 前の奥行き, 後ろの奥行き
def prof(z):
    if z<=PROF[0][0]: return PROF[0][1:]
    for a,b in zip(PROF,PROF[1:]):
        if z<=b[0]:
            t=(z-a[0])/(b[0]-a[0]); return tuple(lerp(a[i],b[i],t) for i in (1,2,3))
    return PROF[-1][1:]
def r_ell(th,z):
    rx,rf,rb=prof(z); s,c=math.sin(th),math.cos(th); ry=rf if c>=0 else rb; n=2.6
    return (((abs(s)/rx)**n+(abs(c)/ry)**n)**(-1/n))
_rc={}
def r_body(th,z):
    k=(round(th,4),round(z,4))
    if k in _rc: return _rc[k]
    r=r_ell(th,z); d=dirv(th); o=Vector((0,CY,z))
    h,_,_,_=bvh.ray_cast(o+d*0.4,-d,0.4)
    if h is not None and abs(h.x)<0.135 and abs(h.z-z)<0.01: r=max(r,(h-o).dot(d))
    _rc[k]=r; return r
def neck_r(z):
    rs=[]
    for k in range(8):
        d=dirv(k*math.pi/4); o=Vector((0,-0.005,z)); h,_,_,_=bvh.ray_cast(o+d*0.2,-d,0.2)
        if h is not None: rs.append((h-o).dot(d))
    return (sum(rs)/len(rs)) if rs else 0.03
def top_z(th):
    a=abs(math.sin(th)); zc=1.268 if math.cos(th)>=0 else 1.250
    return zc-(zc-1.17)*sstep(a,0.32,0.92)
def body_w(co,hint=None):
    """胴まわりの服の頂点ウェイト: 高さで下半身→上半身→上半身2→首へ。胸まわりは近い肌の頂点のウェイト(胸ボーン含む)をコピー。"""
    z=co.z; w={}
    if z<0.93: w={"lower_body":1.0}
    elif z<1.0: t=(z-0.93)/0.07; w={"lower_body":1-t,"upper_body":t}
    elif z<1.06: w={"upper_body":1.0}
    elif z<1.11: t=(z-1.06)/0.05; w={"upper_body":1-t,"upper_body2":t}
    elif z<1.29: w={"upper_body2":1.0}
    else: t=min(1,(z-1.29)/0.03); w={"upper_body2":1-t,"neck":t}
    if 1.10<z<1.27 and co.y<-0.02 and abs(co.x)<0.12:
        _,i,d=kd.find(co)
        if d<0.03:
            src=VW[i]; tt=1-d/0.03; ww={}
            for k,x in w.items(): add_w(ww,k,x*(1-tt))
            for k,x in src.items(): add_w(ww,k,x*tt)
            w=ww
    return norm_w(w)
def stand(i): return i

def ruffle_soft2(acc,pts,nrm,dirs,width,amp,lam,mat,wf,**kw):
    """やわらかいフリルを位相をずらして2重にする(谷間が透けて歯のように見えないように)。"""
    ruffle(acc,pts,nrm,dirs,width,amp,lam,mat,wf,soft=True,**kw)
    k2=dict(kw); k2["phase"]=kw.get("phase",0.0)+math.pi
    ruffle(acc,[p-n*0.0016 for p,n in zip(pts,nrm)],nrm,dirs,width*0.84,amp*0.8,lam,mat,wf,soft=True,**k2)

# ---- 4-0. 素肌の穴埋め: 元のモデルは服で隠れていた所(胸〜腹〜脇の大きな穴、首の下の帯状の穴)に肌のジオメトリが無い。
# 体の軸から外へ向けて内側からレイを撃ち、穴(命中なし)を見つけ、周りの実在する肌の半径から滑らかに補間した面で塞ぐ(境界は1マス重ねて少し内側に入れる) ----
FZ0,FZ1,DZF,NTF=0.90,1.32,0.004,120
FZS=[FZ0+DZF*j for j in range(int(round((FZ1-FZ0)/DZF))+1)]
def inner_hit(th,z):
    d=dirv(th); o=Vector((0,CY,z)); h,_,_,_=bvh.ray_cast(o,d,0.30)
    if h is None: return None
    r=(h-o).dot(d)
    if z>=1.285: return r if r<0.06 else None            # 首(顔マテリアルの首の壁)
    re=r_ell(th,min(z,1.28))
    return r if 0.55*re<=r<=1.4*re else None
KN=[[inner_hit(2*math.pi*i/NTF,z) for z in FZS] for i in range(NTF)]
HOLE={(i,j) for i in range(NTF) for j in range(len(FZS)) if KN[i][j] is None}
R=[[KN[i][j] if KN[i][j] is not None else r_ell(2*math.pi*i/NTF,min(FZS[j],1.28)) for j in range(len(FZS))] for i in range(NTF)]
for _ in range(600):       # 穴の半径をまわりの値から緩和(ラプラシアン)で滑らかに
    R2=[row[:] for row in R]
    for (i,j) in HOLE:
        nb=[R[(i-1)%NTF][j],R[(i+1)%NTF][j]]
        if j>0: nb.append(R[i][j-1])
        if j<len(FZS)-1: nb.append(R[i][j+1])
        R2[i][j]=sum(nb)/len(nb)
    R=R2
HD=set(HOLE)
for (i,j) in HOLE:
    for di,dj in ((1,0),(-1,0),(0,1),(0,-1)): HD.add(((i+di)%NTF,j+dj))
print("hole nodes",len(HOLE),"patch nodes",len(HD))
def fill_vert(i,j,cache={}):
    if (i,j) in cache: return cache[(i,j)]
    th=2*math.pi*i/NTF; z=FZS[j]; r=R[i][j]-(0.0012 if KN[i][j] is not None else 0.0)
    co=Vector((0,CY,z))+dirv(th)*r
    _,idx,_d=kd.find(co); w=norm_w(dict(VW[idx]))
    v=acc.vert(co,w); cache[(i,j)]=v; return v
nfill=0
for i in range(NTF):
    for j in range(len(FZS)-1):
        cs=[(i,j),((i+1)%NTF,j),((i+1)%NTF,j+1),(i,j+1)]
        if not any(c in HD for c in cs): continue
        mat="skinface" if FZS[j]>=1.262 else "skin"
        uv=SUV_N if mat=="skinface" else SUV_T
        f=acc.face([fill_vert(*c) for c in cs][::-1],mat,[tuple(uv)]*4,smooth=True)
        if f is not None:
            f.normal_update(); ctr=f.calc_center_median()
            if f.normal.dot(ctr-Vector((0,CY,ctr.z)))<0: f.normal_flip()
            nfill+=1
print("skin fill faces",nfill)

# ---- 4a. 着物トップ。下は4-0で埋めた実在の素肌(透ける布の下に体の形がうっすら見える)、外は半透明の青い布 ----
def top_z(th):
    """上端の高さ。前は首の付け根でまるくすくった襟ぐり(中央が低く、首の両脇で高い)、そこから肩口の切り込みへ斜めに下がる。"""
    a=abs(math.sin(th)); front=math.cos(th)>=0
    zc=1.205 if front else 1.250; zp=1.265 if front else 1.266
    if a<0.55:   # まるいU字(端は急に立ち上がらないよう放物線と半円を混ぜる)
        t_=a/0.55; return zc+(zp-zc)*(0.5*(1-math.sqrt(max(0.0,1-t_*t_)))+0.5*t_*t_)
    return zp-(zp-1.17)*sstep(a,0.55,0.95)
NC=72; NR=14; ZB=0.95
TILE=0.36                                   # くらげ柄1タイルの実寸(m)
OFF_U=0.013; STEP=0.009; TH_S=2.2; XE0,XE1=0.036,0.010; ZE0,ZE1=1.25,1.052   # 上前(外側の身頃)の合わせ目: 襟ぐりの右端→帯の上、ほぼ垂直で少し中央へ寄る
def edge_x(z): return lerp(XE1,XE0,max(0.0,min(1.0,(z-ZE1)/(ZE0-ZE1))))
def edge_th(z):
    x=edge_x(z); th=0.0
    for _ in range(4): th=math.asin(max(-0.95,min(0.95,x/r_body(th,z))))
    return th
def th_norm(t): return (t+math.pi)%(2*math.pi)-math.pi
def surf_off(th,z):
    """その位置の布の表面の高さ(体からの距離)。上前が重なる所は一段高い。"""
    t=th_norm(th); te=edge_th(min(max(z,ZE1),ZE0))
    if te<=t<=TH_S: s_=(t-te)/(TH_S-te); return OFF_U+0.002+STEP*(1-sstep(s_,0.45,1.0))
    return OFF_U+0.0015
def shell(off,mat,zoff,uvf=None):
    P=[];ZG=[]
    for i in range(NC):
        th=2*math.pi*i/NC; col=[]; zc_=[]; tz=top_z(th)-zoff
        for j in range(NR+1):
            z=lerp(ZB,tz,j/NR); zc_.append(z); col.append(Vector((0,CY,z))+dirv(th)*(r_body(th,z)+off))
        P.append(col); ZG.append(zc_)
    G=[[P[i][j] for i in range(NC)] for j in range(NR+1)]
    uvf=uvf or (lambda r,c:(c/NC,(ZG[c%NC][r]-ZB)/0.32))      # u=角度/2π(前中央が0)、v=高さ0.32m
    return acc.grid(G,lambda co,r,c:body_w(co),mat,uvf,closed=True,ref=lambda p:Vector((0,CY,p.z)),smooth=True)
shell(OFF_U,"bodice",0.0)                                    # 下前(全周)
# ---- 4b. 上前: 別パーツの重ね層(一段高く、縁に厚みの側面と影、縁に紺のやわらかいフリル) ----
NS=44
def outer_pt(s_,v,dz=0.0):
    t0=edge_th(1.245); ztop=top_z(t0+(TH_S-t0)*s_)
    z=lerp(ZB,ztop,v); te=edge_th(min(max(z,ZE1),ZE0)); th=te+(TH_S-te)*s_
    off=OFF_U+0.002+STEP*(1-sstep(s_,0.45,1.0))+dz
    return Vector((0,CY,z))+dirv(th)*(r_body(th,z)+off),th,z
OP=[[outer_pt(c/NS,r/NR) for c in range(NS+1)] for r in range(NR+1)]
P=[[q[0] for q in row] for row in OP]
acc.grid(P,lambda co,r,c:body_w(co),"bodice",lambda r,c:(OP[r][c][1]/(2*math.pi),(OP[r][c][2]-ZB)/0.32),ref=lambda p:Vector((0,CY,p.z)),smooth=True)
# 二重に重なる範囲は深い青に見えるよう、2枚の布の間に薄い濃紺の半透明の層を挟む
P=[[outer_pt(c/NS,r/NR,-0.0045)[0] for c in range(NS+1)] for r in range(NR+1)]
acc.grid(P,lambda co,r,c:body_w(co),"shade",lambda r,c:(0.5,0.5),ref=lambda p:Vector((0,CY,p.z)),smooth=True)
# 縁の厚み(側面)と、下前に落ちる影
P=[];Q=[]
for r in range(NR+1):
    o,th,z=outer_pt(0,r/NR); P.append([o,Vector((0,CY,z))+dirv(th)*(r_body(th,z)+OFF_U)])
    Q.append([Vector((0,CY,z))+dirv(th-0.19*w)*(r_body(th-0.19*w,z)+OFF_U+0.0012) for w in (0,0.33,0.66,1.0)])
acc.grid(P,lambda co,r,c:body_w(co),"lining",lambda r,c:(r/NR,c),ref=lambda p:Vector((0,CY,p.z)),smooth=False)
acc.grid(Q,lambda co,r,c:body_w(co),"shade",lambda r,c:(r/NR,c/3),ref=lambda p:Vector((0,CY,p.z)),smooth=True)
vmin=(ZE1-ZB)/(top_z(edge_th(1.245))-ZB)
pts=[];nr=[];ds=[]
for k in range(41):
    v=1.0-(1.0-vmin)*k/40; o,th,z=outer_pt(0,v); n=dirv(th); tg=Vector((math.cos(th),math.sin(th),0))
    pts.append(o+n*0.002); nr.append(n); ds.append((-tg*0.92+n*0.22).normalized())
ruffle_soft2(acc,pts,nr,ds,0.019,0.0060,0.022,"navy",lambda co,r,c:body_w(co),rows=6,uv_s=0.08,ref=lambda c:Vector((0,CY,c.z)))

# ---- 4c. 襟ぐり(まるくすくった首の付け根): 紺のやわらかい寄せフリル+首の上の細い紺のチョーカー(立ち襟は無し) ----
def top_edge(th,off=None):
    z=top_z(th); return Vector((0,CY,z))+dirv(th)*(r_body(th,z)+(surf_off(th,z) if off is None else off)+0.002)
for front in (True,False):
    pts=[];nr=[];ds=[]
    for a_ in np.linspace(-0.56,0.56,34):
        th=math.asin(a_) if front else math.pi-math.asin(a_)
        th=th%(2*math.pi); p=top_edge(th); pts.append(p); n=dirv(th); nr.append(n); ds.append((Z*0.80+n*0.35).normalized())
    if not front: pts,nr,ds=pts[::-1],nr[::-1],ds[::-1]
    ruffle_soft2(acc,pts,nr,ds,0.017,0.0055,0.021,"navy",lambda co,r,c:body_w(co),rows=6,uv_s=0.08)
def ring(z0,z1,rfun,mat,wf,n=40,rows=3,uvs=0.12):
    P=[[Vector((0,CY+0.0,lerp(z0,z1,j/(rows-1))))+dirv(2*math.pi*i/n)*rfun(lerp(z0,z1,j/(rows-1)),i) for i in range(n)] for j in range(rows)]
    return acc.grid(P,wf,mat,lambda r,c:(c/n*2*math.pi*0.04/uvs,r/(rows-1)),closed=True,ref=lambda c:Vector((0,CY,c.z)))
ring(1.296,1.310,lambda z,i:neck_r(1.303)+0.004,"navy",lambda co,r,c:norm_w({"neck":1.0}),n=48,rows=2)
# ---- 4d. 肩口(切り口)の白い小フリル(やわらかい寄せ) ----
for sgn in (1,-1):
    for front in (True,False):
        pts=[];nr=[];ds=[]
        for a_ in np.linspace(0.56,0.95,22):
            th=(math.asin(a_) if front else math.pi-math.asin(a_))*sgn
            th=th%(2*math.pi); pts.append(top_edge(th)); n=dirv(th); nr.append(n); ds.append((Z*0.9+n*0.3).normalized())
        ruffle(acc,pts,nr,ds,0.016,0.0055,0.016,"white",lambda co,r,c:body_w(co),rows=5,uv_s=0.08,soft=True)

# ---- 4e. 帯(深い紅色の厚みのある帯。縁は丸く巻き、ゆるい縦のひだ+陰影のテクスチャ) ----
OB0,OB1=0.958,1.058; NO=96; NOB=14
def obi_r(th,z,f):
    return r_body(th,z)+0.030+0.014*(math.sin(math.pi*f)**0.55)+0.0013*math.sin(th*9+f*2.0)*math.sin(math.pi*f)
P=[]
for i in range(NO):
    th=2*math.pi*i/NO
    P.append([Vector((0,CY,lerp(OB0,OB1,j/NOB)))+dirv(th)*obi_r(th,lerp(OB0,OB1,j/NOB),j/NOB) for j in range(NOB+1)])
G=[[P[i][j] for i in range(NO)] for j in range(NOB+1)]
acc.grid(G,lambda co,r,c:body_w(co),"obi",lambda r,c:(c/NO*3,r/NOB),closed=True,ref=lambda c:Vector((0,CY,c.z)))

# ---- 4f. 蝶結び(前の右=画像の右=+x側)。ふっくらした2つの輪(根元から放射するしわ+中央の折り目)+内側の輪+結び目+赤い玉+垂れ(揺れ物) ----
THK=0.45
WBOW={"upper_body":0.6,"lower_body":0.4}; wbow=lambda co,r,c:dict(WBOW)
Rk=r_body(THK,1.008)+0.046
Nn=dirv(THK)
def bow_pt(th,z,pil): return Vector((0,CY,z))+dirv(th)*(Rk+pil)
def loop(sg,L,H,B,z0,droop,mat,groove):
    nu,nv=16,12; P=[]
    for a_ in range(nu+1):
        u=a_/nu; hh=H*math.sqrt(max(0.0,1-(2*u-1)**2))+H*0.10*(1-u); row=[]
        for b in range(nv+1):
            v=-1+2*b/nv; th=THK+sg*(L*u/Rk)
            pil=0.004+B*(math.sin(math.pi*u)**0.7)*max(0.0,1-v*v)**0.7
            pil+=0.0035*math.cos(5*math.pi*v)*(1-u)**1.2*max(0.0,1-abs(v))     # 根元から放射するしわ
            pil-=groove*math.exp(-(v/0.16)**2)*math.sin(math.pi*u)**0.8          # 輪の中央の折り目
            row.append(bow_pt(th,1.008+z0-droop*u*u+v*hh,pil))
        P.append(row)
    acc.grid(P,wbow,mat,lambda r,c:(r/nu,c/nv),ref=lambda cc:Vector((0,CY,cc.z)),smooth=True)
for sg in (1,-1):
    loop(sg,0.080,0.034,0.016,-0.010,0.034,"bowdark",0.005)    # 下の輪(内側の濃い面。斜め下へ)
    loop(sg,0.098,0.050,0.024,0.014,-0.020,"bow",0.011)        # 上のふくらんだ輪(斜め上へ。中央に折り目)
K=Vector((0,CY,1.008))+dirv(THK)*(Rk+0.016)
acc.sphere(K,0.0155,"bow",WBOW,sc=(0.9,0.8,1.35),seg=12,rings=8)
acc.sphere(Vector((0,CY,1.008))+dirv(THK)*(Rk+0.030),0.0125,"jewel",WBOW,seg=14,rings=9)
# 垂れ(2本): 結び目から体(スカート)の表面に沿って垂れる。ボーンは3節
def r_skirt_top(th): return r_ell(th,0.97)+0.034
HEMZ=0.70; ZS0=0.97
def gap(f): return 0.40*sstep(f,0.12,1.0)
def r_hem(th): return 1/math.sqrt((math.sin(th)/0.208)**2+(math.cos(th)/0.178)**2)
def r_skirt(th,f):
    rt=r_skirt_top(th); return rt+(r_hem(th)-rt)*f**0.72
def skirt_z(f): return ZS0-(ZS0-HEMZ)*f
tails=[]
for k in range(2):
    cen=[]
    for j in range(7):
        f=j/6; z=0.995-0.250*f-0.01*k*f; th=THK+(0.30 if k==0 else -0.22)*f
        ff=max(0.0,(ZS0-z)/(ZS0-HEMZ))
        rr=max(r_skirt(th,ff),r_body(th,min(z,1.0))+0.03)+0.014
        cen.append((Vector((0,CY,z))+dirv(th)*rr,th))
    tails.append(cen)
    NF=12; P=[]
    for j in range(NF+1):
        f=j/NF; i0=int(min(5,f*6)); t_=f*6-i0
        c=cen[i0][0].lerp(cen[i0+1][0],t_); th=lerp(cen[i0][1],cen[i0+1][1],t_)
        hw=0.026*(1+0.30*f); tgv=Vector((math.cos(th),math.sin(th),0)); nv_=dirv(th); row=[]
        for b in range(7):
            u=-1+2*b/6; p=c+tgv*hw*u
            p+=nv_*(0.0085*math.sin(2*math.pi*(0.85*u)+f*6.0)*(f**0.7)+0.0035*math.sin(math.pi*(b/6)))     # 垂れのひだ
            p+=tgv*0.004*math.sin(f*11+u*2)*abs(u)*f                                              # 縁のゆらぎ
            p+=Z*0.030*(1-abs(u))*sstep(f,0.78,1.0)                                               # 先端はツバメの尾のV字切れ込み
            row.append(p)
        P.append(row)
    def twf(co,r,c,k=k):
        f=r/NF; w={}
        add_w(w,"upper_body",max(0.0,1-f*6))
        for s_ in range(3):
            cen_s=(s_+0.5)/3; wgt=max(0.0,1-abs(f-cen_s)*3)
            add_w(w,f"KObiTail_{k}_{s_}",wgt*min(1.0,f*6))
        return norm_w(w)
    acc.grid(P,twf,"bow",lambda r,c:(c/6,r/NF),ref=lambda cc:Vector((0,CY,cc.z)),smooth=True)

# ---- 4g. 短い着物スカート ----
NA=56; NRS=12
def skirt_pt(phi,f):
    g=gap(f); th=g+(2*math.pi-2*g)*phi
    r=r_skirt(th,f)*(1+0.010*math.sin(phi*math.pi*2*13)*f)
    return Vector((0,CY,skirt_z(f)))+dirv(th)*r,th
def skirt_w(f,phi):
    # 列(8)×節(3): 上端は下半身、節の中央で1になる補間(列方向にもなめらかに)
    w={}; top=max(0.0,1-f/0.10); add_w(w,"lower_body",top)
    cc=phi*8-0.5; c0=int(math.floor(cc)); wc=cc-c0
    sc=f*3-0.5; s0=int(math.floor(sc)); ws=sc-s0
    for cj,wcj in ((c0,1-wc),(c0+1,wc)):
        cj=max(0,min(7,cj))
        for sj,wsj in ((s0,1-ws),(s0+1,ws)):
            sj=max(0,min(2,sj)); add_w(w,f"KSkirt_{cj}_{sj}",(1-top)*wcj*wsj)
    return norm_w(w)
P=[];PHI=[];FF=[]
for j in range(NRS+1):
    f=j/NRS; P.append([skirt_pt(c/NA,f)[0] for c in range(NA+1)])
acc.grid(P,lambda co,r,c:skirt_w(r/NRS,c/NA),"skirt",lambda r,c:(c/NA*1.1/0.6*1.0+0.0,1-r/NRS),ref=lambda cc:Vector((0,CY,cc.z)),smooth=True)
# 裾: 白フリル(上)+ラベンダーのフリル(下)、橙ビーズの列
for lay,(mat,wd,am,lm,off,ph) in enumerate((("lilac",0.052,0.014,0.030,-0.004,1.5),("white",0.038,0.011,0.024,0.0,0.0))):
    pts=[];nr=[];ds=[]
    for c in range(NA+1):
        p,th=skirt_pt(c/NA,1.0); d=dirv(th); pts.append(p+d*(0.004+off)); nr.append(d); ds.append((Z*-0.94+d*0.34).normalized())
    ruffle(acc,pts,nr,ds,wd,am,lm,mat,lambda co,r,c:skirt_w(1.0,c/((len(pts)-1)*5) if False else min(1.0,max(0.0,(math.atan2(co.x,-(co.y-CY))%(2*math.pi)-gap(1.0))/(2*math.pi-2*gap(1.0))))),rows=3,uv_s=0.1,phase=ph)
nb=int(2*math.pi*0.2/0.05)
for i in range(nb+1):
    ph=(i+0.5)/(nb+1); p,th=skirt_pt(ph,1.0); d=dirv(th)
    acc.sphere(p+d*0.012+Z*0.002,0.0115,"bead",skirt_w(1.0,ph),seg=10,rings=7)
# 前の開き(左右の縁)に白フリル
for side in (0,1):
    pts=[];nr=[];ds=[]
    for j in range(9):
        f=0.34+0.66*j/8; p,th=skirt_pt(0.0 if side==0 else 1.0,f); d=dirv(th); pts.append(p+d*0.003); nr.append(d)
        tg=Vector((math.cos(th),math.sin(th),0)); ds.append(tg*(1 if side==0 else -1)*-1 if False else (tg*(-1 if side==0 else 1)*1.0*-1))
    ruffle(acc,pts,nr,ds,0.018,0.006,0.016,"white",lambda co,r,c:skirt_w(max(0.0,(skirt_z(0)-co.z)/(skirt_z(0)-skirt_z(1))),0.02 if side==0 else 0.98),rows=3,uv_s=0.1)

# ================= 5. 袖(別パーツ。左を作って右はミラー) =================
A0,A1,A2,A3=B("arm_L"),B("elbow_L"),B("wrist_L"),Tl("wrist_L")
SEG=[(A0,A1),(A1,A2),(A2,A3)]; LENS=[(b-a).length for a,b in SEG]; CUM=[0,LENS[0],LENS[0]+LENS[1],sum(LENS)]
def arm_at(s):
    for i in range(3):
        if s<=CUM[i+1]+1e-9 or i==2:
            t=(s-CUM[i])/LENS[i]; a,b=SEG[i]; return a.lerp(b,t),(b-a).normalized()
S0,S1=0.095,CUM[2]+0.05              # 袖の開始(上腕)〜終端(手首の少し手前)
def R_of(t): return lerp(0.044,0.078,sstep(t,0.0,0.55))*(1-0.5*sstep(t,0.78,1.0))
def HANG(t): return 0.105*math.sin(math.pi*min(1,max(0,t))**0.85)**1.2
def sag(t): return max(0.0,R_of(t)-0.046)*0.55
NT=14; NPH=28
def sleeve_frame(t):
    s=lerp(S0,S1,t); p,a=arm_at(s); u=Vector((0,-1,0)); v=a.cross(u).normalized()
    if v.z<0: v=-v
    u=v.cross(a).normalized()
    if u.y>0: u=-u
    return p,a,u,v
def sleeve_w(t,phi,e,h):
    """袖の頂点ウェイト: 腕ボーン(arm→elbow→wrist)を位置で補間。下側の垂れは揺れ物ボーン(列3x節2)へ。"""
    s=lerp(S0,S1,t); w={}
    if s<CUM[1]-0.03: add_w(w,"arm_L",1.0)
    elif s<CUM[1]+0.03: x=(s-(CUM[1]-0.03))/0.06; add_w(w,"arm_L",1-x); add_w(w,"elbow_L",x)
    elif s<CUM[2]-0.05: add_w(w,"elbow_L",1.0)
    else: x=min(1,(s-(CUM[2]-0.05))/0.05); add_w(w,"elbow_L",1-x); add_w(w,"wrist_L",x)
    if h>0.012:
        q=e/h                                    # 垂れ量に対する下方向の伸び割合
        ws=sstep(q,0.15,0.6)*sstep(t,0.12,0.30)*(1-sstep(t,0.93,1.0))
        tc=[0.36,0.60,0.82]; cc=[]
        for k,tk in enumerate(tc): cc.append(max(0.0,1-abs(t-tk)/0.24))
        tot=sum(cc)
        if tot>1e-6 and ws>0:
            s1=sstep(q,0.55,1.0)
            for k in range(3):
                x=ws*cc[k]/tot
                add_w(w,f"KSleeve_L_{k}_0",x*(1-s1)); add_w(w,f"KSleeve_L_{k}_1",x*s1)
            for kk in list(w):
                if not kk.startswith("KSleeve"): w[kk]*=(1-ws)
    return norm_w(w)
SL_AXIS={}
def sleeve_pt(t,phi):
    p,a,u,v=sleeve_frame(t); R=R_of(t); c=p-Z*sag(t); ph=phi*2*math.pi
    off=R*(math.cos(ph)*u+math.sin(ph)*v); e=0.0
    if math.sin(ph)<0: e=HANG(t)*(-math.sin(ph))**1.6
    return c+off-Z*e,e,HANG(t)
def build_sleeve(side):
    f=(lambda p:p) if side>0 else mx
    sg=side
    P=[];E=[]
    for r in range(NT+1):
        t=r/NT; row=[];er=[]
        for c in range(NPH):
            q,e,h=sleeve_pt(t,c/NPH); row.append(f(q)); er.append((e,h))
        P.append(row); E.append(er)
    def wf(co,r,c):
        e,h=E[r][c]; w=sleeve_w(r/NT,c/NPH,e,h)
        if side<0: w={k.replace("_L","_R"):x for k,x in w.items()}
        return w
    axis=lambda cc:(lambda t:sleeve_frame(t)[0])(0.5)
    refc=lambda cc: f(arm_at(lerp(S0,S1,min(1,max(0,((mx(cc) if side<0 else cc)-A0).length/(0.4)))))[0]-Z*0.02)
    acc.grid(P,wf,"jelly",lambda r,c:(c/NPH*2*math.pi*0.07/TILE,r/NT*0.30/TILE*2),closed=True,ref=refc,smooth=True)
    # 上端: 紺フリル帯(上腕)+橙ビーズ5個
    p,a,u,v=sleeve_frame(0.0); R0=R_of(0.0)
    pts=[];nr=[];ds=[]
    for c in range(24):
        ph=2*math.pi*c/24; off=math.cos(ph)*u+math.sin(ph)*v
        pts.append(f(p+off*(R0+0.002)-a*0.020)); nr.append(f(off)-f(Vector((0,0,0)))); ds.append((f(a)*0.9+f(off)*0.25).normalized() if True else None)
    nr=[n.normalized() for n in nr]
    def bw(co,r,c): return {("arm_L" if side>0 else "arm_R"):1.0}
    ruffle(acc,pts,nr,ds,0.022,0.0055,0.0125,"navy",bw,closed=True,rows=3,uv_s=0.08)
    for k in range(5):
        ph=math.radians(-150+k*45); off=math.cos(ph)*u+math.sin(ph)*v
        acc.sphere(f(p+off*(R0+0.004)+a*0.006),0.0115,"bead",bw(None,0,0),seg=10,rings=7)
    # 手首: 紺フリルの袖口(袖の終端リングに付ける)
    p,a,u,v=sleeve_frame(1.0); R1=R_of(1.0)+0.002
    pts=[];nr=[];ds=[]
    for c in range(20):
        ph=2*math.pi*c/20; off=math.cos(ph)*u+math.sin(ph)*v
        pts.append(f(p-Z*sag(1.0)+off*R1)); nr.append((f(off)-f(Vector((0,0,0)))).normalized()); ds.append((f(a)*0.85+f(off)*0.3).normalized())
    def cw(co,r,c): return {("wrist_L" if side>0 else "wrist_R"):1.0}
    ruffle(acc,pts,nr,ds,0.026,0.005,0.0125,"navy",cw,closed=True,rows=4,uv_s=0.08)
build_sleeve(1); build_sleeve(-1)

# ================= 6. 素足+サンダル+足首のフリル(左を作って右はミラー) =================
FXC,FYH,FYT=0.0715,0.078,-0.108          # 足の中心x、かかと後端y、つま先y
def foot_top(y): return float(np.interp(y,[-0.108,-0.07,-0.02,0.02,0.05,0.075,0.080],[0.014,0.028,0.050,0.066,0.088,0.062,0.030]))
def foot_w(y): return float(np.interp(y,[-0.108,-0.095,-0.07,-0.03,0.02,0.06,0.078],[0.020,0.033,0.0375,0.032,0.027,0.027,0.018]))
FZB=0.003
def build_foot(side):
    f=(lambda p:p) if side>0 else mx
    wfoot=lambda co,r,c:{("ankle_L" if side>0 else "ankle_R"):1.0}
    UVS=lambda r,c:tuple(SUV[side])
    # 足: 後ろ→前へ断面を並べる
    ys=[FYH-(FYH-FYT)*i/22 for i in range(23)]
    P=[]
    for y in ys:
        w=foot_w(y); zt=foot_top(y); tp=1.0
        if y<FYT+0.02: tp=math.sqrt(max(0.15,(y-FYT)/0.02))
        if y>FYH-0.015: tp=math.sqrt(max(0.15,(FYH-y)/0.015))
        row=[]
        for k in range(16):
            a=2*math.pi*k/16; ca,sa=math.cos(a),math.sin(a); n=2.6
            cx=math.copysign(abs(ca)**(2/n),ca)*w*tp; cz=math.copysign(abs(sa)**(2/n),sa)
            zc=(zt+FZB)/2; hz=(zt-FZB)/2*tp
            row.append(f(Vector((FXC+cx,y,zc+cz*hz))))
        P.append(row)
    G=[[P[i][k] for i in range(len(ys))] for k in range(16)]   # 行=周方向 列=前後 → 転置して使う
    G=[[P[i][k] for k in range(16)] for i in range(len(ys))]
    acc.grid(G,wfoot,"skin",UVS,closed=True,flip=(side<0),ref=lambda c:f(Vector((FXC,(FYH+FYT)/2,0.04))),smooth=True)
    # すね(足首まで)
    P=[]
    for j in range(5):
        z=lerp(0.125,0.072,j/4); cy=0.048+0.002*j/4; rx=0.0215-0.001*j/4; ry=0.025-0.003*j/4
        P.append([f(Vector((0.0755+rx*math.cos(2*math.pi*k/16),cy+ry*math.sin(2*math.pi*k/16),z))) for k in range(16)])
    lw=lambda co,r,c:({("knee_L" if side>0 else "knee_R"):1-r/4*0.9,("ankle_L" if side>0 else "ankle_R"):r/4*0.9+0.1})
    acc.grid(P,lw,"skin",UVS,closed=True,flip=(side<0),ref=lambda c:f(Vector((0.0755,0.048,c.z))),smooth=True)
    # 足指5本(親指が内側=体の中心側)
    for k,(dx,dy,rs) in enumerate(((-0.0195,0.0,1.25),(-0.0095,0.007,0.95),(0.0,0.011,0.88),(0.0095,0.015,0.8),(0.0175,0.018,0.72))):
        acc.sphere(f(Vector((FXC+dx*0.95,FYT-0.004+dy,0.0105))),0.0085*rs,"skin",wfoot(None,0,0),sc=(1.0,1.25,0.95),seg=8,rings=6)
        for v in acc.bm.verts[-0:]: pass
    # サンダルの底(足の輪郭より一回り大きい板)
    out=[]
    for y in [FYH+0.006]+[FYH-(FYH-FYT)*i/16 for i in range(17)]+[FYT-0.012]:
        out.append((y,foot_w(max(min(y,FYH),FYT))+0.010))
    loop=[(FXC+w,y) for y,w in out]+[(FXC-w,y) for y,w in reversed(out)]
    top=[];bot=[]
    for (x,y) in loop:
        cx,cy=FXC,(FYH+FYT)/2; d=Vector((x-cx,y-cy));
        top.append(f(Vector((x,y,FZB))));bot.append(f(Vector((x+(cx-x)*0.0,y,-0.011))))
    vt=[acc.vert(p,{("ankle_L" if side>0 else "ankle_R"):1.0}) for p in top]; vb=[acc.vert(p,{("ankle_L" if side>0 else "ankle_R"):1.0}) for p in bot]
    n=len(loop)
    for i in range(n):
        j=(i+1)%n; q=[vb[i],vb[j],vt[j],vt[i]]
        if side<0: q=q[::-1]
        acc.face(q,"sandal",[(0,0)]*4,smooth=False)
    ft=acc.face(vt if side>0 else vt[::-1],"sandal",[(0,0)]*n,smooth=False); fb=acc.face(vb[::-1] if side>0 else vb,"sandal",[(0,0)]*n,smooth=False)
    for fc in (ft,fb):
        if fc is None: continue
    # 鼻緒(Vの字): 土踏まずの両脇から足の甲の上を通って、親指と人さし指の間へ
    def surf_z(y,x):
        w=foot_w(y); zt=foot_top(y); dx=abs(x-FXC)/w;
        return FZB+(zt-FZB)*(max(0.0,1-dx**2.6))**(1/2.6)*1.0
    xt=FXC-0.004; yt=-0.083
    for sgn in (-1,1):
        xs=FXC+sgn*(foot_w(-0.02)+0.003)
        cen=[]
        for i in range(8):
            ff=i/7; x=lerp(xs,xt,ff**0.85); y=lerp(-0.02,yt,ff); z=surf_z(y,x)+0.0035
            if ff>0.85: z=lerp(z,FZB+0.002,(ff-0.85)/0.15)
            cen.append(Vector((x,y,z)))
        P=[]
        for i,c in enumerate(cen):
            tg=(cen[min(i+1,7)]-cen[max(i-1,0)]).normalized(); sd=tg.cross(Z).normalized()*0.0055
            P.append([f(c-sd),f(c+sd)])
        acc.grid(P,wfoot,"sandal",lambda r,c:(0,0),ref=lambda cc:f(Vector((FXC,-0.04,0.0))),smooth=True)
    # 足首の青フリル+ビーズ
    pts=[];nr=[];ds=[]
    for k in range(20):
        a=2*math.pi*k/20; ca,sa=math.cos(a),math.sin(a); p=Vector((0.0755+0.0235*ca,0.049+0.026*sa,0.108)); pts.append(f(p))
        o=Vector((ca,sa,0)); nr.append(f(o)-f(Vector((0,0,0)))); ds.append((f(Vector((0,0,-0.93)))+f(o)-f(Vector((0,0,0)))*(-0.0)+(f(o)-f(Vector((0,0,0))))*0.4).normalized())
    nr=[n.normalized() for n in nr]
    ruffle(acc,pts,nr,ds,0.026,0.0075,0.0115,"bfrill",wfoot,closed=True,rows=3,uv_s=0.08)
    for k in range(10):
        a=2*math.pi*(k+0.5)/10; p=Vector((0.0755+0.0255*math.cos(a),0.049+0.028*math.sin(a),0.109))
        acc.sphere(f(p),0.0072,"bead",wfoot(None,0,0),seg=8,rings=6)
build_foot(1); build_foot(-1)

# ================= 7. ボーン(揺れ物)を追加 =================
bpy.context.view_layer.objects.active=arm; bpy.ops.object.mode_set(mode="EDIT")
E=arm.data.edit_bones; NEWB={}
def newbone(name,h,t,parent,conn=False,jp=""):
    b=E.new(name); b.head=h; b.tail=t; b.parent=E[parent]; b.use_connect=conn; b.use_deform=True; NEWB[name]=jp; return b
# スカート 8列x3節
for c in range(8):
    phi=(c+0.5)/8; prev="lower_body"
    for s in range(3):
        f0=s/3; f1=(s+1)/3
        h=skirt_pt(phi,f0)[0]; t=skirt_pt(phi,f1)[0]
        h=h.lerp(Vector((h.x,h.y,h.z)),0);
        b=newbone(f"KSkirt_{c}_{s}",h,t,prev,conn=(s>0),jp=f"裾{c+1}_{s+1}"); prev=b.name
# 袖: 左右 3列x2節(腕/ひじの子。リング下端から真下へ垂れる)
for side,sf in ((1,"L"),(-1,"R")):
    f=(lambda p:p) if side>0 else mx
    for k,tk in enumerate((0.36,0.60,0.82)):
        p,a,u,v=sleeve_frame(tk); R=R_of(tk); c=p-Z*sag(tk); hang=HANG(tk)
        head=f(c-v*R*0.92); L1=max(0.03,hang*0.55); par=f"arm_{sf}" if tk<0.5 else f"elbow_{sf}"
        b0=newbone(f"KSleeve_{sf}_{k}_0",head,head-Z*L1,par,jp=f"{'左' if side>0 else '右'}袖{k+1}_1")
        newbone(f"KSleeve_{sf}_{k}_1",head-Z*L1,head-Z*(L1+max(0.03,hang*0.5)),b0.name,conn=True,jp=f"{'左' if side>0 else '右'}袖{k+1}_2")
# 帯の垂れ 2本x3節(上半身の子)
for k in range(2):
    cen=tails[k]; prev="upper_body"
    for s in range(3):
        h=cen[s*2][0]; t=cen[s*2+2][0]
        b=newbone(f"KObiTail_{k}_{s}",h,t,prev,conn=(s>0),jp=f"帯{k+1}_{s+1}"); prev=b.name
bpy.ops.object.mode_set(mode="OBJECT")
for n,jp in NEWB.items():
    pb=arm.pose.bones[n]; pb.mmd_bone.name_j=jp; pb.mmd_bone.name_e=n

# ================= 8. メッシュオブジェクトを作る(骨のウェイト付き) =================
me=bpy.data.meshes.new("Nowa_Kimono_mesh"); acc.bm.to_mesh(me); acc.bm.free()
for k in MATORDER: me.materials.append(M[k])
o=bpy.data.objects.new("Nowa_Kimono_mesh",me)
for c in body.users_collection: c.objects.link(o)
o.parent=arm; o.matrix_parent_inverse=body.matrix_parent_inverse.copy()
for n,i in sorted(acc.gi.items(),key=lambda kv:kv[1]): o.vertex_groups.new(name=n)
md=o.modifiers.new("Armature","ARMATURE"); md.object=arm
missing=[n for n in acc.gi if n not in arm.data.bones]
print("missing bones for groups:",missing)
for p in me.polygons: p.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=S+"/nowa_s2.blend")
print("DONE2 verts",len(me.vertices),"faces",len(me.polygons),"bones added",len(NEWB))
