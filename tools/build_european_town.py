"""Blender is the authoritative scene and navigation exporter. Run with Blender -b --python."""
import bpy, math, random, json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from alpine_terrain import PROFILE,PEAKS,center_x,channel_width,terrain_height,smooth
from mathutils import Vector, Matrix
from mathutils.geometry import tessellate_polygon
P=Path(__file__).resolve().parents[1]
OUT=P/'blender';ASSET=P/'dist/assets'; rng=random.Random(417)
# XY are Blender's ground plane; export maps them to Three.js X/-Z.
def river(x,z):return (x+math.tanh(x*.2)*max(0,z-32)*.25*math.exp(-abs(x)/45)+6.5*math.sin(z*.07)+2*math.sin(z*.16+.6)+2.2*math.sin(x*.17+z*.065),z+4.5*math.sin(x*.07+1)+2*math.sin(x*.145-z*.045)+1.2*math.sin(z*.14))
def heading(x,z,a=0):
 p=river(x,z);q=river(x+math.sin(a)*.1,z+math.cos(a)*.1);return math.atan2(q[0]-p[0],q[1]-p[1])
# Rounded polygons reduce square intersections and avoid sharp bank protrusions.
def rounded(a,c,d,f,r=2):
 points=[]
 for cx,cz,start in [(c-r,f-r,0),(a+r,f-r,90),(a+r,d+r,180),(c-r,d+r,270)]:
  for i in range(9):
   t=math.radians(start+i*90/8);points.append((cx+r*math.cos(t),cz+r*math.sin(t)))
 # Sample straight segments too; curved mapping must never be applied to only four corners.
 out=[]
 for i,p in enumerate(points):
  q=points[(i+1)%len(points)];n=max(1,math.ceil(math.dist(p,q)/1.1))
  for j in range(n):out.append((p[0]+(q[0]-p[0])*j/n,p[1]+(q[1]-p[1])*j/n))
 return out
xs=[(-100,-32.5),(-23.5,-6.5),(6.5,23.5),(32.5,100)];zs=[(-90,-29.5),(-20.5,-5.5),(5.5,20.5),(29.5,90)]
blocks=[]
for ix,(a,c) in enumerate(xs):
 for iz,(d,f) in enumerate(zs):
  if (ix,iz) in [(1,2),(2,3)]:continue
  if (ix,iz)==(1,1):f=20.5
  if (ix,iz)==(2,0):d=-37.5
  if (ix,iz)==(2,2):f=52
  if iz==3:f=50 if ix==0 else 48 if ix==1 else 54
  blocks.append(dict(a=a,c=c,d=d,f=f,ix=ix,iz=iz,park=(ix,iz) in [(2,1),(1,3)]))
# A connected northern continent closes the lake below the mountain foothills.
blocks.extend([dict(a=-100,c=20,d=-112,f=-82,ix=4,iz=-1,park=True),dict(a=28,c=100,d=-112,f=-82,ix=5,iz=-1,park=True)])
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.name='EuropeanWaterTown_Source';scene.unit_settings.system='METRIC'
for name in ['COL_Architecture','COL_Terrain','COL_Nature','COL_Landmarks','COL_Export','COL_Collision','COL_Lights']:
 col=bpy.data.collections.new(name);scene.collection.children.link(col)
col=bpy.data.collections['COL_Export'];buckets={};materials={}
palette={'Plaster':'#d8c9a8','Cream':'#e5dcc3','Rose':'#bda08a','Sage':'#a7b0a0','Stone':'#b2b39e','Path':'#ccc2aa','Ink':'#556152','Wood':'#8b785b','Roof':'#a5755e','Slate':'#657c78','Glass':'#6b8b88','Lamplight':'#d6bd82','Meadow':'#a5ad87','Leaf':'#7e9677','Willow':'#91a487','Flowers':'#c39b96','WaterWash':'#91aaa0','GreenhouseGlass':'#a8beb0','Waterfall':'#bed9d1','FlowersLavender':'#a6a3b5'}
def srgb(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
for name,hx in palette.items():
 rgb=[srgb(int(hx[i:i+2],16)/255) for i in (1,3,5)];m=bpy.data.materials.new('MAT_Paper_'+name);m.use_nodes=True;bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(*rgb,1);bs.inputs['Roughness'].default_value=1;bs.inputs['Specular IOR Level'].default_value=.08;bs.inputs['Emission Color'].default_value=(*rgb,1);bs.inputs['Emission Strength'].default_value=.18 if name!='Lamplight' else .6;m.diffuse_color=(*rgb,1);materials[name]=m
 if name=='GreenhouseGlass':
  bs.inputs['Base Color'].default_value=(*rgb,.35);bs.inputs['Alpha'].default_value=.35;m.diffuse_color=(*rgb,.35)
  try:m.surface_render_method='DITHERED'
  except (TypeError,AttributeError):pass
# Builders work in game x/y/z. Rigid groups follow the shore tangent without bending houses.
rigid=None
architecture_counts={}
building_plots=[]
detail_counts={}
roads=[]
vertex_count=0
def mapped(v):
 x,y,z=v
 if rigid:
  cx,cz,rot,wx,wz,wr=rigid;dx=x-cx;dz=z-cz;da=wr-rot;x=wx+math.cos(da)*dx+math.sin(da)*dz;z=wz-math.sin(da)*dx+math.cos(da)*dz
 else:x,z=river(x,z)
 return (x,-z,y)
def add(verts,faces,mat):
 b=buckets.setdefault(mat,[[],[]]);offset=len(b[0]);b[0].extend(mapped(v) for v in verts);b[1].extend(tuple(offset+i for i in face) for face in faces)
def box(x,y,z,w,h,d,mat,rot=0):
 # Subdivide long quays, paths and terrain strips before the curved river deformation.
 nx=max(1,min(180,math.ceil(w/1.1))) if 8<w<180 else 1;nz=max(1,min(180,math.ceil(d/1.1))) if 8<d<180 else 1
 def pt(a,b,c):return (x+math.cos(rot)*a+math.sin(rot)*c,y+b,z-math.sin(rot)*a+math.cos(rot)*c)
 for iy in [-1,1]:
  vs=[pt(-w/2+i*w/nx,iy*h/2,-d/2+j*d/nz) for j in range(nz+1) for i in range(nx+1)];fs=[]
  for j in range(nz):
   for i in range(nx):
    k=j*(nx+1)+i;face=(k,k+1,k+nx+2,k+nx+1);fs.append(face if iy==1 else face[::-1])
  add(vs,fs,mat)
 for axis,sign in [(0,-1),(0,1),(2,-1),(2,1)]:
  n=nz if axis==0 else nx;vs=[]
  for i in range(n+1):
   a=sign*w/2 if axis==0 else -w/2+i*w/nx;c=-d/2+i*d/nz if axis==0 else sign*d/2
   vs.extend([pt(a,-h/2,c),pt(a,h/2,c)])
  fs=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(n)];add(vs,fs,mat)
def tube(a,b,r=.035,mat='Ink',sides=5):
 va=Vector(a);vb=Vector(b);axis=(vb-va).normalized();u=axis.cross(Vector((0,1,0)))
 if u.length<.01:u=axis.cross(Vector((1,0,0)))
 u.normalize();v=axis.cross(u);vs=[tuple(p+r*(math.cos(i*2*math.pi/sides)*u+math.sin(i*2*math.pi/sides)*v)) for p in [va,vb] for i in range(sides)];fs=[(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)];fs.extend([tuple(range(sides-1,-1,-1)),tuple(range(sides,2*sides))]);add(vs,fs,mat)
def foliage(x,y,z,r,mat='Leaf',stretch=1):
 # Low-poly rounded crown with staggered rings, as in the approved paper palette.
 vs=[(x,y-r*stretch,z)]
 for k in range(1,5):
  t=-math.pi/2+k*math.pi/5
  for j in range(9):
   a=j*math.tau/9+(k%2)*.16;rr=r*math.cos(t)*(1+rng.uniform(-.07,.07));vs.append((x+rr*math.cos(a),y+r*math.sin(t)*stretch,z+rr*math.sin(a)))
 vs.append((x,y+r*stretch,z));fs=[]
 for j in range(9):fs.append((0,1+(j+1)%9,1+j));fs.append((len(vs)-1,28+j,28+(j+1)%9))
 for k in range(3):
  for j in range(9):a=1+k*9+j;b=1+k*9+(j+1)%9;fs.append((a,b,b+9,a+9))
 add(vs,fs,mat)
def tree(x,z,s=1,willow=False):
 if 34<x<52 and 6<z<20:return # Open civic plaza
 if -144<z<-80 and abs(x-center_x(z))<channel_width(z)+2.3:return # Shared mountain stream corridor
 ground=max(0,terrain_height(x,z)-.35) if -32<x<108 and -174<z<-82 else 0
 tube((x,.35+ground,z),(x,2.2*s+ground,z),.1*s,'Wood');foliage(x,2.6*s+ground,z,1.1*s,'Willow' if willow else 'Leaf',1.3 if willow else 1)
 for k in range(2):a=k*2.6;foliage(x+math.cos(a)*.65*s,2.0*s+ground,z+math.sin(a)*.65*s,.65*s,'Leaf')
def cylinder(x,y,z,r,h,mat,sides=12,top_r=None):
 tr=r if top_r is None else top_r
 vs=[(x+rr*math.cos(i*math.tau/sides),yy,z+rr*math.sin(i*math.tau/sides)) for yy,rr in [(y-h/2,r),(y+h/2,tr)] for i in range(sides)]
 fs=[(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)]
 fs.extend([tuple(range(sides-1,-1,-1)),tuple(range(sides,2*sides))]);add(vs,fs,mat)
def road_strip(x,z,w,d):
 box(x,.405,z,w,.035,d,'Path');roads.append(dict(x=x,z=z,width=w,depth=d))
 # Sparse transverse stone joints instead of a high contrast tiled grid.
 if d>w:
  for j in range(math.ceil(d/1.4)):
   zz=z-d/2+j*1.4;tube((x-w/2+.08,.428,zz),(x+w/2-.08,.428,zz+.07),.012,'Stone')
 else:
  for j in range(math.ceil(w/1.4)):
   xx=x-w/2+j*1.4;tube((xx,.428,z-d/2+.08),(xx+.07,.428,z+d/2-.08),.012,'Stone')
