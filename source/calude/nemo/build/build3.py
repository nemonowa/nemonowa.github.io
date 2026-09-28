import bpy, sys, math
from mathutils import Vector
S=sys.argv[sys.argv.index("--")+1]
bpy.ops.preferences.addon_enable(module="mmd_tools")
sc=bpy.context.scene
arm=bpy.data.objects["Armature"]; wear=bpy.data.objects["wear"]

# ---------- 1. 義手のプロシージャル模様を画像へベイク(PMXでも見えるように) ----------
pro=bpy.data.materials["prosthetic"]; nt=pro.node_tree; N=nt.nodes; L=nt.links
img=bpy.data.images.new("prosthetic",1024,1024)
p=N["Principled BSDF"]; mr=[n for n in N if n.type=="MAP_RANGE"][0]
mix=N.new("ShaderNodeMix"); mix.data_type="RGBA"; mix.inputs[6].default_value=(0.025,0.025,0.03,1); mix.inputs[7].default_value=(1,0.04,0.03,1)
L.new(mr.outputs["Result"],mix.inputs[0])
em=N.new("ShaderNodeEmission"); L.new(mix.outputs[2],em.inputs[0])
out=N["Material Output"]; orig=out.inputs["Surface"].links[0].from_socket
L.new(em.outputs[0],out.inputs["Surface"])
tn=N.new("ShaderNodeTexImage"); tn.image=img; N.active=tn
for m in wear.data.materials:   # 他マテリアルはベイク対象外に
    if m and m!=pro and m.use_nodes:
        t=m.node_tree.nodes.new("ShaderNodeTexImage"); t.name="_bk"; t.image=bpy.data.images.new("_dummy",8,8); m.node_tree.nodes.active=t
sc.render.engine="CYCLES"; sc.cycles.samples=4; sc.cycles.device="CPU"
bpy.ops.object.select_all(action="DESELECT"); wear.select_set(True); bpy.context.view_layer.objects.active=wear
bpy.ops.object.bake(type="EMIT",margin=4)
img.pack()
for m in wear.data.materials:
    if m and m!=pro and m.use_nodes and "_bk" in m.node_tree.nodes: m.node_tree.nodes.remove(m.node_tree.nodes["_bk"])
# 義手マテリアルを画像ベースに作り直す
for n in list(N):
    if n not in (p,out,tn): N.remove(n)
L.new(tn.outputs["Color"],p.inputs["Base Color"]); L.new(p.outputs[0],out.inputs["Surface"])
sep=N.new("ShaderNodeSeparateColor"); L.new(tn.outputs["Color"],sep.inputs[0])
L.new(sep.outputs[0],p.inputs["Emission Strength"]); p.inputs["Emission Color"].default_value=(1,0.03,0.02,1)
print("baked prosthetic")

# ---------- 2. ボーン再構成(MMD標準・nowaと同じ命名) ----------
J={"lower_body":"下半身","upper_body":"上半身","upper_body2":"上半身2","neck":"首","head":"頭","root":"全ての親","center":"センター","groove":"グルーブ"}
REN={"hips":"lower_body","spine":"upper_body","chest":"upper_body2","neck":"neck","head 1":"head"}
FING={"thumb":("thumb","親指",0),"f_index":("fore","人指",1),"f_middle":("middle","中指",1),"f_ring":("third","薬指",1),"f_pinky":("little","小指",1)}
ZEN="０１２３４５６７８９"
for s,js in (("L","左"),("R","右")):
    for a,b,j in (("shoulder","shoulder","肩"),("upper_arm","arm","腕"),("forearm","elbow","ひじ"),("forearm.twist","wrist_twist","手捩"),("hand","wrist","手首"),
                  ("thigh","leg","足"),("shin","knee","ひざ"),("foot","ankle","足首"),("toe","toe_ex","足先EX"),("heel","heel","かかと")):
        REN[f"{a}.{s}"]=f"{b}_{s}"; J[f"{b}_{s}"]=js+j
    for k,(e,j,base) in FING.items():
        for i in (1,2,3):
            REN[f"{k}.0{i}.{s}"]=f"{e}{i-1+base}_{s}"; J[f"{e}{i-1+base}_{s}"]=js+j+ZEN[i-1+base]
    for i in (1,2,3,4): REN[f"palm.0{i}.{s}"]=f"palm{i}_{s}"; J[f"palm{i}_{s}"]=f"{js}手掌{i}"
    J[f"legIK_{s}"]=js+"足ＩＫ"; J[f"toeIK_{s}"]=js+"つま先ＩＫ"; J[f"toe_{s}"]=js+"つま先"
