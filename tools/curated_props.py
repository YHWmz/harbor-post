"""Import verified CC0 props, normalize metres, simplify scans and remap all surfaces to paper palette.
Executed within the town builder, before district construction.
"""
curated_templates={};curated_usage={};curated_audit={}
for asset,path,budget in [('gazebo',P/'source-assets/quaternius/gazebo.glb',1400),('horse_statue',P/'source-assets/polyhaven/horse_statue_01/horse_statue_01_1k.gltf',1800),('garden_bench',P/'source-assets/polyhaven/painted_wooden_bench/painted_wooden_bench_1k.gltf',800)]:
 before=set(scene.objects);bpy.ops.import_scene.gltf(filepath=str(path));imported=set(scene.objects)-before;bpy.context.view_layer.update()
 objects=[o for o in imported if o.type=='MESH'];original=0
 for o in objects:o.data.calc_loop_triangles();original+=len(o.data.loop_triangles)
 for o in objects:
  if original>budget:
   if o.data.shape_keys:o.shape_key_clear()
   bpy.context.view_layer.objects.active=o;modifier=o.modifiers.new('PaperSilhouetteBudget','DECIMATE');modifier.ratio=budget/original;bpy.ops.object.modifier_apply(modifier=modifier.name)
 vertices=[o.matrix_world@v.co for o in objects for v in o.data.vertices]
 minimum=Vector(tuple(min(v[k] for v in vertices) for k in range(3)));maximum=Vector(tuple(max(v[k] for v in vertices) for k in range(3)));span=max(maximum-minimum);cx=(minimum.x+maximum.x)/2;cy=(minimum.y+maximum.y)/2
 parts=[]
 for o in objects:
  o.data.calc_loop_triangles()
  for tri in o.data.loop_triangles:
   points=[o.matrix_world@o.data.vertices[vi].co for vi in tri.vertices]
   avg=sum(v.z for v in points)/3
   mat='Stone' if asset=='horse_statue' else 'Wood' if asset=='garden_bench' else 'Slate' if avg>minimum.z+(maximum.z-minimum.z)*.65 else 'Stone' if avg<minimum.z+(maximum.z-minimum.z)*.12 else 'Wood'
   parts.append((tuple(((v.x-cx)/span,(v.z-minimum.z)/span,-(v.y-cy)/span) for v in points),mat))
 curated_templates[asset]=parts;curated_audit[asset]=dict(original_triangles=original,optimized_triangles=len(parts),paper_materials=sorted({m for _,m in parts}))
 for o in imported:bpy.data.objects.remove(o,do_unlink=True)
def curated_asset(asset,x,z,size=1,rotation=0,y=.4):
 global rigid
 old=rigid;wx,wz=river(x,z);rigid=(x,z,rotation,wx,wz,heading(x,z,rotation))
 for vertices,mat in curated_templates[asset]:
  add([(x+size*(math.cos(rotation)*a+math.sin(rotation)*c),y+size*b,z+size*(-math.sin(rotation)*a+math.cos(rotation)*c)) for a,b,c in vertices],[(0,1,2)],mat)
 rigid=old;curated_usage[asset]=curated_usage.get(asset,0)+1