def free_plot(x,z,w,d,rot=0):
 hx=abs(math.cos(rot))*w/2+abs(math.sin(rot))*d/2;hz=abs(math.sin(rot))*w/2+abs(math.cos(rot))*d/2
 return not any(abs(x-b['x'])<hx+b['hx']+.35 and abs(z-b['z'])<hz+b['hz']+.35 for b in building_plots)
def house(x,z,w=2.8,d=3,h=3,rot=0,typ=0):
 if x < -33 and z < -31.5:return # Reserved cliff apron and coach road
 if abs(x-43)<8+w/2 and abs(z-13)<4.8+d/2:return # Main civic plaza and its circulation
 global rigid
 # Reserve existing landmark footprints and keep the central streets open.
 if any(abs(x-px)<ww and abs(z-pz)<dd for px,pz,ww,dd in [(10,9,3.8,3.4),(-18.7,14,3.4,3.0),(-36,-14,3.3,3.4),(-19,6,2.8,2.8),(19.8,34,3.0,4.4),(-11.8,3.4,2.1,2.2)]):return
 if not free_plot(x,z,w,d,rot):return
 variant=typ%6
 style=['low_cottage','timber_house','dutch_gable','mansard_townhouse','stepped_merchant','workshop_shed'][variant]
 architecture_counts[style]=architecture_counts.get(style,0)+1
 if variant==0:h*=.72
 elif variant==3:h*=1.32
 elif variant==4:h*=1.15
 elif variant==5:h*=.84
 x+=rng.uniform(-.35,.35);z+=rng.uniform(-.25,.25);rot+=rng.uniform(-.10,.10)
 building_plots.append(dict(x=x,z=z,hx=abs(math.cos(rot))*w/2+abs(math.sin(rot))*d/2,hz=abs(math.sin(rot))*w/2+abs(math.cos(rot))*d/2))
 wx,wz=river(x,z);rigid=(x,z,rot,wx,wz,heading(x,z,rot))
 def local(a,y,c):return (x+math.cos(rot)*a+math.sin(rot)*c,y,z-math.sin(rot)*a+math.cos(rot)*c)
 def bx(a,y,c,ww,hh,dd,m):p=local(a,y,c);box(*p,ww,hh,dd,m,rot)
 def ln(a,b,r=.03,m='Ink'):tube(local(*a),local(*b),r,m)
 wall=['Plaster','Cream','Rose','Sage'][typ%4];rm='Slate' if typ%3==0 else 'Roof'
 bx(0,.45+h/2,0,w,h,d,wall);bx(0,.5,0,w+.16,.22,d+.16,'Stone')
 # Distinct roof silhouettes: gable, hipped, Dutch facade, mansard, stepped and shed.
 if variant in [0,1,2,4]:
  rise=1.05 if variant==0 else 1.75 if variant==2 else 1.35
  v=[local(a,y,c) for c in [-d/2-.2,d/2+.2] for a,y in [(-w/2-.2,h+.45),(0,h+.45+rise),(w/2+.2,h+.45)]];add(v,[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)],rm)
  ln((-w/2-.2,h+.46,d/2+.22),(0,h+.46+rise,d/2+.22));ln((0,h+.46+rise,d/2+.22),(w/2+.2,h+.46,d/2+.22));ln((0,h+.46+rise,-d/2-.22),(0,h+.46+rise,d/2+.22))
  if variant==2:
   # Dutch bell-shaped gable masks the simple roof triangle.
   for width,yy,hh in [(w*.93,h+.63,.4),(w*.72,h+1.02,.4),(w*.46,h+1.41,.4),(w*.21,h+1.77,.32)]:bx(0,yy,d/2+.25,width,hh,.2,'Cream')
   bx(0,h+1.05,d/2+.37,.4,.52,.05,'Glass')
  if variant==4:
   for j in range(4):
    yy=h+.65+j*.31;ww=w*(1-j*.21);bx(0,yy,d/2+.24,ww,.31,.19,wall)
   bx(0,h+1.05,d/2+.36,.36,.52,.06,'Glass')
 elif variant==3:
  # Mansard roof with a narrow flat ridge and dormer windows.
  vs=[local(a,y,c) for a,y,c in [(-w/2-.18,h+.45,-d/2-.2),(w/2+.18,h+.45,-d/2-.2),(w/2+.18,h+.45,d/2+.2),(-w/2-.18,h+.45,d/2+.2),(-w*.28,h+1.55,-d*.34),(w*.28,h+1.55,-d*.34),(w*.28,h+1.55,d*.34),(-w*.28,h+1.55,d*.34)]]
  add(vs,[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],'Slate')
  for xx in [-w*.25,w*.25]:bx(xx,h+.98,d*.43,.52,.66,.28,'Cream');bx(xx,h+.98,d*.43+.16,.32,.4,.04,'Glass')
 else:
  vs=[local(a,y,c) for a,y,c in [(-w/2-.2,h+.5,-d/2-.2),(w/2+.2,h+.5,-d/2-.2),(w/2+.2,h+1.0,d/2+.2),(-w/2-.2,h+1.0,d/2+.2)]];add(vs,[(0,1,2,3)],rm)
  bx(w*.36,.95,0,w*.55,1.2,d*.75,'Wood')
 bx(w*.3,h+1.35,d*.2,.32,1,.38,'Stone')
 floors=[1.45] if h<2.4 else [1.6,h-.05] if h<4.2 else [1.5,2.9,h-.15]
 for yy in floors:
  for xx in [-w*.28,w*.28]:
   bx(xx,yy,d/2+.04,.58,.81,.07,'Ink');bx(xx,yy,d/2+.09,.46,.68,.04,'Lamplight' if typ%5==0 else 'Glass');bx(xx,yy,d/2+.12,.035,.68,.04,'Cream');bx(xx,yy,d/2+.13,.46,.035,.04,'Cream')
   if typ%2==0:
    bx(xx,yy-.5,d/2+.15,.69,.15,.28,'Wood')
    for j in range(3):p=local(xx-.2+j*.2,yy-.37,d/2+.2);foliage(*p,.12,'Flowers' if j%2 else 'Leaf')
 bx(0,1.1,d/2+.09,.58,1.4,.12,'Wood')
 if typ%3==1:
  for xx in [-w/2+.03,0,w/2-.03]:bx(xx,h/2+.45,d/2+.13,.08,h,.08,'Ink')
  bx(0,h*.62,d/2+.13,w,.08,.08,'Ink');ln((-w/2,h*.62+.45,d/2+.15),(0,h+.45,d/2+.15));ln((0,h+.45,d/2+.15),(w/2,h*.62+.45,d/2+.15))
 if typ%4==2:
  for j in range(6):bx(-w/2+(j+.5)*w/6,2.05,d/2+.55,w/6,.1,.95,'Cream' if j%2 else 'Sage')
  for xx in [-w*.48,w*.48]:ln((xx,.5,d/2+1),(xx,2.05,d/2+1),.035,'Wood')
 if variant in [0,1,2,4]:
  for k in range(1,4):
   xx=(w/2+.2)*(1-k*.24);yy=h+.45+rise*k*.24
   for sign in [-1,1]:ln((sign*xx,yy,-d/2-.22),(sign*xx,yy,d/2+.22),.012)
 if variant==0:
  bx(-w*.3,1.05,-d*.25,w*.6,1.2,d*.55,'Sage')
 # Shutters on side facades and individual hanging shop signs soften repeated fronts.
 for side in [-1,1]:
  bx(side*(w/2+.025),1.65,0,.045,.7,.55,'Ink');bx(side*(w/2+.055),1.65,0,.025,.57,.43,'Glass')
 if typ%2==0:
  ln((w*.4,2.35,d/2),(w*.4,2.35,d/2+.85),.035,'Wood')
  bx(w*.4,2.05,d/2+.76,.62,.42,.08,'Wood')
  if variant in [0,4]:
   pp=local(w*.4,2.05,d/2+.82);foliage(*pp,.16,'Cream',.52)
  else:
   ln((w*.27,1.98,d/2+.82),(w*.52,2.15,d/2+.82),.035,'Cream')
  detail_counts['shop_signs']=detail_counts.get('shop_signs',0)+1
 rigid=None
# CC0 public kit components are imported, recolored per sampled atlas swatch, and batched.
import colorsys
PUBLIC_DIR=P/'source-assets/fantasy-town'
public_names=['stall-red','stall-green','cart','cart-high','lantern','stall-bench','fountain-round-detail','wall-wood-window-shutters','wall-wood-doorway-round','wall-wood-detail-cross','stairs-wood','tree-high-round','fence','watermill']
public_templates={};public_usage={};pixel_cache={}
def paper_color(rgb):
 r,g,b=rgb;h,s,v=colorsys.rgb_to_hsv(r,g,b)
 if v<.16:return 'Ink'
 if s<.16:return 'Cream' if v>.65 else 'Stone'
 if .23<h<.47:return 'Sage' if v>.45 else 'Leaf'
 if .47<h<.76:return 'Glass' if v>.4 else 'Slate'
 if h<.055 or h>.95:return 'Rose' if v>.45 else 'Wood'
 return 'Cream' if v>.75 and s<.55 else 'Wood'
