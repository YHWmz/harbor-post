"""Native footbridges, articulated paper courier, and collision-aware multilayer walk graph.
Run with Blender -b --python tools/build_walking.py after the town build.
"""
import bpy, math, json, sys, time
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import tessellate_polygon
P=Path(__file__).resolve().parents[1]; A=P/'dist/assets'
nav=json.loads((A/'town-navigation.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(P/'blender/european-water-town.blend'))
scene=bpy.context.scene
col=bpy.data.collections.new('COL_Walking');scene.collection.children.link(col)
materials={m.name.removeprefix('MAT_Paper_'):m for m in bpy.data.materials if m.name.startswith('MAT_Paper_')}
buckets={};surfaces=[];bridges=[]
def river(x,z):return (x+math.tanh(x*.2)*max(0,z-32)*.25*math.exp(-abs(x)/45)+6.5*math.sin(z*.07)+2*math.sin(z*.16+.6)+2.2*math.sin(x*.17+z*.065),z+4.5*math.sin(x*.07+1)+2*math.sin(x*.145-z*.045)+1.2*math.sin(z*.14))
def add(v,f,m):
 b=buckets.setdefault(m,[[],[]]);n=len(b[0]);b[0].extend((x,-z,y) for x,y,z in v);b[1].extend(tuple(n+i for i in face) for face in f)
def beam(a,b,width,mat='Wood'):
 a,b=Vector(a),Vector(b);d=b-a;n=d.cross(Vector((0,1,0))).normalized()*width/2;u=d.normalized().cross(n).normalized()*width/2
 vs=[tuple(p+n*s+u*t) for p in (a,b) for s,t in [(-1,-1),(1,-1),(1,1),(-1,1)]]
 add(vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
def polygon(x,z,poly):
 inside=False
 for i,(a,c) in enumerate(poly):
  b,d=poly[i-1]
  if (c>z)!=(d>z) and x<(b-a)*(z-c)/(d-c)+a:inside=not inside
 return inside
def nearestbank(p,land):
 for i,b in land:
  if polygon(p[0],p[1],b['polygon']):return i
 return min(land,key=lambda ib:min(math.dist(p,q) for q in ib[1]['polygon']))[0]
land=[(i,b) for i,b in enumerate(nav['banks']) if i<20]
parent={i:i for i,b in land}
def root(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
def join(i,j):parent[root(i)]=root(j)
# Land overlaps and existing bridges already form part of the road network.
for i,b in land:
 for j,c in land:
  if j<=i:continue
  if any(polygon(x,z,c['polygon']) for x,z in b['polygon'][::3]) or any(polygon(x,z,b['polygon']) for x,z in c['polygon'][::3]):join(i,j)
# Reuse actual stone bridge geometry. Approach aprons close their 65cm end riser.
for x,z,axis,half in [(0,-12,'x',8),(28,12,'x',6),(-28,-12,'x',6),(-14,-25,'z',6)]:
 pts=[]
 for k in range(49):
  d=-(half+2)+2*(half+2)*k/48
  y=1.085+3*(1-(d/half)**2) if abs(d)<=half else .40+.685*(half+2-abs(d))/2
  xx,zz=(x+d,z) if axis=='x' else (x,z+d);wx,wz=river(xx,zz);pts.append(dict(x=wx,z=wz,y=y))
  if k:
   a,b=pts[-2:];surfaces.append(dict(a=a,b=b,width=1.65,kind='stone_bridge'))
   if abs(d)>half-.7 or abs(-(half+2)+2*(half+2)*(k-1)/48)>half:
    dx=b['x']-a['x'];dz=b['z']-a['z'];l=math.hypot(dx,dz);nx,nz=-dz/l*.88,dx/l*.88
    add([(a['x']+nx,a['y']-.03,a['z']+nz),(a['x']-nx,a['y']-.03,a['z']-nz),(b['x']-nx,b['y']-.03,b['z']-nz),(b['x']+nx,b['y']-.03,b['z']+nz)],[(3,2,1,0)],'Path')
 join(nearestbank((pts[0]['x'],pts[0]['z']),land),nearestbank((pts[-1]['x'],pts[-1]['z']),land))
 bridges.append(dict(name='原石拱桥',existing=True,points=pts))
# Minimum spanning connections across the closest banks, never across the open lake/sea.
edges=[]
for i,b in land:
 for j,c in land:
  if j<=i:continue
  best=(1e9,None,None)
  for p in b['polygon'][::2]:
   for q in c['polygon'][::2]:
    d=math.dist(p,q)
    if d<best[0]:best=(d,p,q)
  edges.append((*best,i,j))
for gap,p,q,i,j in sorted(edges):
 if root(i)==root(j):continue
 assert gap<18,('unexpected long crossing',gap,i,j)
 if {i,j}=={2,3}:p,q=river(-78,19),river(-78,31)
 if {i,j}=={7,10}:p,q=river(8,-33),river(-8,-33);j=4
 dx,dz=q[0]-p[0],q[1]-p[1];ll=math.hypot(dx,dz);dx/=ll;dz/=ll
 a=(p[0]-dx*2,p[1]-dz*2);b=(q[0]+dx*2,q[1]+dz*2);length=ll+4;nx,nz=-dz*1.12,dx*1.12;pts=[]
 count=max(16,math.ceil(length/.8))
 for k in range(count+1):
  t=k/count;x=a[0]+(b[0]-a[0])*t;z=a[1]+(b[1]-a[1])*t;y=.40+3.15*math.sin(math.pi*t)**1.15;pts.append(dict(x=x,y=y,z=z))
  if k:
   aa,bb=pts[-2:];surfaces.append(dict(a=aa,b=bb,width=2.0,kind='footbridge'))
   add([(aa['x']+nx,aa['y'],aa['z']+nz),(aa['x']-nx,aa['y'],aa['z']-nz),(bb['x']-nx,bb['y'],bb['z']-nz),(bb['x']+nx,bb['y'],bb['z']+nz)],[(3,2,1,0)],'Path')
   for side in [-1,1]:
    pa=(aa['x']+nx*side,aa['y'],aa['z']+nz*side);pb=(bb['x']+nx*side,bb['y'],bb['z']+nz*side)
    beam(pa,pb,.14,'Stone');beam((pa[0],pa[1]+.85,pa[2]),(pb[0],pb[1]+.85,pb[2]),.065)
  if k%4==0:
   for side in [-1,1]:beam((x+nx*side,y,z+nz*side),(x+nx*side,y+.90,z+nz*side),.085)
 bridges.append(dict(name='步行桥 '+str(len(bridges)-3),existing=False,banks=[i,j],points=pts));join(i,j)
for bx,bz,axis,span in [(15,-25,'z',7),(60,25,'z',7),(28,47,'x',7)]:
 p=river(bx-span if axis=='x' else bx,bz-span if axis=='z' else bz);q=river(bx+span if axis=='x' else bx,bz+span if axis=='z' else bz);i=nearestbank(p,land);j=nearestbank(q,land)
 dx,dz=q[0]-p[0],q[1]-p[1];ll=math.hypot(dx,dz);dx/=ll;dz/=ll
 a=(p[0]-dx*2,p[1]-dz*2);b=(q[0]+dx*2,q[1]+dz*2);length=ll+4;nx,nz=-dz*1.12,dx*1.12;pts=[]
 count=max(16,math.ceil(length/.8))
 for k in range(count+1):
  t=k/count;x=a[0]+(b[0]-a[0])*t;z=a[1]+(b[1]-a[1])*t;y=.40+3.15*math.sin(math.pi*t)**1.15;pts.append(dict(x=x,y=y,z=z))
  if k:
   aa,bb=pts[-2:];surfaces.append(dict(a=aa,b=bb,width=2.0,kind='footbridge'))
   add([(aa['x']+nx,aa['y'],aa['z']+nz),(aa['x']-nx,aa['y'],aa['z']-nz),(bb['x']-nx,bb['y'],bb['z']-nz),(bb['x']+nx,bb['y'],bb['z']+nz)],[(3,2,1,0)],'Path')
   for side in [-1,1]:
    pa=(aa['x']+nx*side,aa['y'],aa['z']+nz*side);pb=(bb['x']+nx*side,bb['y'],bb['z']+nz*side)
    beam(pa,pb,.14,'Stone');beam((pa[0],pa[1]+.85,pa[2]),(pb[0],pb[1]+.85,pb[2]),.065)
  if k%4==0:
   for side in [-1,1]:beam((x+nx*side,y,z+nz*side),(x+nx*side,y+.90,z+nz*side),.085)
 bridges.append(dict(name='步行桥 '+str(len(bridges)-3),existing=False,banks=[i,j],points=pts));join(i,j)
assert len({root(i) for i,b in land})==1
# Native shared-material geometry. Retain source town unchanged in its own .blend.
bridge_objects=[]
for mat,(verts,faces) in buckets.items():
 me=bpy.data.meshes.new('GEO_Walking_'+mat);me.from_pydata(verts,[],faces);me.update();me.materials.append(materials[mat]);o=bpy.data.objects.new('SM_Walking_'+mat,me);col.objects.link(o);bridge_objects.append(o)
# Build a BVH from original architecture and new bridges. This provides real walls,
# hedges and furniture collision, rather than allowing the courier through buildings.
verts=[];faces=[];face_names=[]
for o in scene.objects:
 if o.type!='MESH' or o.name=='SM_Water_SourcePreview' or o.name.startswith('SM_HarborBoat'):continue
 o.data.calc_loop_triangles();offset=len(verts);verts.extend(o.matrix_world@v.co for v in o.data.vertices);faces.extend(tuple(offset+i for i in t.vertices) for t in o.data.loop_triangles);face_names.extend([o.name]*len(o.data.loop_triangles))
bvh=BVHTree.FromPolygons(verts,faces,all_triangles=True);print('Collision BVH ready',len(faces),flush=True)
# Spatial buckets keep sampling O(1); geometry/collision and foot heights are co-exported.
step=.45;minx=-117;minz=-120;nx=510;nz=410
sgrid={}
def put(surface):
 a,b=surface['a'],surface['b'];w=surface['width']/2+.5
 for gz in range(math.floor((min(a['z'],b['z'])-w-minz)/step),math.ceil((max(a['z'],b['z'])+w-minz)/step)+1):
  for gx in range(math.floor((min(a['x'],b['x'])-w-minx)/step),math.ceil((max(a['x'],b['x'])+w-minx)/step)+1):sgrid.setdefault((gx,gz),[]).append(surface)
for s in surfaces:put(s)
for a,b in zip(nav['carriage']['route'],nav['carriage']['route'][1:]):put(dict(a=a,b=b,width=3.0,kind='hill_road'))
cliff=next(b for b in nav['banks'] if b.get('name')=='NorthwestCliff')
# Docks are sampled as land too, but never moored boats, rocks or waterfall blockers.
lands=[b for i,b in land]+[cliff]+nav['docks']
nodes=[];node_by_cell={}
for iz in range(nz):
 z=minz+iz*step
 for ix in range(nx):
  x=minx+ix*step;heights=[]
  for b in lands:
   if not(b['minX']<=x<=b['maxX'] and b['minZ']<=z<=b['maxZ']):continue
   if polygon(x,z,b['polygon']):heights.append(18.39 if b.get('name')=='NorthwestCliff' else .40)
  # No fictitious ground under the cliff wall.
  if 18.39 in heights:heights=[h for h in heights if h>18]
  for s in sgrid.get((ix,iz),[]):
   a,b=s['a'],s['b'];dx=b['x']-a['x'];dz=b['z']-a['z'];t=max(0,min(1,((x-a['x'])*dx+(z-a['z'])*dz)/(dx*dx+dz*dz or 1)))
   if math.hypot(x-a['x']-t*dx,z-a['z']-t*dz)<s['width']/2:heights.append(a['y']+t*(b['y']-a['y'])+.025)
  for y in sorted(set(round(h,2) for h in heights)):
   if any(abs(y-nodes[n][1]/100)<.22 for n in node_by_cell.get(ix+iz*nx,[])):continue
   # Capsule occupancy samples protect walls, railings, vegetation and low props.
   if any((hit:=bvh.find_nearest(Vector((x,-z,y+h)),.28))[0] is not None for h in [.75,1.15,1.50]):continue
   cell=ix+iz*nx;node_by_cell.setdefault(cell,[]).append(len(nodes));nodes.append([cell,round(y*100)])
print('Walk nodes',len(nodes),'bridges',len(bridges),flush=True)
# Flood the actual collision graph, not just the authored bridge-bank topology.
def neighbors(n):
 cell,y=nodes[n];ix=cell%nx;iz=cell//nx
 for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
  xx,zz=ix+dx,iz+dz
  if not(0<=xx<nx and 0<=zz<nz):continue
  for k in node_by_cell.get(xx+zz*nx,[]):
   if abs(nodes[k][1]-y)<=65:yield k
seen=set();components=[]
for i in range(len(nodes)):
 if i in seen:continue
 todo=[i];seen.add(i);comp=[]
 while todo:
  n=todo.pop();comp.append(n)
  for k in neighbors(n):
   if k not in seen:seen.add(k);todo.append(k)
 components.append(comp)
components.sort(key=len,reverse=True);main=set(components[0]);print('Walk components',[len(c) for c in components[:20]],flush=True)
def pos(n):
 c,y=nodes[n];return (minx+c%nx*step,y/100,minz+c//nx*step)
coverage=[]
for i,b in land:
 eligible=[n for n in main if b['minX']<=pos(n)[0]<=b['maxX'] and b['minZ']<=pos(n)[2]<=b['maxZ'] and polygon(pos(n)[0],pos(n)[2],b['polygon'])];coverage.append(dict(bank=i,nodes=len(eligible)));assert eligible,('disconnected land',i)
# Only reachable cells are shipped: walled building interiors and prop pockets are not walking areas.
reachable=[nodes[i] for i in sorted(main)]
assert any(pos(i)[1]>18 for i in main),'castle summit is not reachable on foot'
checkpoints=[]
for f in nav['district_features']:
 nearest=min(main,key=lambda n:(pos(n)[0]-f['x'])**2+(pos(n)[2]-f['z'])**2+((pos(n)[1]-f['ground'])*4)**2);x,y,z=pos(nearest);checkpoints.append(dict(name=f['name'],kind=f['kind'],x=x,y=y,z=z,offset=round(math.hypot(x-f['x'],z-f['z']),2)))
walknav=dict(version=1,source='walking-town.blend',step=step,minX=minx,minZ=minz,nx=nx,nz=nz,nodes=reachable,bridges=bridges,coverage=coverage,checkpoints=checkpoints,height_step=.65,radius=.25,connected=True)
(A/'walking-navigation.json').write_text(json.dumps(walknav,ensure_ascii=False,separators=(',',':')))
# Check finite geometry and shared palette before export.
tris=0
for o in bridge_objects:o.data.calc_loop_triangles();tris+=len(o.data.loop_triangles);assert all(math.isfinite(c) for v in o.data.vertices for c in v.co)
assert tris<16000,('walking geometry budget',tris)
bpy.ops.object.select_all(action='DESELECT')
for o in bridge_objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(A/'walking-town.glb'),export_format='GLB',use_selection=True,export_animations=False,export_cameras=False,export_lights=False)
# Lightweight articulated courier; pivots authored at hips/shoulders for runtime gait.
walker=bpy.data.objects.new('Courier',None);col.objects.link(walker);parts=[]
def part(name,loc,scale,mat,shape='cube',pivot=None):
 if shape=='sphere':bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,location=loc)
 else:bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
 o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(materials[mat]);
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o)
 if pivot:
  pivot=Vector(pivot);delta=o.location-pivot
  for v in o.data.vertices:v.co+=delta
  o.location=pivot
 o.parent=walker;parts.append(o);return o
# Blender Y=-gameZ; courier faces game+Z.
part('Coat',(0,0,1.0),(.48,.30,.61),'Sage');part('Collar',(0,-.04,1.33),(.31,.32,.10),'Cream')
part('Head',(0,0,1.51),(.18,.17,.20),'Plaster','sphere')
part('Cap',(0,0,1.68),(.23,.20,.07),'Slate','sphere');part('CapBrim',(0,-.15,1.64),(.39,.20,.045),'Slate')
for side,xx in [('Left',-.16),('Right',.16)]:
 part(side+'Leg',(xx,0,.39),(.17,.21,.66),'Slate',pivot=(xx,0,.73));shoe=part(side+'Shoe',(xx,-.05,.08),(.19,.32,.16),'Wood');leg=next(o for o in parts if o.name==side+'Leg');shoe.parent=leg;shoe.location-=leg.location
 part(side+'Arm',(xx*1.9,0,1.03),(.14,.18,.52),'Sage',pivot=(xx*1.9,0,1.28))
part('Mailbag',(.29,.03,.83),(.22,.36,.30),'Wood');part('SatchelFlap',(.29,-.16,.87),(.23,.04,.22),'Cream')
# Strap on front of coat, only a narrow painted band.
part('Strap',(0,-.16,1.03),(.055,.035,.65),'Wood').rotation_euler.y=-.48
for s in [-1,1]:part('Eye'+str(s),(s*.065,-.163,1.54),(.022,.025,.026),'Ink')
bpy.ops.object.select_all(action='DESELECT')
for o in [walker,*parts]:o.select_set(True)
walker_tris=0
for o in parts:o.data.calc_loop_triangles();walker_tris+=len(o.data.loop_triangles)
assert walker_tris<1200
bpy.ops.export_scene.gltf(filepath=str(A/'walker.glb'),export_format='GLB',use_selection=True,export_animations=False,export_cameras=False,export_lights=False)
# Source blend includes the original town for editable placement context.
bpy.ops.wm.save_as_mainfile(filepath=str(P/'blender/walking-town.blend'))
(A/'walking-audit.json').write_text(json.dumps(dict(bridges=len(bridges),new_bridges=sum(not b['existing'] for b in bridges),bridge_triangles=tris,courier_triangles=walker_tris,reachable_nodes=len(reachable),all_town_banks_connected=all(c['nodes'] for c in coverage),castle_walkable=True),indent=2))
print('PASS walking export',tris,walker_tris,'nodes',len(reachable),flush=True)
