# 顔の再現度向上: 基本表情(クール)焼き込み・つり目化・輪郭・瞳テクスチャ・アホ毛/跳ね毛
import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
S=sys.argv[sys.argv.index("--")+1]
h=bpy.data.objects["head"]; me=h.data; kbs=me.shape_keys.key_blocks; B=kbs["Basis"]; n=len(me.vertices)
def arr(kb): a=np.empty(n*3,np.float32); kb.data.foreach_get("co",a); return a.reshape(n,3)
base=arr(B); keys={k.name:arr(k) for k in kbs[1:]}

# ---- 1. 基本表情の焼き込み(各キーが動かす頂点はキー本来の形を優先) ----
MIX={"lip_up":0.8,"eye_zitome":0.85,"eye_close":0.15,"eye_angry":0.3,"face_happy":0.08,"eye_black_small":0.8,"eye_brow_down":0.35}   # 半目の伏し目+低い眉(参考: 気だるげな切れ長)
SERIOUS={"face_angry":0.35,"eye_zitome":0.35,"eye_black_small":0.4,"lip_down":0.3,"eye_brow_down":0.2}
delta=sum((keys[k]-base)*w for k,w in MIX.items())
newbase=base+delta
newkeys={}
for k,a in keys.items():
    moved=np.linalg.norm(a-base,axis=1)>1e-5
    newkeys[k]=np.where(moved[:,None],a,a+delta)
orig=base
base=newbase
# 追加モーフ(絶対形状): 真顔=2枚目の参考、ニヤリウィンク=1枚目の参考(右目を閉じる)
serious=orig+sum((keys[k]-orig)*w for k,w in SERIOUS.items())
wmove=np.linalg.norm(keys["blink_R"]-orig,axis=1)>1e-5
wink=np.where(wmove[:,None],keys["blink_R"],newbase)+(keys["lip_up"]-orig)*0.25

# ---- 2. 形状調整(全キーに同じ関数を適用) ----
EC=np.array([0.0523,-0.0904,1.5867]); MZ=1.5212; CZ=1.4720
_mv=lambda k: np.linalg.norm(keys[k]-orig,axis=1)>1e-5
BROW=_mv("eye_brow_down")&~_mv("eye_close")&~_mv("eye_zitome")&(orig[:,2]>EC[2]+0.012)   # 眉だけの頂点(まぶたは除く)
print("BROW verts",int(BROW.sum()))
def sm(e0,e1,x): t=np.clip((x-e0)/(e1-e0),0,1); return t*t*(3-2*t)
def F(p):
    p=p.copy(); x,y,z=p[:,0],p[:,1],p[:,2]; ax=np.abs(x)
    front=1-sm(-0.07,-0.02,y)
    # つり目: 目の周り(まぶた・瞳)の外側を持ち上げ、縦をやや詰める
    we=(1-sm(0.022,0.04,np.abs(z-EC[2])))*(1-sm(0.085,0.10,ax))*sm(0.008,0.02,ax)*front
    p[:,2]+=we*(0.10*(ax-EC[0]))
    p[:,2]=EC[2]+(p[:,2]-EC[2])*(1-0.05*we)
    p[:,0]+=np.sign(x)*we*0.10*np.clip(ax-EC[0],0,None)   # 目尻側へ切れ長に
    # 眉: 目頭側を下げて内へ向かって下がる直線的な眉に
    bi=np.clip(1-(ax-0.012)/0.07,0,1)
    p[:,2]-=BROW*(0.010+0.010*bi**1.2)   # 眉を目のすぐ上へ下げ、目頭側ほど低く(内へ向かって下がる)
    # 輪郭: 顎を下へ伸ばして細く、頬を少し削る
    tj=sm(MZ+0.01,CZ,z)*front
    p[:,2]-=0.003*tj; p[:,0]*=1-0.07*tj-0.08*tj**1.6   # 顎先へ向かって細く(V字の輪郭)
    tc=(1-sm(0.0,0.03,np.abs(z-(MZ+0.03))))*sm(0.04,0.08,ax)*(1-sm(-0.03,0.02,y))
    p[:,0]*=1-0.05*tc
    return p