for b in arm.data.bones:
    if b.name.startswith("hair"): J[b.name.replace(".","_")]="髪"+b.name[4:].replace("_","").replace(".00","")
    if b.name.startswith("foot_rope"): J[b.name.replace(".","_")]=("左" if "_L" in b.name else "右")+"足紐"+("2" if ".001" in b.name else "1")
for b in arm.data.bones:
    if b.name.startswith(("hair","foot_rope")): b.name=b.name.replace(".","_")
bpy.context.view_layer.objects.active=arm; bpy.ops.object.mode_set(mode="EDIT")
E=arm.data.edit_bones
for o,n in REN.items():
    if o in E: E[o].name=n
def nb(name,h,t,parent):
    b=E.new(name); b.head=h; b.tail=t; b.parent=E[parent] if parent else None; return b
nb("root",(0,0,0),(0,0,0.1),None)
nb("center",(0,0,0.70),(0,0,0.0),"root")
nb("groove",(0,0,0.72),(0,0,0.82),"center")
E["lower_body"].parent=E["groove"]; E["upper_body"].parent=E["groove"]
lb=E["lower_body"]; lb.tail=lb.head+Vector((0,0,-0.10))
for s in "LR":
    leg,knee,ank,tex=E[f"leg_{s}"],E[f"knee_{s}"],E[f"ankle_{s}"],E[f"toe_ex_{s}"]
    leg.tail=knee.head; knee.tail=ank.head; ank.tail=tex.head
    for b in (leg,knee): b.align_roll(Vector((0,1,0)))
    tip=nb(f"toe_{s}",tex.head.copy(),tex.head+Vector((0,0,-0.03)),f"ankle_{s}")
    ik=nb(f"legIK_{s}",ank.head.copy(),ank.head+Vector((0,0.05,0)),"root")
    nb(f"toeIK_{s}",tex.head.copy(),tex.head+Vector((0,0,-0.08)),f"legIK_{s}")
    E[f"arm_{s}"].tail=E[f"elbow_{s}"].head
    E[f"elbow_{s}"].tail=E[f"wrist_twist_{s}"].head
bpy.ops.object.mode_set(mode="POSE")
P=arm.pose.bones
for s in "LR":
    c=P[f"knee_{s}"].constraints.new("IK"); c.target=arm; c.subtarget=f"legIK_{s}"; c.chain_count=2; c.iterations=40
    k=P[f"knee_{s}"]; k.lock_ik_y=k.lock_ik_z=True; k.use_ik_limit_x=True; k.ik_min_x=math.radians(0.5); k.ik_max_x=math.radians(180)
    c=P[f"ankle_{s}"].constraints.new("IK"); c.target=arm; c.subtarget=f"toeIK_{s}"; c.chain_count=1; c.iterations=3
bpy.ops.object.mode_set(mode="OBJECT")
arm.name="nemo_arm"

# ---------- 3. 表情モーフ(シェイプキー)を日本語標準名へ ----------
MOR={"eye_close":("まばたき","blink","EYE"),"blink_L":("ウィンク","wink","EYE"),"blink_R":("ウィンク右","wink_R","EYE"),
     "eye_smile":("笑い","smile_eyes","EYE"),"eye_open":("びっくり","surprised","EYE"),"eye_small":("瞳小","small_pupil","EYE"),
     "eye_no_hilight":("ハイライト消","highlight_hide","EYE"),"eye_zitome":("じと目","jito","EYE"),"eye_angry":("怒り目","angry_eyes","EYE"),
     "eye_brow_up":("上","up","EYEBROW"),"eye_brow_down":("下","down","EYEBROW"),
     "lip_a":("あ","a","MOUTH"),"lip_i":("い","i","MOUTH"),"lip_u":("う","u","MOUTH"),"lip_e":("え","e","MOUTH"),"lip_o":("お","o","MOUTH"),
     "lip_w":("ω","omega","MOUTH"),"mouse_open":("口開け","mouth_open","MOUTH"),"lip_up":("にやり","grin","MOUTH"),
     "face_happy":("にこり","happy","OTHER"),"face_angry":("怒り","anger","OTHER"),"face_sad":("困る","sad","OTHER"),"face_surprise":("驚き","surprise","OTHER"),
     "cheek":("照れ","blush","OTHER"),"serious":("真顔","serious","OTHER"),"smirk_wink":("ニヤリウィンク","smirk_wink","OTHER")}