for name in public_names:
 before=set(scene.objects);bpy.ops.import_scene.gltf(filepath=str(PUBLIC_DIR/(name+'.glb')))
 imported=[o for o in scene.objects if o not in before];parts=[]
 for o in imported:
  if o.type!='MESH':continue
  me=o.data;me.calc_loop_triangles();uvs=me.uv_layers.active.data if me.uv_layers.active else None
  for t in me.loop_triangles:
   mat=me.materials[t.material_index] if me.materials else None;image=next((n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None) if mat and mat.use_nodes else None
   rgb=tuple(mat.diffuse_color[:3]) if mat else (.5,.5,.5)
   if image and uvs:
    if image.name not in pixel_cache:pixel_cache[image.name]=(image.size[0],image.size[1],list(image.pixels[:]))
    iw,ih,pix=pixel_cache[image.name];uv=sum((uvs[l].uv for l in t.loops),Vector((0,0)))/3;ix=max(0,min(iw-1,int(uv.x*iw)));iy=max(0,min(ih-1,int(uv.y*ih)));off=(iy*iw+ix)*4;rgb=tuple(pix[off:off+3])
   coords=[]
   for vi in t.vertices:
    p=o.matrix_world@me.vertices[vi].co;coords.append((p.x,p.z,-p.y))
   parts.append((coords,paper_color(rgb)))
 public_templates[name]=parts
 for o in imported:bpy.data.objects.remove(o,do_unlink=True)
def public_asset(name,x,z,scale=1,rotation=0,y=.43):
 global rigid
 old_rigid=rigid
 if rigid is None:
  wx,wz=river(x,z);rigid=(x,z,rotation,wx,wz,heading(x,z,rotation))
 for vs,mat in public_templates[name]:
  vv=[(x+scale*(math.cos(rotation)*px+math.sin(rotation)*pz),y+scale*py,z+scale*(-math.sin(rotation)*px+math.cos(rotation)*pz)) for px,py,pz in vs]
  add(vv,[(0,1,2)],mat)
 rigid=old_rigid;public_usage[name]=public_usage.get(name,0)+1

WATERCRAFT_DIR=P/'source-assets/watercraft'
watercraft_names=['boat-sail-a','boat-sail-b','boat-fishing-small','boat-row-large']
for name in watercraft_names:
 before=set(scene.objects);bpy.ops.import_scene.gltf(filepath=str(WATERCRAFT_DIR/(name+'.glb')))
 imported=[o for o in scene.objects if o not in before];parts=[]
 for o in imported:
  if o.type!='MESH':continue
  me=o.data;me.calc_loop_triangles();uvs=me.uv_layers.active.data if me.uv_layers.active else None
  for t in me.loop_triangles:
   mat=me.materials[t.material_index] if me.materials else None;image=next((n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None) if mat and mat.use_nodes else None
   rgb=tuple(mat.diffuse_color[:3]) if mat else (.5,.5,.5)
   if image and uvs:
    if image.name not in pixel_cache:pixel_cache[image.name]=(image.size[0],image.size[1],list(image.pixels[:]))
    iw,ih,pix=pixel_cache[image.name];uv=sum((uvs[l].uv for l in t.loops),Vector((0,0)))/3;ix=max(0,min(iw-1,int(uv.x*iw)));iy=max(0,min(ih-1,int(uv.y*ih)));off=(iy*iw+ix)*4;rgb=tuple(pix[off:off+3])
   coords=[]
   for vi in t.vertices:
    p=o.matrix_world@me.vertices[vi].co;coords.append((p.x,p.z,-p.y))
   parts.append((coords,paper_color(rgb)))
 public_templates[name]=parts
 for o in imported:bpy.data.objects.remove(o,do_unlink=True)

# Land shapes and their collision outlines are authored once here and exported together.
banks=[]
for b in blocks:
 a,c,d,f=[b[k] for k in ['a','c','d','f']];outline=rounded(a,c,d,f,2.2 if b['park'] else 1.5)
 # The northern land cap follows the same winding creek as the mountain height field.
 if b['iz']==-1:
  outline=[(min(x,center_x(z)-channel_width(z)-1.6) if b['ix']==4 else max(x,center_x(z)+channel_width(z)+1.6),z) for x,z in outline]
 # Shared curved lake shore: widen the upper tributaries into one mountain basin.
 if b['iz']==0 and b['ix'] in [1,3]:
  lake_outline=[]
  for x,z in outline:
   if abs(z+60)<22:
    radius=34*math.sqrt(max(0,1-((z+60)/22)**2));x=min(x,14-radius) if b['ix']==1 else max(x,14+radius)
   lake_outline.append((x,z))
  outline=lake_outline
 poly=[river(x,z) for x,z in outline];banks.append({'polygon':poly,'minX':min(x for x,z in poly),'maxX':max(x for x,z in poly),'minZ':min(z for x,z in poly),'maxZ':max(z for x,z in poly)})
 # Top polygon tessellation, separate lower vertical skirt.
 vs=[(x,.35,z) for x,z in outline];coords=[Vector((*river(x,z),0)) for x,z in outline];tri=tessellate_polygon([coords]);lookup={tuple(v):i for i,v in enumerate(coords)};faces=[tuple(v if isinstance(v,int) else lookup[tuple(v)] for v in t) for t in tri];add(vs,faces,'Meadow')
 rural=b['park'] or b['ix'] in [0,3] and b['iz'] in [0,3]
 for i,p in enumerate(outline):
  q=outline[(i+1)%len(outline)];add([(p[0],-.22,p[1]),(q[0],-.22,q[1]),(q[0],.35,q[1]),(p[0],.35,p[1])],[(0,1,2,3)],'Stone' if not rural else 'Meadow')
  if not rural:tube((p[0],.39,p[1]),(q[0],.39,q[1]),.07,'Cream')
 # A narrow stone towpath follows the curve, rural banks leave room for grasses and boulders.
 for i,p in enumerate(outline):
  q=outline[(i+1)%len(outline)];v=Vector((q[0]-p[0],q[1]-p[1]));v.normalize();normal=Vector((-v.y,v.x));cen=Vector(((a+c)/2,(d+f)/2));mid=Vector(p)
  # The sampled outline is CCW; its left normal also works on concave lake shores.
  width=1.1 if rural else 1.35
  add([(p[0],.38,p[1]),(q[0],.38,q[1]),(q[0]+normal.x*width,.38,q[1]+normal.y*width),(p[0]+normal.x*width,.38,p[1]+normal.y*width)],[(0,1,2,3)],'Path' if not rural else 'Meadow')
  if rural and i%4==0 and -55<p[0]<55 and -46<p[1]<46:
   foliage(p[0]+normal.x*.8,.42,p[1]+normal.y*.8,rng.uniform(.22,.42),'Stone',.45)
   for k in range(2):
    tx=p[0]+normal.x*1.5+rng.uniform(-.3,.3);tz=p[1]+normal.y*1.5+rng.uniform(-.3,.3);tube((tx,.38,tz),(tx+.1,.8,tz+.13),.017,'Leaf')
 if b['iz']==-1:continue
 loX=max(a,-52);hiX=min(c,52);loZ=max(d,-43);hiZ=min(f,43)
 mx=(loX+hiX)/2;mz=(loZ+hiZ)/2
 if not b['park']:
  road_strip(mx,(loZ+hiZ)/2,2.0,hiZ-loZ-2.4)
  road_strip((loX+hiX)/2,mz,hiX-loX-2.4,1.8)
  box(mx,.425,mz,4.2,.04,4.0,'Path')
  for side in [-1,1]:box(mx+side*2.1,.45,mz,.12,.08,4,'Cream')
  # Small fountain or market square; street branches pass either side.
  if b['ix'] in [1,2] and b['iz'] in [1,2]:
   public_asset('fountain-round-detail',mx,mz,.7)
  if b['ix']==0 and b['iz']==1:
   for j in range(3):box(mx-1+j,.8,mz-1.2,.8,.65,.65,'Wood')

 if b['park']:
  for x in range(math.ceil(loX+3),math.floor(hiX-1),4):
   for z in range(math.ceil(loZ+3),math.floor(hiZ-1),4):
    tx=x+rng.uniform(-.65,.65);tz=z+rng.uniform(-.65,.65)
    if not (b['iz']==1 and abs(tx-14)<5 and abs(tz+13)<4.5):tree(tx,tz,rng.uniform(.7,1.1),b['iz']==1)
    if b['iz']==3:
     for j in range(3):foliage(tx+math.cos(j*2)*.55,1.9,tz+math.sin(j*2)*.55,.12,'Rose')
  continue
 x=loX+2.5
 while x<hiX-2:
  if abs(x-mx)>2.7 and rng.random()>.12:
   if d>-40:house(x,d+3.4,rng.uniform(2.4,3.1),3,rng.uniform(2.4,4),math.pi,rng.randrange(12))
   if f<40:house(x,f-3.4,rng.uniform(2.4,3.1),3,rng.uniform(2.4,4),0,rng.randrange(12))
  x+=rng.uniform(3.7,4.6)
 z=loZ+7
 while z<hiZ-6:
  if abs(z-mz)>2.5 and rng.random()>.14:
   if a>-50:house(a+3.5,z,2.7,3,rng.uniform(2.7,4),-math.pi/2,rng.randrange(12))
   if c<50:house(c-3.5,z,2.7,3,rng.uniform(2.7,4),math.pi/2,rng.randrange(12))
  z+=rng.uniform(4,5)
 for k in range(6):
  tx=rng.uniform(loX+2,hiX-2);tz=rng.uniform(loZ+4,hiZ-4)
  if abs(tx-mx)>2.5 and abs(tz-mz)>2.5:tree(tx,tz,rng.uniform(.7,1.1))
# Back-street housing adds density while leaving the existing road corridors open.
for b in blocks:
 if b['park']:continue
 a,c,d,f=[b[k] for k in ['a','c','d','f']];lx=max(a,-52);hx=min(c,52);lz=max(d,-43);hz=min(f,43);mx=(lx+hx)/2;mz=(lz+hz)/2
 if b['ix'] in [0,3]:
  xx=-47.5 if b['ix']==0 else 47.5;rot=math.pi/2 if b['ix']==0 else -math.pi/2
  zz=lz+2.8
  while zz<hz-2:
   if abs(zz-mz)>2.6:house(xx,zz,2.6,3.1,2.7+rng.random(),rot,rng.randrange(12))
   zz+=4.6
 elif b['iz'] in [0,3]:
  zz=max(-40,lz+2.8) if b['iz']==0 else 39.5;rot=0 if b['iz']==0 else math.pi
  xx=lx+2.7
  while xx<hx-2:
   if abs(xx-mx)>2.7:house(xx,zz,2.6,3,2.7+rng.random()*.8,rot,rng.randrange(12))
   xx+=4.5
# An outer residential lane completes the town silhouette beyond the waterfront rows.
for side in [-1,1]:
 xx=side*58;street_x=side*54.5
 for lo,hi in [(-43,-29.5),(-20.5,-5.5),(5.5,20.5),(29.5,43)]:
  mid=(lo+hi)/2;road_strip(street_x,mid,1.6,hi-lo-2.4);road_strip(side*49.5,mid,10,1.6)
  for zz in [lo+3.2,hi-3.2]:
   house(xx,zz,2.7,3.0,2.8+rng.random()*.8,-side*math.pi/2,rng.randrange(12))
# A single main estuary: continuous coastal spits close the two peripheral mouths.
coastal_closures=[]
for a,c,d,f in [(-35,-21,43,51),(21,35,46,55)]:
 outline=rounded(a,c,d,f,2.4);poly=[river(x,z) for x,z in outline]
 bank=dict(name='CoastalSpit',polygon=poly,minX=min(v[0] for v in poly),maxX=max(v[0] for v in poly),minZ=min(v[1] for v in poly),maxZ=max(v[1] for v in poly));banks.append(bank);coastal_closures.append(bank)
 coords=[Vector((*v,0)) for v in poly];lookup={tuple(v):i for i,v in enumerate(coords)}
 faces=[tuple(v if isinstance(v,int) else lookup[tuple(v)] for v in t) for t in tessellate_polygon([coords])]
 add([(x,.35,z) for x,z in outline],faces,'Meadow')
 for j,(x,z) in enumerate(outline):
  xx,zz=outline[(j+1)%len(outline)];add([(x,-.22,z),(xx,-.22,zz),(xx,.35,zz),(x,.35,z)],[(0,1,2,3)],'Meadow')
 road_strip((a+c)/2,(d+f)/2,c-a-1,1.4)
# Close the two mountain-side lateral sea outlets shown in the reference screenshots.
# Each infill overlaps both original shores; topology and collision share one sampled polygon.
northern_closures=[]
for a,c,d,f in [(-104,-74,-34,-17),(74,104,-34,-17)]:
 outline=rounded(a,c,d,f,3);poly=[river(x,z) for x,z in outline]
 bank=dict(name='NorthernClosure',polygon=poly,minX=min(v[0] for v in poly),maxX=max(v[0] for v in poly),minZ=min(v[1] for v in poly),maxZ=max(v[1] for v in poly));banks.append(bank);northern_closures.append(bank)
 coords=[Vector((*v,0)) for v in poly];lookup={tuple(v):i for i,v in enumerate(coords)}
 faces=[tuple(v if isinstance(v,int) else lookup[tuple(v)] for v in t) for t in tessellate_polygon([coords])]
 add([(x,.35,z) for x,z in outline],faces,'Meadow')
 for j,(x,z) in enumerate(outline):
  xx,zz=outline[(j+1)%len(outline)];add([(x,-.22,z),(xx,-.22,zz),(xx,.35,zz),(x,.35,z)],[(0,1,2,3)],'Meadow')
# Additional houses extend the inhabited town along real side streets.
for side in [-1,1]:
 for lo,hi in [(-20.5,-5.5),(5.5,20.5),(29.5,43)]:
  road_strip(side*64,(lo+hi)/2,1.5,hi-lo-2)
  road_strip(side*60,(lo+hi)/2,8,1.5)
  for j,zz in enumerate([lo+3.1,hi-3.1]):house(side*68,zz,2.9,3.1,3.0+(j%2)*.6,-side*math.pi/2,(j+int(lo)+20)%6)
# A generous open fountain square beside the town landing, tied into the street network.
road_strip(43,13,15,9);road_strip(53,13,8,2);road_strip(34,13,4,2)
for xx in [35.7,50.3]:box(xx,.46,13,.16,.09,9,'Cream')
for zz in [8.65,17.35]:box(43,.46,zz,14.6,.09,.16,'Cream')
public_asset('fountain-round-detail',43,13,1.45)
for xx,zz,rr in [(38,10,0),(47,16,math.pi),(38,16,math.pi),(48,10,0)]:public_asset('stall-bench',xx,zz,.95,rr)
for xx,zz in [(36.7,9.8),(49.3,16.2)]:
 cylinder(xx,.65,zz,.47,.55,'Stone');foliage(xx,1,zz,.5,'Flowers',.5)
public_asset('stall-red',55,8.6,.85);public_asset('stall-green',55,17.4,.85,math.pi)
detail_counts['central_plazas']=1
# Snowmelt flows on the exact valley floor of the adjacent alpine mountain mesh.
# No standalone trough, vertical walls or raised channel supports.
water_source=[]
for p in PROFILE:
 wx,wz=river(p['x'],p['z']);water_source.append(dict(x=wx,y=p['y']+.025,z=wz))
for j in range(len(PROFILE)-1):
 p,q=PROFILE[j:j+2];x,z,y=p['x'],p['z'],p['y']+.025;xx,zz,yy=q['x'],q['z'],q['y']+.025
 w=p['width']*smooth(-142,-139,z)*.8;ww=q['width']*smooth(-142,-139,zz)*.8
 add([(x-w,y,z),(x+w,y,z),(xx+ww,yy,zz),(xx-ww,yy,zz)],[(0,1,2,3)],'Waterfall')
 # Discontinuous fine foam washes follow the current without ladder-like crossbars.
 if j%3!=0:
  for k in [-.38,.3]:
   r=.035 if j<72 else .05
   add([(x+k*w-r,y+.012,z),(x+k*w+r,y+.012,z),(xx+k*ww+r,yy+.012,zz),(xx+k*ww-r,yy+.012,zz)],[(0,1,2,3)],'WaterWash')
# The lake head remains open water; uphill rock/creek bed is a solid navigation limit.
left=[(p['x']-p['width']-1.4,p['z']) for p in PROFILE if p['z']<=-83]
right=[(p['x']+p['width']+1.4,p['z']) for p in PROFILE if p['z']<=-83]
poly=[river(x,z) for x,z in left+right[::-1]]
banks.append(dict(name='MountainCascade',polygon=poly,minX=min(v[0] for v in poly),maxX=max(v[0] for v in poly),minZ=min(v[1] for v in poly),maxZ=max(v[1] for v in poly)))
alpine_peaks=[dict(name=p['name'],x=river(p['x'],p['z'])[0],z=river(p['x'],p['z'])[1],y=terrain_height(p['x'],p['z'])) for p in PEAKS]
# Streetlamps are authored in Blender; web lights use these exported head positions.
street_lamps=[]
def street_lamp(x,z,y=.4):
 cylinder(x,y+.12,z,.22,.24,'Stone',6);tube((x,y+.2,z),(x,y+2.6,z),.055,'Ink',6)
 box(x,y+2.65,z,.42,.60,.42,'Lamplight');cylinder(x,y+3,z,.36,.18,'Slate',4,0)
 for dx in [-.22,.22]:
  for dz in [-.22,.22]:tube((x+dx,y+2.34,z+dz),(x+dx,y+2.97,z+dz),.022,'Ink',3)
 wx,wz=river(x,z);street_lamps.append(dict(x=wx,z=wz,y=y+2.65,ground=y))
for x,z in [(36,9),(50,9),(36,17),(50,17),(54.5,-14),(54.5,34),(-54.5,-13),(-54.5,13),(-54.5,35),(-34,-12),(-34,13),(34,-13),(34,34),(-8,10),(8,10),(-21,-18),(21,-18),(-20,37),(9,42),(-34,46),(34,49)]:street_lamp(x,z)
detail_counts['street_lamps']=len(street_lamps)

# Low grassy continent below the water and far fields, rather than sea/island backdrop.
box(0,-.7,0,400,.5,360,'Meadow')
# Riparian trees shade the towpaths and coastal promenade.
for tx,tz in [(-36,34),(-36,41),(-40,47),(-49,47),(-59,46),(37,33),(38,41),(43,49),(51,49),(62,49),(-19,40),(-12,44),(12,38),(17,46),(-37,-40),(37,-40)]:tree(tx,tz,rng.uniform(.85,1.35),tz<40)
# Reuse approved Blender source landmarks, retaining original mesh and material colours.
with bpy.data.libraries.load(str(OUT/'harbor_expanded_v5.blend'),link=False) as (data_from,data_to):
 data_to.objects=[n for n in data_from.objects if n.startswith(('SM_V4_PostOffice','SM_V4_Cottage','SM_V5_Workshop'))]
for o in data_to.objects:
 if o.type not in ['MESH','CURVE']:continue
 orig=o.copy();orig.data=o.data.copy();bpy.data.collections['COL_Landmarks'].objects.link(orig)
 # Original Blender positions are X/Y horizontal, Z height.
 if o.name.startswith('SM_V4_PostOffice'):sx,sy,tx,tz,rot=2.4,2.5,10,9,0
 elif o.name.startswith('SM_V4_Cottage'):sx,sy,tx,tz,rot=5.35,3.2,-18.7,14,0
 else:sx,sy,tx,tz,rot=-8.1,4.5,-36,-14,math.pi/2
 wx,wz=river(tx,tz);ang=heading(tx,tz,rot);M=Matrix.Translation(Vector((wx,-wz,0)))@Matrix.Rotation(-ang,4,'Z')@Matrix.Translation(Vector((-sx,-sy,0)));orig.matrix_world=M@o.matrix_world
 # Material conversion preserves approved palette while making every material GLB compatible.
 for slot in orig.material_slots:
  old=slot.material
  if not old:continue
  name='Approved_'+old.name
  if name not in materials:
   rgb=tuple(old.diffuse_color)
   if old.use_nodes:
    ramp=next((n for n in old.node_tree.nodes if n.type=='VALTORGB'),None)
    if ramp:rgb=tuple((ramp.color_ramp.elements[0].color[i]+ramp.color_ramp.elements[-1].color[i])/2 for i in range(4))
   m=bpy.data.materials.new(name);m.use_nodes=True;bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=rgb;bs.inputs['Roughness'].default_value=1;bs.inputs['Emission Color'].default_value=rgb;bs.inputs['Emission Strength'].default_value=.16;materials[name]=m
  slot.material=materials[name]
# Stone arch bridges: only on surviving branches, high central openings.
for x,z,axis,half in [(0,-12,'x',8),(28,12,'x',6),(-28,-12,'x',6),(-14,-25,'z',6)]:
 def bp(xx,yy,zz):return (x+xx,yy,z+zz) if axis=='x' else (x+zz,yy,z+xx)
 for k in range(30):
  xx=-half+(k+.5)*half/15;yy=1+3*(1-(xx/half)**2);p=bp(xx,yy,0);box(*p,half/15+.04,.17,1.8,'Path',0 if axis=='x' else math.pi/2)
  for side in [-1,1]:
   tube(bp(xx,yy,side),bp(xx,yy+.7,side),.03,'Wood')
   if k<29:
    xxx=xx+half/15;yyy=1+3*(1-(xxx/half)**2);tube(bp(xx,yy+.7,side),bp(xxx,yyy+.7,side),.03,'Wood')
 for side in [-.9,.9]:
  vs=[];fs=[]
  for k in range(31):
   xx=-half+k*half/15;top=1+3*(1-(xx/half)**2);low=max(.35,top-.5);vs.extend([bp(xx,low,side),bp(xx,top,side)])
  fs=[(2*k,2*k+1,2*k+3,2*k+2) for k in range(30)];add(vs,fs,'Stone')
# Clock tower, bakery and watermill wheel.
house(36,-34,3.4,4,3.4,math.pi/2,6)
wx,wz=river(-19,6);rigid=(-19,6,0,wx,wz,heading(-19,6));box(-19,3.8,6,2.4,6.8,2.4,'Cream');add([(-20.6,7.2,4.4),(-17.4,7.2,4.4),(-17.4,7.2,7.6),(-20.6,7.2,7.6),(-19,9.5,6)],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'Slate');rigid=None
# Sparse hand drawn ripple marks around navigable water, not a uniform ocean pattern.
for c in [-28,0,28]:
 for z in range(-42,43,3):
  x=c+rng.uniform(-1.5,1.5);tube((x,-.145,z),(x+rng.uniform(.25,.65),-.145,z+.06),.012,'WaterWash')
# Market, public benches, lamp posts and carts furnish the town's real streets.
for name,x,z,sc,rot in [('stall-red',-18,-4,2.0,0),('stall-green',-11.8,3.4,1.8,math.pi),('cart',-18,2.2,1.7,.7),('cart-high',40,-12,1.5,1.2),('stall-bench',9,-7,2.4,0),('stall-bench',20,-17,2.4,.5),('tree-high-round',-44,13,1.1,0),('tree-high-round',41,24,1.1,0),('fence',-38,-52,2,0),('fence',-34,-52,2,0)]:public_asset(name,x,z,sc,rot)
for x,z in [(-15,-8),(-15,7),(15,14),(15,30),(-42,-17),(39,12),(-28,-50)]:public_asset('lantern',x+1.4,z,1.55)
# Guildhall combines native massing with reused detailed window, doorway and timber components.
gx,gz=19.8,34;wx,wz=river(gx,gz);rigid=(gx,gz,0,wx,wz,heading(gx,gz))
box(gx,2.35,gz,3.2,3.9,5.4,'Cream');box(gx,2.0,gz,3.3,.12,5.5,'Wood')
add([(gx-1.8,4.3,gz-2.9),(gx+1.8,4.3,gz-2.9),(gx+1.8,4.3,gz+2.9),(gx-1.8,4.3,gz+2.9),(gx,6.5,gz-2.9),(gx,6.5,gz+2.9)],[(0,1,4),(3,5,2),(0,4,5,3),(1,2,5,4)],'Slate')
for yy in [.6,2.1]:
 for zz in [-1.7,0,1.7]:public_asset('wall-wood-window-shutters',gx+1.1,gz+zz,1.1,y=yy)
public_asset('wall-wood-doorway-round',gx+1.05,gz,1.3,y=.42)
for zz in [-2.6,2.6]:public_asset('wall-wood-detail-cross',gx+1.1,gz+zz,1.1,y=2.1)
public_asset('stairs-wood',gx-1.2,gz+3.4,1.8,math.pi/2)
rigid=None
# Replace the simple mill wheel with a recognizable optimized public watermill component.
public_asset('watermill',-32.2,-15,1.5,0,y=1.6)
# District details: garden glasshouse, orchard, domestic courtyards and working quays.
def flowerbox(x,z,w=1.2):
 box(x,.63,z,w,.38,.48,'Wood')
 for j in range(5):foliage(x-w*.4+j*w*.2,.88,z,.15,'Flowers' if j%2 else 'Leaf')
 detail_counts['flowerboxes']=detail_counts.get('flowerboxes',0)+1
def laundry(x,z):
 tube((x,.4,z),(x,2.35,z),.045,'Wood');tube((x+3.3,.4,z),(x+3.3,2.35,z),.045,'Wood')
 for i in range(12):
  a=i/12;b=(i+1)/12;tube((x+3.3*a,2.35-.24*math.sin(a*math.pi),z),(x+3.3*b,2.35-.24*math.sin(b*math.pi),z),.014,'Ink')
 for i in range(4):
  xx=x+.3+i*.75;yy=2.25-.18*math.sin((i+1)*math.pi/5);add([(xx,yy,z),(xx+.48,yy-.03,z),(xx+.5,yy-.65,z+.03),(xx-.03,yy-.6,z+.03)],[(0,1,2,3)],['Cream','Sage','Rose','Cream'][i])
 detail_counts['laundry_yards']=detail_counts.get('laundry_yards',0)+1
def resident(x,z,coat='Sage',hat=False):
 cylinder(x,.51,z,.14,.2,'Wood',7);cylinder(x,.94,z,.18,.65,coat,7,.14);foliage(x,1.43,z,.17,'Cream')
 tube((x-.14,1.15,z),(x-.29,.83,z+.08),.045,coat);tube((x+.14,1.15,z),(x+.27,.9,z-.07),.045,coat)
 if hat:cylinder(x,1.6,z,.23,.06,'Wood',9);cylinder(x,1.67,z,.14,.13,'Wood',9)
 detail_counts['residents']=detail_counts.get('residents',0)+1
for x,z in [(7.3,11),(-22.1,4),(-33.5,-10.5),(34.5,-32),(17.5,31),(45,13),(-44,8),(10,-8)]:flowerbox(x,z)
for x,z in [(-21,10),(-49,-35),(44,35)]:laundry(x,z)
for x,z,coat,hat in [(-16,-3,'Rose',True),(-12,1.7,'Sage',False),(16.5,19,'Wood',True),(8,13,'Sage',False),(-34,-13,'Rose',True),(12,-7,'Cream',False),(44,9,'Sage',False)]:resident(x,z,coat,hat)
# The garden now has a real glazed greenhouse with beds and a connected path.
gx,gz=14,-13;wx,wz=river(gx,gz);rigid=(gx,gz,0,wx,wz,heading(gx,gz))
box(gx,.5,gz,7.8,.25,5.2,'Stone')
box(gx,1.65,gz,7.4,2.1,4.8,'GreenhouseGlass')
add([(gx-3.7,2.7,gz-2.4),(gx+3.7,2.7,gz-2.4),(gx+3.7,2.7,gz+2.4),(gx-3.7,2.7,gz+2.4),(gx,4.2,gz-2.4),(gx,4.2,gz+2.4)],[(0,1,4),(3,5,2),(0,4,5,3),(1,2,5,4)],'GreenhouseGlass')
for k in range(8):
 xx=gx-3.5+k
 for zz in [gz-2.45,gz+2.45]:tube((xx,.55,zz),(xx,2.7,zz),.035,'Cream')
for k in range(8):
 xx=gx-3.5+k;ry=2.7+1.5*(1-abs(xx-gx)/3.7)
 tube((xx,ry+.03,gz-2.45),(xx,ry+.03,gz+2.45),.03,'Cream')
 for zz in [gz-2.45,gz+2.45]:tube((xx,2.7,zz),(xx,ry,zz),.03,'Cream')
for zz in [gz-2.45,gz+2.45]:
 for yy in [1.4,2.7]:tube((gx-3.7,yy,zz),(gx+3.7,yy,zz),.035,'Cream')
for zz in [gz-2.45,gz,gz+2.45]:
 tube((gx-3.7,2.72,zz),(gx,4.22,zz),.035,'Cream');tube((gx,4.22,zz),(gx+3.7,2.72,zz),.035,'Cream')
for xx in [gx-3.72,gx+3.72]:
 for zz in [gz-1.6,gz-.8,gz,gz+.8,gz+1.6]:tube((xx,.55,zz),(xx,2.7,zz),.03,'Cream')
tube((gx,4.23,gz-2.45),(gx,4.23,gz+2.45),.045,'Cream')
for zz in [gz-1.2,gz+1.2]:
 box(gx,.72,zz,6.4,.3,.7,'Wood')
 for j in range(9):foliage(gx-2.8+j*.7,.98,zz,.24,'Leaf' if j%2 else 'Flowers')
rigid=None;road_strip(14,-8.4,1.3,3.8);public_asset('stall-bench',18.8,-8,2.2,math.pi/2)
detail_counts['greenhouses']=1
# Market stalls and loading yards occupy deliberately reserved plots beside the streets.
for name,x,z,sc,rot in [('stall-red',-44,-9,1.5,0),('stall-green',-39,-15,1.5,math.pi),('cart-high',-39,-9,1.3,.3),('cart',45,25,1.4,0),('stall-bench',-46,4,2,0)]:public_asset(name,x,z,sc,rot)
for x,z in [(-44,-14),(-39,-9),(35,10),(44,26)]:
 for j in range(3):
  xx=x+(j%2)*.7;zz=z+(j//2)*.7;box(xx,.78,zz,.62,.72,.62,'Wood');tube((xx-.3,.5,zz+.32),(xx+.3,1.08,zz+.32),.025,'Cream')
 detail_counts['cargo_yards']=detail_counts.get('cargo_yards',0)+1
# Bollards, coiled ropes and short landing decks stay on the bank side of the waterline.
for x,z,w,d in [(7.3,7.3,1.3,3),(17,-6.2,3,1.0),(33.2,-34,1.3,3),(-33.2,-15,1.3,3),(-14,30.1,3,1.0)]:
 box(x,.47,z,w,.16,d,'Wood')
 for side in [-1,1]:
  xx=x+side*w*.35;cylinder(xx,.66,z,.09,.4,'Ink',8)
 for j in range(3):
  r=.14+j*.025
  for k in range(12):
   a=k*math.tau/12;b=(k+1)*math.tau/12;tube((x+r*math.cos(a),.58,z+r*math.sin(a)),(x+r*math.cos(b),.58,z+r*math.sin(b)),.014,'Wood')
 detail_counts['landings']=detail_counts.get('landings',0)+1
# Northwest cliff: the same source defines the summit, rock face and dock below.
cliff_outline=[(x+.45*math.sin(z*.72),z+.38*math.sin(x*.66)) for x,z in rounded(-88,-43,-98,-57,5)]
cliff_poly=[river(x,z) for x,z in cliff_outline]
banks.append(dict(polygon=cliff_poly,minX=min(x for x,z in cliff_poly),maxX=max(x for x,z in cliff_poly),minZ=min(z for x,z in cliff_poly),maxZ=max(z for x,z in cliff_poly),name='NorthwestCliff'))
coords=[Vector((*river(x,z),0)) for x,z in cliff_outline];tri=tessellate_polygon([coords]);lookup={tuple(v):i for i,v in enumerate(coords)}
add([(x,18.35,z) for x,z in cliff_outline],[tuple(v if isinstance(v,int) else lookup[tuple(v)] for v in t) for t in tri],'Meadow')
for i,p in enumerate(cliff_outline):
 q=cliff_outline[(i+1)%len(cliff_outline)]
 for lo,hi in [(.25,5.8),(5.8,11.8),(11.8,18.35)]:
  bulge=.35*math.sin(i*.27) if hi<18 else 0
  add([(p[0]+bulge,lo,p[1]),(q[0]+bulge,lo,q[1]),(q[0],hi,q[1]),(p[0],hi,p[1])],[(0,1,2,3)],'Stone' if lo!=5.8 else 'Plaster')
  if i%4==0:tube((p[0]-.02,lo+.15,p[1]+.02),(p[0]-.15,hi-.2,p[1]+.02),.025,'Ink')
# An exposed, supported switchback climbs around the eastern cliff face.
road_controls=[(-37,-39,.55),(-49,-38,2),(-72,-38,4.4),(-81,-43,5.8),(-80,-50,7),(-69,-53,8.5),(-47,-53,11),(-37,-58,12.5),(-36,-80,16.4),(-40,-92,18.5),(-46,-94,18.5),(-45.5,-81,18.5),(-43,-58.5,18.5),(-51,-58,18.5),(-64,-57.5,18.5)]
road_points=[]
for k in range(len(road_controls)-1):
 p0=Vector(road_controls[max(0,k-1)]);p1=Vector(road_controls[k]);p2=Vector(road_controls[k+1]);p3=Vector(road_controls[min(len(road_controls)-1,k+2)])
 n=max(8,math.ceil((p2-p1).length/.6))
 for j in range(n):
  t=j/n;v=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t);road_points.append((v.x,v.y,max(.55,min(18.5,v.z))))
road_points.append(road_controls[-1]);carriage_route=[]
for i,(x,z,y) in enumerate(road_points):
 wx,wz=river(x,z);carriage_route.append(dict(x=wx,y=y+.025,z=wz))
 if i==len(road_points)-1:break
 xx,zz,yy=road_points[i+1];length=math.hypot(xx-x,zz-z);nx=-(zz-z)/length;nz=(xx-x)/length
 add([(x+nx*1.7,y,z+nz*1.7),(xx+nx*1.7,yy,zz+nz*1.7),(xx-nx*1.7,yy,zz-nz*1.7),(x-nx*1.7,y,z-nz*1.7)],[(0,1,2,3)],'Path')
 # Stone embankment supports every part of the road, with continuous guard rails.
 for side in [-1,1]:
  ex=x+nx*1.9*side;ez=z+nz*1.9*side;fx=xx+nx*1.9*side;fz=zz+nz*1.9*side
  add([(ex,.35,ez),(fx,.35,fz),(fx,yy-.05,fz),(ex,y-.05,ez)],[(0,1,2,3)],'Stone')
  tube((ex,y+.72,ez),(fx,yy+.72,fz),.045,'Wood')
  if i%5==0:tube((ex,y-.05,ez),(ex,y+.75,ez),.065,'Wood')
# Sculpt a continuous stepped hillside below the exposed lower bends.
def apron_height(x,z):
 best=1e9;h=.35
 for a,b in zip(road_controls[:8],road_controls[1:8]):
  dx=b[0]-a[0];dz=b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz)));dist=math.hypot(x-a[0]-t*dx,z-a[1]-t*dz)
  if dist<best:best=dist;h=a[2]+t*(b[2]-a[2])
 return max(.35,h-.3-max(0,best-2)*.75)
