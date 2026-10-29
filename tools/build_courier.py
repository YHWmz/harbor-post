"""Adapt Quaternius CC0 skinned character into the Harbor Post courier.
Standalone: Blender -b --python tools/build_courier.py. No network required.
"""
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];A=P/'dist/assets';SOURCE=P/'source-assets/quaternius/casual-character.glb'
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.name='PaperCourier_Source';scene.unit_settings.system='METRIC';scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
arm=next(o for o in scene.objects if o.type=='ARMATURE');arm.name='ARM_PaperCourier'
# A display sphere in the source upload is not part of the character.
for o in list(scene.objects):
 if o.type=='MESH' and not any(m.type=='ARMATURE' for m in o.modifiers):bpy.data.objects.remove(o,do_unlink=True)
arm.animation_data_clear();arm.data.pose_position='REST';bpy.context.view_layer.update()
base_meshes=[o for o in scene.objects if o.type=='MESH'];source_tris=sum(len(o.data.loop_triangles) if o.data.loop_triangles else sum(len(p.vertices)-2 for p in o.data.polygons) for o in base_meshes)
col=bpy.data.collections.new('COL_Courier');scene.collection.children.link(col)
for o in list(scene.objects):
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o)
colors={'Uniform':'#81968a','Trousers':'#536a70','Leather':'#80694f','Sole':'#4e574d','Linen':'#ded2b8','Skin':'#c9b698','SkinShadow':'#af9b82','Hair':'#5c5141','Ink':'#39433c','Brass':'#b49a62','Cap':'#596e70','Seam':'#b4b39b'}
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
mats={}
for name,h in colors.items():
 rgb=tuple(linear(int(h[i:i+2],16)/255) for i in (1,3,5));m=bpy.data.materials.new('MAT_Courier_'+name);m.use_nodes=True;bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(*rgb,1);bs.inputs['Roughness'].default_value=.90;bs.inputs['Specular IOR Level'].default_value=.12;bs.inputs['Emission Color'].default_value=(*rgb,1);bs.inputs['Emission Strength'].default_value=.12;m.diffuse_color=(*rgb,1);mats[name]=m
mapping={'White':'Sole','Red_Dark':'Leather','LightBrown':'Uniform','Skin':'Skin','Skin_Darker':'SkinShadow','Eyebrows':'Hair','Eye':'Ink','Hair':'Hair','LightBlue':'Trousers'}
for o in base_meshes:
 o.name='SM_Courier_'+o.name.removeprefix('Casual2_')
 old_names=[m.name for m in o.data.materials]
 for i,n in enumerate(old_names):o.data.materials[i]=mats[mapping[n]]
 # Extend the source short sleeve onto its already-weighted forearm surface.
 if 'Body' in o.name:
  sleeve=o.data.materials.find(mats['Uniform'].name)
  wrist_limit=abs((arm.matrix_world@arm.data.bones['Wrist.L'].head_local).x)-.055
  arm_groups={g.index for g in o.vertex_groups if g.name.startswith(('UpperArm.','LowerArm.','Shoulder.'))}
  hand_groups={g.index for g in o.vertex_groups if g.name.startswith(('Wrist.','Index','Middle','Ring','Pinky','Thumb'))}
  skin_index=o.data.materials.find(mats['Skin'].name)
  for f in o.data.polygons:
   arm_weight=sum(sum(g.weight for g in o.data.vertices[i].groups if g.group in arm_groups) for i in f.vertices)/len(f.vertices)
   if old_names[f.material_index]=='Skin' and arm_weight>.55 and abs((o.matrix_world@f.center).x)<wrist_limit:f.material_index=sleeve
   hand_weight=sum(sum(g.weight for g in o.data.vertices[i].groups if g.group in hand_groups) for i in f.vertices)/len(f.vertices)
   if hand_weight>.12:f.material_index=skin_index
 for f in o.data.polygons:f.use_smooth=True
# Original skin weights and animation joints stay intact.
accessories=[]
def bind(o,bone='Chest'):
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.name='SM_Courier_'+o.name;world=o.matrix_world.copy();o.parent=arm;o.matrix_world=world
 vg=o.vertex_groups.new(name=bone);vg.add(list(range(len(o.data.vertices))),1,'REPLACE');mod=o.modifiers.new('CourierSkin','ARMATURE');mod.object=arm;accessories.append(o);return o
