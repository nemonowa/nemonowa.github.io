# 着物用のテクスチャをnumpyで手続き生成する(PMXに書き出せるよう、すべて画像にする)
# 画像配列は (H,W,4) float32, 行0がBlenderのv=0(下端)。
import numpy as np, math, random

def _smooth(x,a,b):
    t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)

def stars(img,n,seed,rmin=0.8,rmax=2.0,bright=0.9,cross=0.0,tile=True):
    """白い星の点。tile=Trueで端をまたぐ点も反対側へ描く(タイル張り用)。"""
    H,W=img.shape[:2]; rnd=random.Random(seed)
    for _ in range(n):
        cx,cy=rnd.uniform(0,W),rnd.uniform(0,H); r=rnd.uniform(rmin,rmax); a=bright*rnd.uniform(0.5,1.0)
        R=int(r*3+2)
        for ox in (-W,0,W):
            for oy in (-H,0,H):
                x0,x1=int(cx+ox-R),int(cx+ox+R+1); y0,y1=int(cy+oy-R),int(cy+oy+R+1)
                if x1<=0 or y1<=0 or x0>=W or y0>=H: continue
                xs=np.arange(max(x0,0),min(x1,W)); ys=np.arange(max(y0,0),min(y1,H))
                X,Y=np.meshgrid(xs,ys); dx=X-(cx+ox); dy=Y-(cy+oy)
                m=np.exp(-(dx*dx+dy*dy)/(2*(r*0.6)**2))
                if cross>0: m=np.maximum(m,cross*(np.exp(-dx*dx/(2*0.5**2))*np.exp(-np.abs(dy)/(r*2.2))+np.exp(-dy*dy/(2*0.5**2))*np.exp(-np.abs(dx)/(r*2.2))))
                m=np.clip(m*a,0,1)[...,None]
                sub=img[ys[0]:ys[-1]+1,xs[0]:xs[-1]+1,:3]
                img[ys[0]:ys[-1]+1,xs[0]:xs[-1]+1,:3]=sub*(1-m)+np.array([1,1,1])*m
    return img

def _jelly(mask,cx,cy,s,ang,rnd,W,H):
    """くらげ1匹(傘+触手)をmask(0..1の被覆度)へ加算。傘の向きangで回転。"""
    ca,sa=math.cos(ang),math.sin(ang)
    R=int(s*3.2)
    for ox in (-W,0,W):
        for oy in (-H,0,H):
            x0,x1=int(cx+ox-R),int(cx+ox+R); y0,y1=int(cy+oy-R),int(cy+oy+R)
            if x1<=0 or y1<=0 or x0>=W or y0>=H: continue
            xs=np.arange(max(x0,0),min(x1,W)); ys=np.arange(max(y0,0),min(y1,H))
            X,Y=np.meshgrid(xs,ys); dx=X-(cx+ox); dy=Y-(cy+oy)
            lx=(dx*ca+dy*sa)/s; ly=(-dx*sa+dy*ca)/s     # 局所座標(ly>0が傘側)
            # 傘: 半楕円ドーム(縁は少し波打つ)
            lip=-0.05+0.04*np.sin(lx*9+rnd.uniform(0,6))
            dome=(lx/0.55)**2+(np.clip(ly,0,None)/0.5)**2
            bell=np.where((ly>=lip),np.clip(1-_smooth(dome,0.82,1.0),0,1),0.0)
            core=np.clip(1-_smooth(dome,0.0,0.85),0,1)*0.35        # 傘の中心を少し明るく
            m=bell*(0.62+core)
            # 触手: 下側へ蛇行しながら細くなる
            for k in range(rnd.choice((4,5,6))):
                x0_=rnd.uniform(-0.38,0.38); L=rnd.uniform(0.9,1.5); A=rnd.uniform(0.06,0.14); fr=rnd.uniform(4,7); ph=rnd.uniform(0,6.28)
                t=np.clip(-ly/L,0,1)                              # 0(付け根)→1(先)
                cxk=x0_*(1-0.3*t)+A*t*np.sin(fr*t*1.7+ph)
                w=0.10*(1-t)**0.8+0.014
                d=np.abs(lx-cxk)
                tm=np.where((ly<0.02)&(-ly<L),np.clip(1-_smooth(d,w*0.5,w),0,1)*(1-0.5*t),0.0)
                m=np.maximum(m,tm*0.8)
            sub=mask[ys[0]:ys[-1]+1,xs[0]:xs[-1]+1]; mask[ys[0]:ys[-1]+1,xs[0]:xs[-1]+1]=np.maximum(sub,m)