base=F(base); newkeys={k:F(a) for k,a in newkeys.items()}
for nm,a in (("serious",serious),("smirk_wink",wink)):
    h.shape_key_add(name=nm,from_mix=False); newkeys[nm]=F(a)
B.data.foreach_set("co",base.ravel())
for k,a in newkeys.items(): kbs[k].data.foreach_set("co",a.ravel())
me.vertices.foreach_set("co",base.ravel()); me.update()

# ---- 3. 瞳を小さく鋭く(虹彩を中心から縮小、瞳孔を追加) ----
im=bpy.data.images["faceparts"]; W,H=im.size
a=np.array(im.pixels[:],np.float32).reshape(H,W,4)
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
for cx in (265.0,760.0):     # 左右の虹彩の中心(上原点のx)
    cy_top=440.0; cy=H-1-cy_top
    box=(np.abs(xx-cx)<215)&(np.abs(yy-cy)<290)
    k=1.13
    sx=np.clip(cx+(xx-cx)*k,0,W-1).astype(int); sy=np.clip(cy+(yy-cy)*k,0,H-1).astype(int)
    samp=a[sy,sx]
    a=np.where(box[...,None],samp,a)
    # 縦長の瞳孔
    d=((xx-cx)/17)**2+((yy-(cy-10))/46)**2   # 小さな縦長の瞳孔
    m=np.clip(1.3-d,0,1)[...,None]*box[...,None]*0.75
    a[...,:3]=a[...,:3]*(1-m)+np.array([0.10,0.05,0.16])*m
im.pixels[:]=a.ravel(); im.pack()

# ---- 4. アホ毛・跳ね毛(先細りの房を頭ボーンに追従) ----
hair=bpy.data.objects["hair"]
dg=bpy.context.evaluated_depsgraph_get()
bvh=BVHTree.FromObject(hair,dg)
hm=bpy.data.materials.new("hair_strand"); hm.use_nodes=True
pn=hm.node_tree.nodes["Principled BSDF"]; pn.inputs["Base Color"].default_value=(0.006,0.005,0.008,1); pn.inputs["Roughness"].default_value=0.85; pn.inputs["Specular IOR Level"].default_value=0.15
bm=bmesh.new()
HC=Vector((0,0.005,1.64))
def surf(dirv):
    d=Vector(dirv).normalized(); loc,nrm,_,_=bvh.ray_cast(HC+d*0.4,-d); return loc,nrm
def lock(dirs,width,lift=(0.0,0.006),ext=None,seg=16,flat=0.14):
    """dirs: 頭の中心から見た方向の列。髪表面に沿う点列を作り、毛先側ほど浮かせる。ext: 表面から外れた毛先の延長ベクトル"""
    pts=[];nrms=[]
    for d in dirs:
        loc,nr=surf(d)
        if loc is None: continue
        pts.append(loc); nrms.append(nr)
    if len(pts)<2: return
    if ext:
        b0=pts[-1].copy()   # 延長点は表面上の最終点からの相対位置
        for e in (ext if isinstance(ext[0],tuple) else [ext]): pts.append(b0+Vector(e)); nrms.append(nrms[-1])
    # 点列をCatmull-Rom的に補間
    P=[];Nn=[]
    for i in range(seg+1):
        t=i/seg*(len(pts)-1); k=min(int(t),len(pts)-2); f=t-k
        p0=pts[max(k-1,0)]; p1=pts[k]; p2=pts[k+1]; p3=pts[min(k+2,len(pts)-1)]
        P.append(0.5*((2*p1)+(-p0+p2)*f+(2*p0-5*p1+4*p2-p3)*f*f+(-p0+3*p1-3*p2+p3)*f**3))
        Nn.append(nrms[k].lerp(nrms[k+1],f).normalized())
    rings=[]
    for i,(p,nr) in enumerate(zip(P,Nn)):
        t=i/seg
        tg=(P[min(i+1,seg)]-P[max(i-1,0)]).normalized()
        side=nr.cross(tg).normalized(); up=tg.cross(side).normalized()
        w=width*(1-t**1.6)+0.0005
        c=p+nr*(0.0015+lift[0]+(lift[1]-lift[0])*t*t)
        rings.append([bm.verts.new(c+side*math.cos(a)*w+up*math.sin(a)*w*flat) for a in [2*math.pi*j/6 for j in range(6)]])
    for i in range(seg):
        for j in range(6): bm.faces.new((rings[i][j],rings[i][(j+1)%6],rings[i+1][(j+1)%6],rings[i+1][j]))
    tip=bm.verts.new(P[-1]+(P[-1]-P[-2])*0.5)
    for j in range(6): bm.faces.new((rings[-1][j],rings[-1][(j+1)%6],tip))