def mesh(name,verts,faces,mat,bone='Chest'):
 me=bpy.data.meshes.new('GEO_'+name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);scene.collection.objects.link(o);me.materials.append(mats[mat]);return bind(o,bone)
def rounded(name,loc,size,mat,bone='Chest',bevel=.015):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 mod=o.modifiers.new('Soft cloth edges','BEVEL');mod.width=bevel;mod.segments=3;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 o.data.materials.append(mats[mat]);return bind(o,bone)
def ball(name,loc,size,mat,bone='Head',segments=16,rings=8):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for f in o.data.polygons:f.use_smooth=True
 o.data.materials.append(mats[mat]);return bind(o,bone)
def line(name,points,r,mat,bone='Chest',sides=4):
 verts=[];faces=[]
 for i,p in enumerate(points):
  tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)]);tangent.normalize();u=tangent.cross(Vector((0,1,0)))
  if u.length<.01:u=tangent.cross(Vector((1,0,0)))
  u.normalize();v=tangent.cross(u)
  verts.extend(tuple(Vector(p)+r*(math.cos(j*math.tau/sides)*u+math.sin(j*math.tau/sides)*v)) for j in range(sides))
 for i in range(len(points)-1):
  for j in range(sides):faces.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
 return mesh(name,verts,faces,mat,bone)
# Project seams and buttons onto the source shirt surface, instead of floating in front.
body=next(o for o in base_meshes if 'Body' in o.name);body.data.calc_loop_triangles();vs=[body.matrix_world@v.co for v in body.data.vertices];bvh=BVHTree.FromPolygons(vs,[tuple(t.vertices) for t in body.data.loop_triangles],all_triangles=True)
def front(x,z):
 hit=bvh.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2);return hit[0].y-.006 if hit[0] is not None else -.18
# Shaped linen shirt collar, brass buttons, front placket and stitched pocket.
for sign in [-1,1]:
 mesh('Collar_'+str(sign),[(sign*.035,front(sign*.035,1.51)-.01,1.51),(sign*.12,front(sign*.12,1.49)-.012,1.49),(sign*.072,front(sign*.072,1.405)-.012,1.405)],[(0,1,2)],'Linen')
for x in [-.012,.012]:line('Placket',[(x,front(x,z)-.006,z) for z in [1.09,1.18,1.27,1.36,1.43]],.003,'Seam')
for z in [1.12,1.23,1.34,1.43]:ball('UniformButton',(0,front(0,z)-.011,z),(.009,.004,.009),'Brass','Chest',8,4)
for sign in [-1,1]:
 x=sign*.115;mesh('Pocket_'+str(sign),[(x-.04,front(x-.04,1.30)-.009,1.30),(x+.04,front(x+.04,1.30)-.009,1.30),(x+.035,front(x+.035,1.24)-.009,1.24),(x-.035,front(x-.035,1.24)-.009,1.24)],[(0,1,2,3)],'Uniform')
 line('PocketStitch',[(x-.04,front(x-.04,1.30)-.013,1.30),(x+.04,front(x+.04,1.30)-.013,1.30)],.002,'Seam')
# Flexible wrist cuffs follow forearm bones and leave all original fingers articulated.
for sign,side in [(1,'L'),(-1,'R')]:
 pos=arm.matrix_world@arm.data.bones['Wrist.'+side].head_local;cx=pos.x-sign*.032
 verts=[]
 for dx in [-.027,.027]:
  for k in range(12):
   a=k*math.tau/12;verts.append((cx+dx,pos.y+.047*math.cos(a),pos.z+.044*math.sin(a)))
 mesh('Cuff_'+side,verts,[(k,(k+1)%12,(k+1)%12+12,k+12) for k in range(12)],'Linen','LowerArm.'+side)
# The cap has an actual cloth crown, band, curved visor and a small envelope badge.
ball('CapCrown',(0,.015,1.835),(.126,.165,.087),'Cap')
verts=[]
for y,z,rx in [(-.12,1.807,.112),(-.22,1.794,.106),(-.285,1.782,.065)]:
 for k in range(9):
  a=-math.pi/2+k*math.pi/8;verts.append((rx*math.sin(a),y+.02*math.cos(a),z+.015*math.cos(a)))