def blur(a,sigma):
    """タイル張りできるガウスぼかし(FFT)。"""
    H,W=a.shape; fy=np.fft.fftfreq(H)[:,None]; fx=np.fft.fftfreq(W)[None,:]
    k=np.exp(-2*(math.pi**2)*sigma**2*(fx*fx+fy*fy))
    return np.real(np.fft.ifft2(np.fft.fft2(a)*k)).astype(np.float32)

def _jelly_canvas(W,H,pos,seed,small_ref=None):
    """透ける青い着物地: 彩度の高い中間の青地に、大きく柔らかい(縁をぼかして発光する)シアンのくらげ(傘+触手)と白い星の粒。タイル張り可。"""
    rnd=random.Random(seed); img=np.zeros((H,W,4),np.float32); img[...,3]=1
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    # 地: 彩度の高い青を、大きな波状のムラで揺らす(絵の具のにじみ風)
    n=0.5+0.5*np.sin(xx/W*6.283*2+np.sin(yy/H*6.283*3)*1.4)*np.cos(yy/H*6.283*2+np.sin(xx/W*6.283)*1.1)
    lo=np.array([0.09,0.22,0.78],np.float32); hi=np.array([0.20,0.40,0.92],np.float32)
    img[...,:3]=lo+(hi-lo)*n[...,None]
    mask=np.zeros((H,W),np.float32); core=np.zeros((H,W),np.float32)
    for fx,fy,s in pos:
        sub=np.zeros((H,W),np.float32); _jelly(sub,fx*W,fy*H,s,rnd.uniform(-0.45,0.45),rnd,W,H); mask=np.maximum(mask,sub)
        sub2=np.zeros((H,W),np.float32); _jelly(sub2,fx*W,fy*H-0.1*s,s*0.55,0.0,random.Random(1),W,H); core=np.maximum(core,sub2)
    soft=np.clip(blur(mask,2.6)*1.1,0,1)               # 縁のぼけ
    glow=np.clip(blur(mask,16.0)*1.5,0,1)               # にじむ発光
    cyan=np.array([0.55,0.97,1.0],np.float32); white=np.array([0.90,1.0,1.0],np.float32)
    m=np.clip(glow*0.26,0,1)[...,None]
    img[...,:3]=img[...,:3]*(1-m)+cyan*0.85*m
    m=(soft*0.92)[...,None]; img[...,:3]=img[...,:3]*(1-m)+cyan*m
    c=np.clip(blur(core,6.0)*1.2*soft,0,1)[...,None]*0.7; img[...,:3]=img[...,:3]*(1-c)+white*c
    rim=np.clip(soft-blur(mask,9.0)*1.1,0,1)[...,None]*0.9; img[...,:3]=img[...,:3]*(1-rim)+white*rim      # 縁の明るい輪郭(絵の具のふち)
    stars(img,170,seed+1,0.9,2.2,0.85)
    return img

def jelly_tex(W=1024,H=1024,seed=3):
    """袖用のタイル張りできるくらげ柄(0.36m角)。"""
    pos=[(0.18,0.20,230),(0.62,0.12,200),(0.88,0.48,150),(0.36,0.58,250),(0.80,0.84,190),(0.08,0.80,140),(0.55,0.92,120),
         (0.30,0.30,80),(0.97,0.18,90),(0.70,0.55,85)]
    return _jelly_canvas(W,H,pos,seed)

def bodice_tex(W=1024,H=576,seed=7):
    """着物トップ用: 胴まわり1周(u=角度/2π、前中央がu=0)×高さ0.32m(v)。胸の見える位置に大きなくらげを意図して配置する。"""
    pos=[(0.905,0.62,130),(0.955,0.43,70),(0.835,0.80,64),            # 下前(画像の左側の胸)
         (0.165,0.60,140),(0.12,0.43,66),(0.245,0.80,76),             # 上前(右側の胸)
         (0.50,0.60,160),(0.62,0.72,120),(0.40,0.45,100),(0.72,0.50,90),(0.30,0.25,80)]   # 横・背中
    return _jelly_canvas(W,H,pos,seed)

