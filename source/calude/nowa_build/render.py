# usage: blender -b file.blend -P render.py -- out_prefix [views] [zoom_target]
import bpy,sys,math
from mathutils import Vector
a=sys.argv[sys.argv.index("--")+1:]
out=a[0]; views=(a[1] if len(a)>1 else "front").split(","); zoom=a[2] if len(a)>2 else "full"
sc=bpy.context.scene
for o in list(bpy.data.objects):
    if o.name in("Icosphere",) : o.hide_render=True
    if o.type in("CAMERA","LIGHT"): bpy.data.objects.remove(o)
sc.render.engine="BLENDER_EEVEE"; sc.eevee.taa_render_samples=16
sc.render.resolution_x,sc.render.resolution_y=(700,1000) if zoom=="full" else (800,800)
sc.render.film_transparent=False
w=sc.world or bpy.data.worlds.new("W"); sc.world=w; w.use_nodes=True
w.node_tree.nodes["Background"].inputs[0].default_value=(0.35,0.35,0.38,1); w.node_tree.nodes["Background"].inputs[1].default_value=0.6
sc.view_settings.view_transform="AgX"; sc.view_settings.look="AgX - Medium High Contrast"
H=max((o.matrix_world@Vector(c)).z for o in sc.objects if o.type=="MESH" and not o.hide_render for c in o.bound_box)
if zoom=="full": tgt=Vector((0,0,H/2)); dist=H*1.9; lens=50
elif zoom=="face": tgt=Vector((0,0,H-0.12)); dist=0.9; lens=85
elif zoom.startswith("c:"):
    x,z,dist=map(float,zoom[2:].split("/")); tgt=Vector((x,0,z)); lens=85
else: tgt=Vector((0,0,H*0.62)); dist=1.6; lens=60
cam=bpy.data.objects.new("Cam",bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera=cam; cam.data.lens=lens
def light(n,e,loc):
    l=bpy.data.objects.new(n,bpy.data.lights.new(n,"AREA")); l.data.energy=e; l.data.size=2; l.location=loc
    l.rotation_euler=(Vector((0,0,H*0.6))-Vector(loc)).to_track_quat('-Z','Y').to_euler(); sc.collection.objects.link(l)
light("K",60,(1.5,-2.5,H*1.3)); light("F",20,(-2,-2,H*0.8)); light("R",30,(0,2.5,H*1.4))
ang={"front":0,"side":90,"back":180,"q":35,"lside":-90}
for v in views:
    t=math.radians(ang[v]); cam.location=tgt+Vector((dist*math.sin(t),-dist*math.cos(t),0))
    cam.rotation_euler=(tgt-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f"{out}_{v}.png"; bpy.ops.render.render(write_still=True)
