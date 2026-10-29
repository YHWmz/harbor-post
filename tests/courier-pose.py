"""Run with Blender -b blender/courier.blend --python tests/courier-pose.py."""
import bpy,math
from mathutils import Vector
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(arm.data.bones)>=60
for o in meshes:
 assert any(m.type=='ARMATURE' for m in o.modifiers),o.name
 for v in o.data.vertices:assert .97<sum(g.weight for g in v.groups)<1.03,(o.name,v.index)
feet=next(o for o in meshes if o.name=='SM_Courier_Feet');cap=next(o for o in meshes if o.name=='SM_Courier_Details_Cap');reference=None
for name in ['Idle','Walk','Run']:
 action=bpy.data.actions[name];arm.animation_data.action=action;arm.animation_data.action_slot=action.slots[0];floors=[];hands=[]
 for k in range(13):
  bpy.context.scene.frame_set(int(action.frame_range.x+(action.frame_range.y-action.frame_range.x)*k/12));bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
  obj=feet.evaluated_get(deps);positions=[obj.matrix_world@v.co for v in obj.data.vertices];floors.append(min(p.z for p in positions));assert all(math.isfinite(c) for p in positions for c in p)
  obj=cap.evaluated_get(deps);centroid=sum((obj.matrix_world@v.co for v in obj.data.vertices),Vector())/len(obj.data.vertices)
  bone_world=arm.matrix_world@arm.pose.bones['Head'].matrix;local=bone_world.inverted()@centroid
  if reference is None:reference=local
  assert (reference-local).length<.02,'cap detaches from animated head'
  hand=arm.matrix_world@arm.pose.bones['Wrist.L'].head;hands.append(tuple(hand))
 assert min(floors)>-.08,(name,'foot penetrates floor',min(floors))
 assert max(floors)<.30,(name,'floating',max(floors))
 if name!='Idle':assert max(math.dist(hands[0],h) for h in hands)>.1,'arm has no actual gait motion'
 print('PASS',name,'deformation, cap binding, normalized weights, foot range',round(min(floors),3),round(max(floors),3),flush=True)