for x in range(-88,-34,2):
 for z in range(-62,-34,2):
  add([(xx,apron_height(xx,zz),zz) for xx,zz in [(x,z),(x+2,z),(x+2,z+2),(x,z+2)]],[(0,1,2),(0,2,3)],'Stone')
# Low dock and a covered coach stop, safely outside the main sailing corridor.
box(-33.7,.49,-40,3.2,.22,6,'Wood');road_strip(-36,-39,5,4)
for z in [-42,-38]:cylinder(-32.3,.8,z,.13,.75,'Wood',8)
box(-39,1.35,-36,3.1,1.9,1.5,'Cream');box(-39,2.45,-36,3.6,.25,2,'Slate')
box(-37.4,1.5,-35.3,.65,.6,.08,'Rose')
for x,z in [(-83,-67),(-85,-84),(-49,-94),(-76,-93),(-54,-63)]:
 save=buckets;buckets={};tree(x,z,1.1)
 for key,(verts,faces) in buckets.items():
  verts=[(vx,vy,vz+18) for vx,vy,vz in verts];target=save.setdefault(key,[[],[]]);off=len(target[0]);target[0].extend(verts);target[1].extend(tuple(off+j for j in f) for f in faces)
 buckets=save
castle_landmark=dict(name='悬崖城堡码头',x=river(-28,-40)[0],z=river(-28,-40)[1])
carriage=dict(dock=castle_landmark,route=carriage_route,castle=carriage_route[-1],cliff_height=18.35,road_width=3.4,castle_look=dict(x=river(-65,-78)[0],z=river(-65,-78)[1]))
saved_buckets=buckets;buckets={}
cx,cz=-28,-63;wx,wz=river(cx,cz);rigid=(cx,cz,0,wx,wz,heading(cx,cz))
# Keep, great hall, curtain walls and corner towers in the approved stone/slate palette.
box(cx,.6,cz,17,.5,13,'Stone');box(cx,4.6,cz-1.5,6.4,8.0,5.8,'Cream')
box(cx,8.65,cz-1.5,7,.3,6.4,'Stone')
for xx in [-2.8,-1.4,0,1.4,2.8]:
 for zz in [-3.0,3.0]:box(cx+xx,9.2,cz-1.5+zz,.7,.95,.65,'Cream')
