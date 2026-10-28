"""Northern mountain backdrop; deliberately no mountain ring across the southern sea."""
import bpy,math,random
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.name='Northern_Alpine_Watercolor_Backdrop';rng=random.Random(91)
materials=[]
for name,color in [('FarMountain','b3b8b2'),('Snow','e6e4d7'),('Mountain','94a59b'),('MountainShade','889a92'),('Foothill','9ca987')]:
 m=bpy.data.materials.new('MAT_Paper_'+name);m.use_nodes=True;bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');c=[int(color[i:i+2],16)/255 for i in (0,2,4)];c=[v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in c];bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=1;bs.inputs['Emission Color'].default_value=(*c,1);bs.inputs['Emission Strength'].default_value=.4;materials.append(m)
# Irregular peaks have snow-lines below their summits, with a ragged snow/rock seam.
for layer,(zbase,height,mat) in enumerate([(-205,43,0),(-139,24,2),(-99,9,4)]):
 vs=[];fs=[];ids=[];n=57
 for band in range(4):
  for i in range(n):
   x=-205+i*7.4;h=height*(.22+sum(a*math.exp(-((x-c)/w)**2) for c,w,a in [(-110+layer*13,33,.70),(-25-layer*5,26,.82),(65+layer*10,43,.72),(148,31,.54)])+.025*math.sin(i*2.1+layer))
   yy=[-.5,h*.57+rng.uniform(-.8,.8),h,1][band];z=[zbase+23,zbase+5,zbase,zbase-32][band]+math.sin(i*.8)*4
   vs.append((x,-z,yy))
 for band in range(3):
  for i in range(n-1):
   k=band*n+i;fs.extend([(k,k+1,k+n),(k+1,k+n+1,k+n)]);ids.extend([1 if layer==0 and band in [1,2] else mat,1 if layer==0 and band in [1,2] else (3 if layer==1 and i%3==0 else mat)])
 me=bpy.data.meshes.new('GEO_NorthernRidge_'+str(layer));me.from_pydata(vs,[],fs);me.update()
 for m in materials:me.materials.append(m)
 for p,mid in zip(me.polygons,ids):p.material_index=mid
 o=bpy.data.objects.new('SM_NorthernRidge_'+str(layer),me);scene.collection.objects.link(o)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'blender/painted-hills.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'dist/assets/painted-hills.glb'),export_format='GLB',export_animations=False)
print('Northern mountains: 1008 triangles, 3 ridges with distant snowcaps; southern horizon open')