def lining_tex(W=256,H=256,seed=4):
    """裏地: 彩度のある深めの青に、ゆるい縦の陰影(平坦に見えないように)と薄いくらげの影。"""
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    n=0.5+0.5*np.sin(xx/W*6.283*3+np.sin(yy/H*6.283*2)*1.6)
    img=np.ones((H,W,4),np.float32)
    lo=np.array([0.10,0.20,0.62],np.float32); hi=np.array([0.20,0.36,0.82],np.float32)
    img[...,:3]=lo+(hi-lo)*(0.25+0.75*n)[...,None]*(0.85+0.15*np.sin(yy/H*6.283))[...,None]
    return img

def obi_tex(W=256,H=256):
    """帯: 深い紅色。上下の縁は少し暗く、中央に柔らかなハイライト、縦のゆるい折れ(ひだ)の陰影。vが高さ、uは周方向(3回繰り返し)。"""
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32); v=yy/H; u=xx/W
    base=np.array([0.80,0.10,0.25],np.float32)
    sh=0.78+0.34*np.sin(math.pi*v)**0.8                       # 縁が暗く中央が明るい
    fold=1.0+0.07*np.sin(u*6.283*7+v*2.0)+0.04*np.sin(u*6.283*13+1.0)
    img=np.ones((H,W,4),np.float32); img[...,:3]=np.clip(base*(sh*fold)[...,None],0,1)
    return img

def bow_tex(W=256,H=256,dark=False):
    """蝶結び: 透けるような淡いアクア。u=輪の根元→先、v=輪の幅方向。中央がやや明るく縁は少し濃い。"""
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32); u=xx/W; v=yy/H
    c=np.array([0.50,0.82,0.95] if not dark else [0.32,0.62,0.86],np.float32)
    e=np.sin(math.pi*v)**0.6
    img=np.ones((H,W,4),np.float32); img[...,:3]=c*(0.84+0.2*e)[...,None]*(0.95+0.07*np.sin(v*6.283*3+u*4))[...,None]
    return np.clip(img,0,1)

def navy_tex(W=256,H=256,seed=5,col=(0.09,0.13,0.52),edge=(0.30,0.55,0.90)):
    """濃紺のフリル布: 縁(v=1側)に水色の細線、白い星の粒。"""
    img=np.zeros((H,W,4),np.float32); img[...,3]=1
    yy=np.mgrid[0:H,0:W][0].astype(np.float32)/H
    img[...,:3]=np.array(col,np.float32)*(0.8+0.35*yy[...,None])
    e=_smooth(yy,0.93,0.985)[...,None]; img[...,:3]=img[...,:3]*(1-e*0.8)+np.array(edge,np.float32)*e*0.8
    stars(img,34,seed,0.8,1.8,0.95)
    return img

def skirt_tex(W=512,H=512,seed=9):
    """星空の紫青のスカート地。v=1(上)が濃い紺紫、v=0(裾)が明るいラベンダー。星と十字のきらめき。"""
    img=np.zeros((H,W,4),np.float32); img[...,3]=1
    v=(np.mgrid[0:H,0:W][0].astype(np.float32)/H)[...,None]
    top=np.array([0.16,0.13,0.50],np.float32); mid=np.array([0.32,0.26,0.72],np.float32); low=np.array([0.62,0.52,0.90],np.float32)
    g=np.where(v>0.5,top*(v-0.5)*2+mid*(1-(v-0.5)*2),mid*(v*2)+low*(1-v*2))
    img[...,:3]=g
    stars(img,150,seed,0.8,2.0,0.9,cross=0.0)
    stars(img,16,seed+2,1.6,2.8,1.0,cross=0.9)
    return img

def solid_tex(col,W=16,H=16):
    img=np.ones((H,W,4),np.float32); img[...,:3]=np.array(col,np.float32); return img