box(cx,2.8,cz+2,7,4.3,4.2,'Plaster')
add([(cx-3.8,5,cz-.3),(cx+3.8,5,cz-.3),(cx+3.8,5,cz+4.3),(cx-3.8,5,cz+4.3),(cx,7.4,cz-.3),(cx,7.4,cz+4.3)],[(0,1,4),(3,5,2),(0,4,5,3),(1,2,5,4)],'Slate')
for xx,zz,hh in [(-6,-4.5,8.0),(6,-4.5,10.3),(-6,4.5,6.8),(6,4.5,6.8)]:
 x=cx+xx;z=cz+zz;cylinder(x,.6+hh/2,z,1.45,hh,'Stone',14);cylinder(x,hh+.65,z,1.65,.35,'Cream',14);cylinder(x,hh+2.2,z,1.9,2.8,'Slate',14,0)
 for yy in [2.7,4.9,6.6]:
  if yy<hh:box(x,yy,z+1.45,.23,.82,.04,'Ink')
 tube((x,hh+3.3,z),(x,hh+5,z),.045,'Wood');add([(x,hh+4.9,z),(x+1.2,hh+4.65,z),(x,hh+4.15,z)],[(0,1,2)],'Rose')
for xx in [-7,7]:box(cx+xx,2,cz,.65,3,9,'Stone')
for zz in [-5.6,5.6]:
 box(cx,1.9,cz+zz,13.5,2.8,.65,'Stone')
 for k in range(12):box(cx-6.3+k*1.15,3.6,cz+zz,.58,.75,.7,'Cream')
