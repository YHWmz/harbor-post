"""Northern mountain backdrop; deliberately no mountain ring across the southern sea."""
import bpy,math,random,sys,json
from mathutils import Vector
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from alpine_terrain import PEAKS,PROFILE,MIN_X,MAX_X,MIN_Z,SHORE_Z,river,terrain_height,center_x,channel_width,snowline
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.name='Northern_Alpine_Watercolor_Backdrop';rng=random.Random(91)
materials=[]
for name,color in [('FarMountain','b3b8b2'),('Snow','e6e4d7'),('Mountain','94a59b'),('MountainShade','889a92'),('Foothill','9ca987'),('AlpineRock','9ba99d'),('AlpineMeadow','96a180')]:
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
   if layer==2 and -42<(-205+(i+.5)*7.4)<118:continue
   k=band*n+i;fs.extend([(k,k+1,k+n),(k+1,k+n+1,k+n)]);ids.extend([1 if layer==0 and band in [1,2] else mat,1 if layer==0 and band in [1,2] else (3 if layer==1 and i%3==0 else mat)])
 me=bpy.data.meshes.new('GEO_NorthernRidge_'+str(layer));me.from_pydata(vs,[],fs);me.update()
 for m in materials:me.materials.append(m)
 for p,mid in zip(me.polygons,ids):p.material_index=mid
 o=bpy.data.objects.new('SM_NorthernRidge_'+str(layer),me);scene.collection.objects.link(o)
# Three connected near mountains touch the northern lake shore.
# Adaptive cross-sections include the exact stream banks and floor at every row.
vs=[];fs=[];ids=[];columns=45
zs=sorted(set([MIN_Z+i*2 for i in range(int((SHORE_Z-MIN_Z)/2)+1)]+[p['z'] for p in PROFILE if p['z']<=SHORE_Z]));rows=len(zs)
for row,z in enumerate(zs):
 cx=center_x(z);w=channel_width(z)
 left=cx-w-4.2;right=cx+w+4.2
 xs=[MIN_X+(left-MIN_X)*i/18 for i in range(18)]+[left,cx-w-2,cx-w,cx-w*.6,cx,cx+w*.6,cx+w,cx+w+2,right]+[right+(MAX_X-right)*i/18 for i in range(1,19)]
 assert len(xs)==columns
 for x in xs:
  y=terrain_height(x,z);wx,wz=river(x,z);vs.append((wx,-wz,y))
for row in range(rows-1):
 for i in range(columns-1):
  k=row*columns+i
  for face in [(k,k+columns,k+1),(k+1,k+columns,k+columns+1)]:
   fs.append(face);v=[vs[n] for n in face];y=sum(p[2] for p in v)/3;x=sum(p[0] for p in v)/3
   # Use source coordinates for the snowline and expose the glacier-cut stream banks.
   bz=(zs[row]+zs[row+1])/2;near_channel=18<=i<=25 and bz>=-144
   mid=1 if y>snowline(x,bz) and not near_channel else 5 if y>8 else 6
   ids.append(mid)
me=bpy.data.meshes.new('GEO_LakesideAlps');me.from_pydata(vs,[],fs);me.update()
for m in materials:me.materials.append(m)
for p,mid in zip(me.polygons,ids):p.material_index=mid
obj=bpy.data.objects.new('SM_LakesideAlps',me);scene.collection.objects.link(obj)
# Normals and welds are validated before the same mesh is sent to the game.
import bmesh
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
triangles=0
for o in scene.objects:
 if o.type!='MESH':continue
 o.data.calc_loop_triangles();triangles+=len(o.data.loop_triangles)
 assert all(math.isfinite(c) for v in o.data.vertices for c in v.co)
assert triangles<15000,triangles
metadata=dict(triangles=triangles,source='shared alpine_terrain.py heightfield',peaks=[dict(name=p['name'],x=river(p['x'],p['z'])[0],z=river(p['x'],p['z'])[1],y=terrain_height(p['x'],p['z'])) for p in PEAKS],shore_z=SHORE_Z,stream_source_height=PROFILE[0]['y'])
(P/'dist/assets/alpine-terrain.json').write_text(json.dumps(metadata,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'blender/painted-hills.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'dist/assets/painted-hills.glb'),export_format='GLB',export_animations=False)
print('ALPINE_AUDIT',metadata)
