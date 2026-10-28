"""Native Blender horse and mail coach, kept separate from the town for runtime travel."""
import bpy,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
mats={}
for name,color in dict(Wood='87715b',Ink='3e4b41',Chestnut='92715a',Mane='514a3d',Cream='e6dcc3',Sage='8b9d8c',Rose='b68c70',Glass='6c8884',Gold='cbb679').items():
 m=bpy.data.materials.new('MAT_Coach_'+name);m.use_nodes=True;n=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');c=[int(color[i:i+2],16)/255 for i in (0,2,4)];c=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c];n.inputs['Base Color'].default_value=(*c,1);n.inputs['Roughness'].default_value=1;n.inputs['Emission Color'].default_value=(*c,1);n.inputs['Emission Strength'].default_value=.2 if name!='Gold' else .7;mats[name]=m
root=bpy.data.objects.new('CliffCarriage',None);bpy.context.scene.collection.objects.link(root)
def loc(p):return (p[0],-p[2],p[1])
def finish(o,name,mat,parent=root):
 o.name=name;o.data.materials.append(mats[mat]);bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=parent;o.matrix_world=world;return o
def box(name,p,s,mat,parent=root):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc(p));o=bpy.context.object;o.scale=(s[0],s[2],s[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,mat,parent)
def ball(name,p,s,mat,parent=root):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,location=loc(p));o=bpy.context.object;o.scale=(s[0],s[2],s[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,mat,parent)
def rod(name,a,b,r,mat,parent=root,verts=8):
 a=Vector(loc(a));b=Vector(loc(b));bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=(b-a).length,location=(a+b)/2);o=bpy.context.object;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return finish(o,name,mat,parent)
def group(name,p):
 o=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(o);o.parent=root;o.location=loc(p);bpy.context.view_layer.update();return o
ball('HorseBody',(0,1.23,1.0),(.40,.45,.83),'Chestnut')
neck=ball('HorseNeck',(0,1.61,1.65),(.28,.58,.31),'Chestnut');neck.rotation_euler.x=math.radians(-18)
ball('HorseHead',(0,1.99,1.95),(.22,.25,.39),'Chestnut');ball('HorseMuzzle',(0,1.88,2.22),(.20,.16,.24),'Mane')
for side in [-1,1]:
 ball('HorseEar',(side*.12,2.30,1.82),(.055,.18,.075),'Chestnut');ball('HorseEye',(side*.211,2.04,2.05),(.032,.038,.035),'Ink')
rod('HorseMane',(0,1.45,1.36),(0,2.05,1.54),.10,'Mane');rod('HorseTail',(0,1.4,.30),(0,.68,.06),.075,'Mane')
for i,(x,z) in enumerate([(-.27,.51),(.27,.51),(-.27,1.50),(.27,1.50)]):
 leg=group('HorseLeg'+str(i),(x,1.02,z));rod('LegUpper',(x,1.03,z),(x,.56,z+.03),.085,'Chestnut',leg);rod('LegLower',(x,.56,z+.03),(x,.13,z+.08),.060,'Chestnut',leg);box('Hoof',(x,.10,z+.11),(.18,.17,.26),'Ink',leg)
for z in [.50,1.4]:rod('LeatherHarness',(-.42,1.32,z),(.42,1.32,z),.045,'Ink')
for x in [-.52,.52]:
 rod('Shaft',(x,.80,-.85),(x,.91,1.35),.048,'Wood');rod('Rein',(x*.4,1.62,-.22),(x*.42,1.91,2.12),.014,'Ink')
box('CoachFloor',(0,.67,-1.65),(1.65,.20,2.25),'Wood');box('CoachBody',(0,1.14,-1.71),(1.52,.88,1.83),'Sage')
box('CoachRoof',(0,1.94,-1.71),(1.82,.20,2.03),'Cream');box('CoachRoofLip',(0,2.07,-1.71),(1.64,.10,1.91),'Wood')
for side in [-1,1]:
 for z in [-2.2,-1.35]:box('CoachWindow',(side*.773,1.48,z),(.035,.48,.57),'Glass')
 box('CoachDoorTrim',(side*.79,1.05,-1.7),(.04,.52,1.65),'Cream')
 box('CoachMailSeal',(side*.82,1.04,-1.7),(.03,.30,.40),'Rose')
 for z in [-2.45,-.87]:rod('CoachPillar',(side*.73,.80,z),(side*.73,1.90,z),.036,'Wood')
for z in [-2.33,-1.0]:
 rod('Axle',(-1,.52,z),(1,.52,z),.065,'Ink')
 for side in [-1,1]:
  x=side*.95;wheel=group('CartWheel'+str(z)+str(side),(x,.52,z));rod('WheelTire',(x-.06,.52,z),(x+.06,.52,z),.48,'Ink',wheel,16);rod('WheelRim',(x-.075,.52,z),(x+.075,.52,z),.40,'Wood',wheel,16)
  for k in range(8):
   a=k*math.tau/8;rod('WheelSpoke',(x+side*.09,.52,z),(x+side*.09,.52+math.cos(a)*.40,z+math.sin(a)*.40),.025,'Cream',wheel)
  rod('WheelHub',(x-.13,.52,z),(x+.13,.52,z),.10,'Ink',wheel)
box('DriverSeat',(0,1.03,-.48),(1.35,.22,.54),'Wood');box('DriverTorso',(0,1.48,-.46),(.42,.53,.28),'Rose');ball('DriverHead',(0,1.96,-.44),(.19,.23,.18),'Cream');box('DriverHat',(0,2.17,-.44),(.46,.09,.4),'Ink')
for side in [-1,1]:rod('DriverArm',(side*.23,1.69,-.43),(side*.28,1.43,-.05),.06,'Rose')
for x in [-.63,.63]:
 box('RearLantern',(x,1.47,-2.69),(.16,.25,.16),'Gold');rod('LanternHook',(x,1.68,-2.65),(x,1.76,-2.65),.028,'Ink')
box('MailTrunk',(0,1.76,-1.72),(.70,.16,.55),'Wood')
bpy.context.view_layer.update()
# Batch by material within each rigid part, preserving wheel and leg pivots.
parents=[root]+[o for o in bpy.context.scene.objects if o.type=='EMPTY' and o!=root]
for parent in parents:
 by_mat={}
 for o in list(parent.children):
  if o.type=='MESH':by_mat.setdefault(o.data.materials[0].name,[]).append(o)
 for key,objects in by_mat.items():
  if len(objects)<2:continue
  bpy.ops.object.select_all(action='DESELECT')
  for o in objects:o.select_set(True)
  bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();objects[0].name='CoachBatch_'+parent.name+'_'+key
triangles=0
for o in bpy.context.scene.objects:
 if o.type=='MESH':o.data.calc_loop_triangles();triangles+=len(o.data.loop_triangles)
assert triangles<12000
bpy.ops.wm.save_as_mainfile(filepath=str(P/'blender/cliff-carriage.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'dist/assets/cliff-carriage.glb'),export_format='GLB',export_animations=False)
print('CARRIAGE_AUDIT',triangles,'triangles; four leg pivots and four wheel pivots')