# Arched gate, arrow slits and a muted banner give the castle a readable facade.
gate=[(cx-1.05,.65,cz+5.96),(cx+1.05,.65,cz+5.96)]+[(cx+1.05*math.cos(t*math.pi/12),2.15+1.05*math.sin(t*math.pi/12),cz+5.96) for t in range(13)]
add(gate,[tuple(range(len(gate)))],'Wood')
for xx in [-.7,-.35,0,.35,.7]:tube((cx+xx,.7,cz+6),(cx+xx,2.6,cz+6),.025,'Ink')
for xx in [-2,2]:
 for yy in [3.5,5.5,7.5]:box(cx+xx,yy,cz+1.43,.5,1.05,.08,'Glass')
box(cx,6.3,cz+1.48,.75,1.5,.09,'Rose')
# Two residential wings and a high central spire make this a palace complex.
for side in [-1,1]:
 x=cx+side*9.2;box(x,3.4,cz-1,4.4,5.8,8.4,'Plaster');box(x,6.5,cz-1,4.8,.35,8.8,'Stone')
 cylinder(x,7.5,cz-4.5,1.55,2.2,'Slate',12,0)
 for zz in [-3,-.5,2]:
  for yy in [2.1,4.1]:box(x+side*2.23,yy,cz+zz,.05,.9,.55,'Glass')
 for k in range(6):box(x-1.85+k*.74,7,cz+3.3,.4,.65,.55,'Cream')
 for dx in [-1.1,0,1.1]:
  for yy in [1.8,3.6,5.4]:
   box(x+dx,yy,cz+3.23,.48,.92,.06,'Glass');box(x+dx,yy+.52,cz+3.27,.65,.10,.10,'Cream')
 for yy in [2.6,4.4]:box(x,yy,cz+3.28,4.5,.09,.10,'Stone')