# アホ毛: 頭頂から小さな輪を描いて前へ跳ねる一房(控えめ)
k_=0.5
lock([(0.02,0.25,1),(0.02,0.12,1)],0.007,lift=(0,0),seg=24,flat=0.3,
     ext=tuple(tuple(c*k_ for c in e) for e in ((0.002,0.014,0.028),(0.004,0.006,0.056),(0.007,-0.02,0.072),(0.010,-0.048,0.066),(0.013,-0.068,0.042),(0.015,-0.074,0.014),(0.016,-0.066,-0.004))))
pass #lock([(0.03,0.06,1),(0.035,0.11,1)
# 跳ね毛は控えめに: サイド各1本・襟足各1本、角度は緩く
for sx in (1,-1):
    lock([(sx*0.35,1,-0.1),(sx*0.4,1,-0.45)],0.009,lift=(0,0.003),ext=(sx*0.006,0.01,-0.02))
# 前髪: 額から目の高さまで落ちる先細りの房(眉間と両目の上に掛かる)
for x0,ex,w in ((0.0,(0.002,-0.012,-0.045),0.012),(0.018,(0.004,-0.012,-0.036),0.010),(-0.020,(-0.004,-0.012,-0.034),0.010),
              (0.042,(0.008,-0.010,-0.040),0.011),(-0.045,(-0.008,-0.010,-0.038),0.011),(0.068,(0.012,-0.006,-0.030),0.010),(-0.070,(-0.012,-0.006,-0.030),0.010)):
    lock([(x0,-1,0.55),(x0*1.05,-1,0.28)],w,lift=(0.001,0.005),ext=ex,flat=0.16)
# 横髪: 耳を覆ってあごの高さまで届く
for sx in (1,-1):
    for yy_,w_ in ((-0.03,0.013),(0.03,0.012)):   # 耳を上から覆ってあごの方へ落ちる横髪
        top,_=surf((sx,yy_,0.45))
        if top is None: continue
        tgt=[Vector((sx*0.122,top.y-0.004,1.575)),Vector((sx*0.118,top.y-0.010,1.545)),Vector((sx*0.110,top.y-0.016,1.515))]
        lock([(sx,yy_,0.55),(sx,yy_,0.45)],w_,lift=(0.0,0.002),ext=tuple(tuple(t-top) for t in tgt),flat=0.16)
# 頭頂〜後頭部: 外へ跳ねる毛束
for d,ex in (((0.25,0.5,1),(0.012,0.012,0.022)),((-0.3,0.45,1),(-0.014,0.012,0.02)),((0.0,0.8,0.7),(0.0,0.024,0.014)),((0.45,0.7,0.5),(0.02,0.014,0.01)),((-0.45,0.7,0.5),(-0.02,0.014,0.01))):
    lock([d,(d[0]*1.05,d[1]*1.05,d[2]*0.97)],0.010,lift=(0.001,0.003),ext=ex,flat=0.2)
ob=bpy.data.objects.new("hair_strands",bpy.data.meshes.new("hair_strands")); bpy.context.scene.collection.objects.link(ob)
bm.to_mesh(ob.data); bm.free(); ob.data.materials.append(hm)
for p in ob.data.polygons: p.use_smooth=True
vg=ob.vertex_groups.new(name="head 1"); vg.add(range(len(ob.data.vertices)),1.0,"REPLACE")
ob.parent=hair.parent; md=ob.modifiers.new("Armature","ARMATURE"); md.object=hair.parent
bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True); hair.select_set(True); bpy.context.view_layer.objects.active=hair
bpy.ops.object.join()
bpy.ops.wm.save_as_mainfile(filepath=S+"/nemo_s2f.blend")
print("DONEF")