visor=mesh('CapVisor',verts,[(j*9+i,j*9+i+1,(j+1)*9+i+1,(j+1)*9+i) for j in range(2) for i in range(8)],'Cap','Head');sol=visor.modifiers.new('Visor thickness','SOLIDIFY');sol.thickness=.009;bpy.context.view_layer.objects.active=visor;bpy.ops.object.modifier_apply(modifier=sol.name)
line('CapBand',[(.122*math.cos(k*math.tau/32),.015+.162*math.sin(k*math.tau/32),1.808) for k in range(33)],.009,'Trousers','Head',5)
rounded('CapBadge',(0,-.153,1.845),(.043,.008,.029),'Brass','Head',.006)
line('BadgeEnvelope',[(-.015,-.159,1.852),(0,-.16,1.839),(.015,-.159,1.852)],.0018,'Linen','Head')
# Rounded leather satchel, hinged flap, visible letters, piping, buckle and stitch marks.
rounded('SatchelBody',(.305,.045,1.015),(.225,.15,.24),'Leather','Hips',.025)
rounded('SatchelFlap',(.305,-.038,1.075),(.23,.028,.14),'Leather','Hips',.018)
rounded('BagStrapTab',(.305,-.058,.995),(.035,.012,.09),'Leather','Hips',.006)
rounded('BagBuckle',(.305,-.069,1.003),(.047,.014,.038),'Brass','Hips',.007)
rounded('BuckleCenter',(.305,-.079,1.003),(.026,.007,.018),'Leather','Hips',.003)
for k in range(3):
 o=rounded('Letter_'+str(k),(.274+k*.021,.036,1.151+k*.008),(.135,.012,.075),'Linen','Hips',.004);o.rotation_euler.y=(k-1)*.10
line('BagPiping',[(.21,-.041,1.10),(.21,-.041,.935),(.40,-.041,.935),(.40,-.041,1.10)],.0035,'Seam','Hips')
for k in range(11):
 x=.217+k*.017;line('FlapStitch',[(x,-.055,1.025),(x+.006,-.055,1.025)],.0015,'Linen','Hips',3)
strap=[]
for k in range(18):
 t=k/17;x=-.14+.40*t;z=1.46-.38*t;strap.append((x,front(x,z)-.018,z))
# A flat leather ribbon with centre stitching and blended chest/hip weights.
verts=[]
for x,y,z in strap:verts.extend([(x-.014,y,z),(x+.014,y,z)])
o=mesh('ShoulderStrap',verts,[(2*k,2*k+1,2*k+3,2*k+2) for k in range(len(strap)-1)],'Leather');vg=o.vertex_groups.get('Chest');vg.remove(list(range(len(o.data.vertices))));hip=o.vertex_groups.new(name='Hips')
for k,v in enumerate(o.data.vertices):
 weight=max(0,min(1,(v.co.z-1.05)/.38));vg.add([k],weight,'REPLACE');hip.add([k],1-weight,'REPLACE')
line('StrapSeam',[(x,y-.003,z) for x,y,z in strap],.0018,'Seam')
# A matching rear ribbon and shoulder loop make the satchel visibly supported in back views.
back=[]
for k in range(18):
 t=k/17;x=-.14+.40*t;z=1.46-.38*t;hit=bvh.ray_cast(Vector((x,1,z)),Vector((0,-1,0)),2);y=hit[0].y+.012 if hit[0] is not None else .09;back.append((x,y,z))
verts=[]
for x,y,z in back:verts.extend([(x-.014,y,z),(x+.014,y,z)])
o=mesh('RearShoulderStrap',verts,[(2*k+2,2*k+3,2*k+1,2*k) for k in range(len(back)-1)],'Leather');ch=o.vertex_groups.get('Chest');ch.remove(list(range(len(o.data.vertices))));hg=o.vertex_groups.new(name='Hips')
for k,v in enumerate(o.data.vertices):
 weight=max(0,min(1,(v.co.z-1.05)/.38));ch.add([k],weight,'REPLACE');hg.add([k],1-weight,'REPLACE')