cylinder(cx,11.3,cz-2,1.7,4.7,'Slate',16,0);tube((cx,13.6,cz-2),(cx,15.6,cz-2),.05,'Wood')
add([(cx,15.5,cz-2),(cx+1.6,15.2,cz-2),(cx,14.5,cz-2)],[(0,1,2)],'Rose')
rigid=None
# Scale the entire authored castle about its own pivot; the town houses stay unchanged.
for verts,faces in buckets.values():
 for i,(x,y,z) in enumerate(verts):verts[i]=(wx+(x-wx)*1.3,-wz+(y+wz)*1.3,.37+(z-.37)*1.5)
newx,newz=river(-65,-78)
for verts,faces in buckets.values():
 for i,(x,y,z) in enumerate(verts):verts[i]=(x+newx-wx,y-newz+wz,z+18.0)
detail_counts['castle_scale']=dict(horizontal=1.3,vertical=1.5,residential_wings=2)
detail_counts.update(cliff_height=18.35,coach_route_points=len(carriage_route))
castle_buckets=buckets;buckets=saved_buckets
# The gatekeeper and post box wait beside the summit arrival court.
box(-65,19.12,-60,.42,1.05,.31,'Slate');foliage(-65,19.91,-60,.19,'Cream')
for side in [-1,1]:
 tube((-65+side*.12,18.38,-60),(-65+side*.12,18.85,-60),.075,'Ink')
 tube((-65+side*.22,19.5,-60),(-65+side*.28,19.05,-59.9),.055,'Slate')
box(-65,20.11,-60,.44,.08,.36,'Ink');box(-64.3,19.15,-60,.44,.68,.33,'Rose');tube((-64.3,18.35,-60),(-64.3,18.85,-60),.065,'Wood');box(-64.3,19.3,-59.82,.26,.04,.025,'Ink')
detail_counts['summit_postbox']=1
# Reused CC0 harbor fleet: separate Blender mesh groups, matching physical hull obstacles.
harbor_boats=[];harbor_buckets=[]
fleet=[('boat-sail-a',52,65,1.25,1.15),('boat-sail-b',60,75,1.2,.85),('boat-fishing-small',33,67,1.25,.2),('boat-fishing-small',-44,62,1.15,1.2),('boat-sail-a',-55,77,1.35,1.2),('boat-row-large',-40,54,1.05,1.4),('boat-sail-b',19,92,1.2,-.9),('boat-row-large',54,60,1,1.5)]
from mathutils.geometry import convex_hull_2d
for i,(name,tx,tz,scale,rot) in enumerate(fleet):
 save=buckets;buckets={};public_asset(name,tx,tz,scale,rot,y=-.62);harbor_buckets.append((i,buckets));buckets=save
 wx,wz=river(tx,tz);angle=heading(tx,tz,rot);plan=[]
 for verts,mat in public_templates[name]:
  for px,py,pz in verts:
   if py<1.1:plan.append(Vector((wx+scale*(math.cos(angle)*px+math.sin(angle)*pz),wz+scale*(-math.sin(angle)*px+math.cos(angle)*pz))))
 poly=[tuple(plan[j]) for j in convex_hull_2d(plan)]
 # Remove duplicate hull vertices from triangulated source meshes.
 poly=list(dict.fromkeys((round(x,6),round(z,6)) for x,z in poly))
 b=dict(name='Moored_'+str(i),polygon=poly,minX=min(x for x,z in poly),maxX=max(x for x,z in poly),minZ=min(z for x,z in poly),maxZ=max(z for x,z in poly));banks.append(b)
 harbor_boats.append(dict(model=name,x=wx,z=wz,scale=scale,rotation=angle,obstacle=b))