head=bpy.data.objects["head"]; kbs=head.data.shape_keys.key_blocks
for o,(j,e,c) in MOR.items():
    if o in kbs: kbs[o].name=j
# ---------- 4. mmd_toolsのMMDモデルへ変換 ----------
bpy.ops.object.select_all(action="DESELECT"); arm.select_set(True); bpy.context.view_layer.objects.active=arm
# 単色マテリアルの色を控えておく(convert後のmmd_material.diffuse_colorに反映させる)
BASE={}
for o in (wear,head,bpy.data.objects["hair"]):
    for m in o.data.materials:
        pn=m.node_tree.nodes.get("Principled BSDF") if m and m.use_nodes else None
        if pn and not pn.inputs["Base Color"].is_linked: BASE[m.name]=tuple(pn.inputs["Base Color"].default_value)[:3]
# mmd_tools v4.0.0はBlender 4.0で削除されたpose.bone_groupsを参照して落ちるため無効化(表示枠は後で自前設定)
from mmd_tools.operators.display_item import DisplayItemQuickSetup as DIQ
DIQ.load_bone_groups=staticmethod(lambda mmd_root,armature:None)
bpy.ops.mmd_tools.convert_to_mmd_model(scale=0.08,convert_material_nodes=True)
root=arm.parent; root.name="nemo"; root.mmd_root.name="ネモ"; root.mmd_root.name_e="Nemo"
root.mmd_root.comment_text=None if False else root.mmd_root.comment_text
for pb in arm.pose.bones:
    pb.mmd_bone.name_j=J.get(pb.name,pb.name); pb.mmd_bone.name_e=pb.name
vm=root.mmd_root.vertex_morphs
vm.clear()
inv={j:(e,c) for o,(j,e,c) in MOR.items()}
for kb in kbs[1:]:
    e,c=inv.get(kb.name,(kb.name,"OTHER" if not kb.name.startswith(("eye","look")) else "EYE"))
    if kb.name.startswith(("lip","mouth")): c="MOUTH"
    it=vm.add(); it.name=kb.name; it.name_e=e; it.category=c
for o in (wear,head,bpy.data.objects["hair"]):
    for m in o.data.materials:
        mm=m.mmd_material
        if m.name in BASE:
            mm.diffuse_color=BASE[m.name]; mm.ambient_color=[c*0.5 for c in BASE[m.name]]
        mm.specular_color=(0.08,0.08,0.08); mm.shininess=8 if m.name not in("gold","prosthetic","wear_metal") else 40
DIQ.load_facial_items(root.mmd_root)
FR=[("センター",["center","groove"]),("体(上)",["upper_body","upper_body2","neck","head"]),
    ("腕",[f"{b}_{s}" for s in "LR" for b in ("shoulder","arm","elbow","wrist_twist","wrist")]),
    ("指",[b.name for b in arm.data.bones if b.name.startswith(("thumb","fore","middle","third","little"))]),
    ("体(下)",["lower_body"]),("足",[f"{b}_{s}" for s in "LR" for b in ("leg","knee","ankle","toe_ex","legIK","toeIK")]),
    ("髪",[b.name for b in arm.data.bones if b.name.startswith("hair")])]
frames=root.mmd_root.display_item_frames
for name,bones in FR:
    f=frames.add(); f.name=name; f.name_e=name
    for bn in bones:
        it=f.data.add(); it.type="BONE"; it.name=bn
wear.name="nemo_body"; head.name="nemo_face"; bpy.data.objects["hair"].name="nemo_hair"
sc.render.engine="BLENDER_EEVEE"
# PMX書き出し時にテクスチャをコピーできるよう、使用画像を実ファイル化しておく
import os
os.makedirs(S+"/tex_out",exist_ok=True)
for im in bpy.data.images:
    if im.users==0 or im.name.startswith("_dummy") or im.source!="FILE" and im.name not in("prosthetic","vest"): continue
    fn=S+"/tex_out/"+im.name.replace(" ","_")+".png"
    im.filepath_raw=fn; im.file_format="PNG"; im.save(); im.filepath=fn
bpy.ops.wm.save_as_mainfile(filepath=S+"/nemo_s3.blend")
print("DONE3",root.name,len(arm.data.bones),"bones",len(vm),"morphs",[o.name for o in root.children])