line('ShoulderLoop',[(-.14,front(-.14,1.46)-.018,1.46),(-.14,-.01,1.505),back[0]],.012,'Leather')
# Merge small accessories by shared material; preserve skin weights in each material batch.
accessory_parts=len(accessories);merged=[];groups={m.name:[] for m in mats.values()}
for o in accessories:groups[o.data.materials[0].name].append(o)
for material in mats.values():
 group=groups[material.name]
 if not group:continue
 bpy.ops.object.select_all(action='DESELECT')
 for o in group:o.select_set(True)
 bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join();o=group[0];o.name='SM_Courier_Details_'+material.name.removeprefix('MAT_Courier_');merged.append(o)
accessories=merged
# Keep only locomotion clips; actual source weights and joint curves are preserved.
selected={}
for action in list(bpy.data.actions):
 suffix=action.name.split('|')[-1]
 if suffix in ['Idle_Neutral','Walk','Run']:
  action.name={'Idle_Neutral':'Idle','Walk':'Walk','Run':'Run'}[suffix];selected[action.name]=action;action.use_fake_user=True
 else:bpy.data.actions.remove(action)
assert len(selected)==3
arm.data.pose_position='POSE';arm.animation_data_create();arm.animation_data.action=selected['Idle'];arm.animation_data.action_slot=selected['Idle'].slots[0];scene.frame_set(0)
# One floor-centred normalization root preserves original skeleton and animation space.
arm.data.pose_position='REST';bpy.context.view_layer.update()
root=bpy.data.objects.new('Courier',None);col.objects.link(root)
for o in list(scene.objects):
 if o!=root and o.parent is None:o.parent=root
points=[o.matrix_world@v.co for o in base_meshes+accessories for v in o.data.vertices];lo=min(v.z for v in points);hi=max(v.z for v in points);scale=1.74/(hi-lo);root.scale=(scale,)*3;root.location.z=-lo*scale
arm.data.pose_position='POSE';scene.frame_set(0);bpy.context.view_layer.update()
# Production gate: bounded meshes, finite coordinates, weighted attachments and original rig.
tris=0
for o in base_meshes+accessories:
 o.data.calc_loop_triangles();tris+=len(o.data.loop_triangles);assert all(math.isfinite(c) for v in o.data.vertices for c in v.co)
 assert any(m.type=='ARMATURE' for m in o.modifiers),o.name
assert 4000<tris<10000,tris
# Export only the courier hierarchy. No camera/lights; retain three sampled actions.
bpy.ops.object.select_all(action='SELECT')
opts=dict(filepath=str(A/'walker.glb'),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False,export_animations=True,export_force_sampling=True,export_animation_mode='ACTIONS',export_nla_strips=False)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'blender/courier.blend'));bpy.ops.export_scene.gltf(**opts)
# Audit the actual GLB output, including animation and normalized bounds.
blob=(A/'walker.glb').read_bytes();import struct
j=json.loads(blob[20:20+struct.unpack_from('<I',blob,12)[0]]);exported=sum(j['accessors'][p['indices']]['count']//3 for m in j['meshes'] for p in m['primitives']);clips=[a['name'] for a in j.get('animations',[])];assert sorted(clips)==['Idle','Run','Walk'],clips
report=dict(source='Quaternius Casual Character',source_url='https://poly.pizza/m/kZ3DmIoGip',download_url='https://static.poly.pizza/90a9e2d4-053f-42f1-99a2-8f5e1180ea7f.glb',license='CC0-1.0',sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),base_triangles=source_tris,triangles=exported,bones=len(arm.data.bones),animations=clips,height=1.74,accessory_meshes=len(accessories),paper_materials=len(mats),native_accessories=['cloth cap and curved visor','collar and cuff bands','uniform buttons and seams','rounded leather satchel, letters and buckle'])
(A/'courier-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));(P/'source-assets/quaternius/CHARACTER-SOURCE.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
if (A/'walking-audit.json').exists():
 audit=json.loads((A/'walking-audit.json').read_text());audit['courier_triangles']=exported;audit['courier_source']='courier.blend';(A/'walking-audit.json').write_text(json.dumps(audit,indent=2))
print('PASS paper courier',exported,'triangles',clips,len(arm.data.bones),'bones',flush=True)