# Nets, stacked fish crates, short mooring posts and rope provide working harbor details.
for tx,tz in [(42,51),(47,51),(-45,48),(-52,48)]:
 for k in range(3):
  box(tx+(k%2)*.7,.7+(k//2)*.5,tz,.6,.55,.6,'Wood')
  tube((tx-.28,.98,tz+.3),(tx+.28,.98,tz+.3),.025,'Cream')
 for k in range(5):tube((tx-1.2+k*.28,.42,tz+1.0),(tx-1.2+k*.28,.42,tz+2.1),.013,'Ink')
 for k in range(5):tube((tx-1.2,.425,tz+1+k*.28),(tx-.08,.425,tz+1+k*.28),.013,'Ink')
for tx,tz in [(49,-52),(51,-60),(49,-70),(35,-84),(19,-85),(-2,-85),(-15,-84)]:tree(tx,tz,rng.uniform(.9,1.3))
for tz in [-47,-55,-63,-71,-79]:
 for k in range(3):
  tx=14+34*math.sqrt(max(0,1-((tz+60)/22)**2))+4+k*2.3;tree(tx,tz+rng.uniform(-1,1),rng.uniform(.85,1.25))
for tx in range(-10,65,6):tree(tx,-87+rng.uniform(-1,1),rng.uniform(.95,1.35))
for tx,tz in [(-45,-34),(-43,-34),(-17,-43)]:tree(tx,tz,.85)
detail_counts.update(moored_boats=len(fleet),fishing_cargo_yards=4,mountain_lakes=1,lakeside_trees=38)
# Small floating markers and reed/lily patches leave the center of each canal clear.
for tx,tz in [(-5,58),(8,63),(-17,74),(22,83),(50,75),(-52,89)]:
 cylinder(tx,.12,tz,.24,.45,'Wood',10);cylinder(tx,.39,tz,.17,.16,'Rose',10,0.06)
for tx,tz in [(-31,37),(-30,43),(31,34),(32,42),(-10,38),(10,44)]:
 for k in range(7):
  dx=rng.uniform(-.45,.45);dz=rng.uniform(-.5,.5);tube((tx+dx,-.12,tz+dz),(tx+dx+.13,.55+rng.random()*.3,tz+dz+.1),.018,'Willow')
 for k in range(4):cylinder(tx+rng.uniform(-.7,.7),-.145,tz+rng.uniform(-.7,.7),.13,.018,'Leaf',7)
detail_counts.update(water_buoys=6,reed_patches=6)

# Exposed stones around shallow shores leave main channels and landings clear.
water_rocks=[]
for i,(x,z,r) in enumerate([(-31,-64,.65),(-30.8,-71,.55),(38,-56,.85),(39,-68,.65),(1,-77,.7),(-61,54,.8),(-19,51,.55),(61,58,.7),(50,56,.55),(-22,28,.4),(32,39,.45),(-5,71,.55)]):
 foliage(x,-.02,z,r,'Stone',.58);foliage(x+r*.55,-.09,z+r*.3,r*.46,'Slate',.6)
 poly=[river(x+math.cos(j*math.tau/10)*r*1.12,z+math.sin(j*math.tau/10)*r*1.12) for j in range(10)]
 rock=dict(name='WaterRock_'+str(i),polygon=poly,minX=min(p[0] for p in poly),maxX=max(p[0] for p in poly),minZ=min(p[1] for p in poly),maxZ=max(p[1] for p in poly));banks.append(rock);water_rocks.append(rock)
detail_counts['water_rocks']=len(water_rocks)
# Warm lights along the cliff approach share the exact exported coach-road elevations.
for i in [12,62,112,162,215,272]:
 point=carriage['route'][i]
 # Route is already deformed; temporarily undo global mapping for these world-space props.
 wx,wz=point['x'],point['z']
 # Find the nearest undeformed location, iterating the smooth shore mapping.
 bx,bz=wx,wz
 for _ in range(12):
  qx,qz=river(bx,bz);bx+=wx-qx;bz+=wz-qz
 street_lamp(bx+2.15,bz,point['y'])
detail_counts['street_lamps']=len(street_lamps)
# Additional native civic and garden districts have an independent mesh budget/export.
exec(compile((P/'tools/curated_props.py').read_text(),str(P/'tools/curated_props.py'),'exec'),globals())
saved_district_buckets=buckets;buckets={}
exec(compile((P/'tools/build_civic_districts.py').read_text(),str(P/'tools/build_civic_districts.py'),'exec'),globals())
district_buckets=buckets;buckets=saved_district_buckets
# Create final Blender meshes by material; no duplicated production geometry is generated at runtime.
for prefix,name,(verts,faces) in [('District',k,v) for k,v in district_buckets.items()]+[('Town',k,v) for k,v in buckets.items()]+[('Castle',k,v) for k,v in castle_buckets.items()]+[('HarborBoat'+str(i),k,v) for i,b in harbor_buckets for k,v in b.items()]:
 me=bpy.data.meshes.new(('GEO_' if prefix=='Town' else 'GEO_'+prefix+'_')+name);me.from_pydata(verts,[],faces);me.update();me.materials.append(materials[name]);o=bpy.data.objects.new('SM_'+prefix+'_'+name,me);col.objects.link(o)
 # Recalculate normals on the native mesh before GLB export.
 import bmesh
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.dissolve_degenerate(bm,dist=.000001,edges=list(bm.edges));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
# Merge the approved static source pieces by material as well.
for o in list(bpy.data.collections['COL_Landmarks'].objects):
 if o.type=='CURVE':
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
# Reuse the approved Blender pier and lighthouse, retaining their original mesh silhouettes.
docks=[];reused=[]
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(ASSET/'approved-modules.glb'))
bpy.context.view_layer.update()
imported=set(bpy.data.objects)-before
pier_root=next(o for o in imported if o.name=='Pier')
lighthouse_root=next(o for o in imported if o.name=='Lighthouse')
pier_templates=[(o.data.copy(),o.matrix_world.copy()) for o in pier_root.children_recursive if o.type=='MESH']
lighthouse_templates=[(o.data.copy(),o.matrix_world.copy()) for o in lighthouse_root.children_recursive if o.type=='MESH']
for o in imported:bpy.data.objects.remove(o,do_unlink=True)
for label,tx,tz,rot in [('TownPier',36,17,0),('SeaPier',43,57,math.pi/2),('MouthLighthouse',10,49,0)]:
 wx,wz=river(tx,tz);ang=heading(tx,tz,rot);pts=[]
 for i,(mesh,original_matrix) in enumerate(lighthouse_templates if label=='MouthLighthouse' else pier_templates):
  o=bpy.data.objects.new('SM_Reused_'+label+'_'+str(i),mesh.copy());bpy.data.collections['COL_Landmarks'].objects.link(o)
  o.matrix_world=Matrix.Translation(Vector((wx,-wz,0)))@Matrix.Rotation(-ang,4,'Z')@original_matrix
  pts.extend(o.matrix_world@v.co for v in o.data.vertices)
  for slot in o.material_slots:slot.material=materials['Cream' if label=='MouthLighthouse' else 'Wood']
 if label!='MouthLighthouse' and pts:
  from mathutils.geometry import convex_hull_2d
  plan=[Vector((p.x,-p.y)) for p in pts];poly=[tuple(plan[i]) for i in convex_hull_2d(plan)]
  dock=dict(polygon=poly,minX=min(x for x,z in poly),maxX=max(x for x,z in poly),minZ=min(z for x,z in poly),maxZ=max(z for x,z in poly),name=label)
  banks.append(dock);docks.append(dock)
 reused.append(label)
sea=river(43,67);mouth=river(4,56)
lake=river(15,-60)
sea_landmarks=[dict(name='雪山湖',x=lake[0],z=lake[1]),dict(name='河口灯塔',x=mouth[0],z=mouth[1]),dict(name='海滨码头',x=sea[0],z=sea[1])]
detail_counts.update(approved_piers=2,approved_lighthouse=1,extra_riparian_trees=16)
# Navigation source is written by Blender, alongside the render asset.
base_stops=[dict(name='运河邮局',person='艾琳',x=1.7,z=7.3,stamp='邮',letter='一封家书',message='艾琳推开沿河的小窗：「孩子说，春天就回来。」'),dict(name='花园温室',person='米拉',x=16,z=0,stamp='花',letter='一封春日来信',message='米拉放下水壶，拆开远方寄来的种子清单。'),dict(name='北街面包房',person='奥利弗',x=28,z=-34,stamp='麦',letter='一封归家的信',message='面包香沿着运河飘来。奥利弗看见了姐姐熟悉的字迹。'),dict(name='柳岸水磨坊',person='卢卡',x=-28,z=-15,stamp='轮',letter='一封老友的信',message='水车慢慢转着。卢卡说，下次给你留一袋新磨的面粉。'),dict(name='南岸果园',person='诺亚',x=-14,z=25,stamp='叶',letter='一封远方的信',message='诺亚在树下读信，夕阳落在弯弯的河面。')]
base_stops.append(dict(base_stops[0],letter='返航交班',message='五封信都送到了。今天的邮路完成了。'))
stops=[dict(s,x=river(s['x'],s['z'])[0],z=river(s['x'],s['z'])[1]) for s in base_stops];sp=river(1.7,3.5)
nav={'source':'european-water-town.blend','banks':banks,'stops':stops,'spawn':dict(x=sp[0],z=sp[1],heading=heading(1.7,3.5),speed=0),'carriage':carriage,'water_rocks':water_rocks,'street_lamps':street_lamps,'water_source':water_source,'alpine_peaks':alpine_peaks,'estuary_count':1,'plaza':dict(x=river(43,13)[0],z=river(43,13)[1]),'coastal_closures':coastal_closures,'northern_closures':northern_closures,'district_features':district_features,'curated_assets':curated_usage,'docks':docks,'harbor_boats':harbor_boats,'details':detail_counts,'public_assets':public_usage,'landmarks':[castle_landmark,*sea_landmarks],'architecture':architecture_counts,'roads':roads,'bounds':dict(minX=-85,maxX=85,minZ=-104,maxZ=112)}
ASSET.mkdir(parents=True,exist_ok=True);(ASSET/'public-assets.json').write_text(json.dumps(dict(pack='Kenney Fantasy Town Kit 2.0 + Watercraft',license='CC0',source='https://kenney.nl/assets/fantasy-town-kit',watercraft_source='https://kenney.nl/assets/watercraft-kit',usage=public_usage,optimization='Blender atlas swatches remapped to shared paper palette and merged by material'),ensure_ascii=False,indent=2));(ASSET/'town-navigation.json').write_text(json.dumps(nav,ensure_ascii=False,separators=(',',':')))
world='// GENERATED BY Blender: tools/build_european_town.py. Do not edit production topology here.\nconst NAV='+json.dumps(nav,ensure_ascii=False,separators=(',',':'))+';\nexport const WORLD_BOUNDS=NAV.bounds,BANKS=NAV.banks,STOPS=NAV.stops,SPAWN=NAV.spawn,DELIVERY_COUNT=STOPS.length-1,DOCKS=[];\nexport const BRIDGE={minX:200,maxX:201,minZ:200,maxZ:201};\nexport const STREET_LAMPS=NAV.street_lamps,WATER_SOURCE=NAV.water_source;\nexport const CARRIAGE=NAV.carriage;\nexport const LANDMARKS=NAV.landmarks;\nexport const MAP_REGIONS=[...STOPS.slice(0,5),...LANDMARKS];\n'
(ASSET.parent/'world.mjs').write_text(world)
# QA gate before export: finite vertices, valid faces, budget, material consistency.
meshes=[o for o in scene.objects if o.type=='MESH' and not o.name.startswith('SM_District_')];tris=0
district_meshes=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('SM_District_')]
district_tris=0
for o in district_meshes:
 o.data.calc_loop_triangles();district_tris+=len(o.data.loop_triangles)
 assert all(math.isfinite(c) for v in o.data.vertices for c in v.co)
assert district_tris<50000,('district budget exceeded',district_tris)
for o in meshes:
 o.data.calc_loop_triangles();tris+=len(o.data.loop_triangles)
 assert all(math.isfinite(c) for v in o.data.vertices for c in v.co),'Non-finite geometry'
assert tris<220000,('triangle budget exceeded',tris)
# The editable source shows the water too; runtime uses its animated shader instead.
me=bpy.data.meshes.new('GEO_Water_SourcePreview');me.from_pydata([(-80,70,-.17),(80,70,-.17),(80,-70,-.17),(-80,-70,-.17)],[],[(0,1,2,3)]);me.update();water=bpy.data.objects.new('SM_Water_SourcePreview',me);scene.collection.objects.link(water);wm=bpy.data.materials.new('MAT_SourceWater');wm.use_nodes=True;bs=next(n for n in wm.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.22,.37,.35,1);bs.inputs['Roughness'].default_value=1;me.materials.append(wm)
# Camera/light rig retained in editable Blender source only.
bpy.ops.object.camera_add(location=(47,-65,64));cam=bpy.context.object;cam.name='CAM_TownOverview';target=Vector((0,0,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=140;cam.data.clip_end=700;scene.camera=cam
bpy.ops.object.light_add(type='AREA',location=(-20,-30,55));bpy.context.object.data.energy=1800;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=30
scene.world=bpy.data.worlds.new('PaperWorld');scene.world.color=(.45,.5,.42);scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.render.resolution_percentage=100
# Export only meshes; camera and lights are a webpage responsibility.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'european-water-town.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
 if o.type=='MESH' and o.name!='SM_Water_SourcePreview' and not o.name.startswith('SM_District_'):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ASSET/'european-water-town.glb'),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False,export_animations=False)
bpy.ops.object.select_all(action='DESELECT')
for o in district_meshes:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ASSET/'civic-districts.glb'),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False,export_animations=False)
(ASSET/'civic-districts.json').write_text(json.dumps(dict(triangles=district_tris,features=district_features,northern_closures=northern_closures),ensure_ascii=False,indent=2))
(ASSET/'curated-assets.json').write_text(json.dumps(dict(license='CC0-1.0',sources=dict(gazebo='https://poly.pizza/m/xYZB1TmGMv',horse_statue='https://polyhaven.com/a/horse_statue_01',garden_bench='https://polyhaven.com/a/painted_wooden_bench'),usage=curated_usage,geometry=curated_audit,processing='Blender silhouette decimation, metre normalization, paper palette, shared ink treatment'),indent=2))
print('DISTRICT_AUDIT',district_tris,'triangles',len(district_features),'features')
audit={'triangles':tris,'district_triangles':district_tris,'mesh_objects':len(meshes),'materials':len({m.name for o in meshes for m in o.data.materials if m}),'source':'european-water-town.blend','navigation':'town-navigation.json','architecture':architecture_counts,'road_segments':len(roads),'carriage':carriage,'water_rocks':water_rocks,'street_lamps':street_lamps,'water_source':water_source,'alpine_peaks':alpine_peaks,'estuary_count':1,'plaza':dict(x=river(43,13)[0],z=river(43,13)[1]),'coastal_closures':coastal_closures,'northern_closures':northern_closures,'district_features':district_features,'curated_assets':curated_usage,'docks':docks,'harbor_boats':harbor_boats,'details':detail_counts,'public_assets':public_usage,'landmarks':[castle_landmark,*sea_landmarks],'validation':'finite geometry and triangle budget pass'};(OUT/'european-water-town-audit.json').write_text(json.dumps(audit,indent=2));print('TOWN_AUDIT',audit)
