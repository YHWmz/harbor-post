"""Verify the exported near mountains and creek share the exact physical valley floor."""
import sys,json,struct,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from alpine_terrain import PROFILE,PEAKS,river,terrain_height,snowline
nav=json.loads((ROOT/'dist/assets/town-navigation.json').read_text());meta=json.loads((ROOT/'dist/assets/alpine-terrain.json').read_text())
assert len(PEAKS)==len(nav['alpine_peaks'])==3
assert PROFILE[0]['y']>35,'headwater must start in the actual high mountains'
assert PROFILE[0]['y']>snowline(PROFILE[0]['x'],PROFILE[0]['z']),'headwater starts above the snowline'
assert PROFILE[-1]['y']<0
assert all(PROFILE[i]['y']>PROFILE[i+1]['y'] for i in range(len(PROFILE)-1))
assert 1500<meta['triangles']<15000
blob=(ROOT/'dist/assets/painted-hills.glb').read_bytes();n=struct.unpack_from('<I',blob,12)[0];doc=json.loads(blob[20:20+n]);start=20+n+8
mesh=next(m for m in doc['meshes'] if m['name']=='GEO_LakesideAlps');points=[]
for primitive in mesh['primitives']:
 a=doc['accessors'][primitive['attributes']['POSITION']];v=doc['bufferViews'][a['bufferView']];offset=start+v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',12)
 points.extend(struct.unpack_from('<3f',blob,offset+i*stride) for i in range(a['count']))
assert max(p[1] for p in points)>48,'the nearby peaks are real exported geometry'
for i in range(0,91,3):
 p=PROFILE[i];x,z=river(p['x'],p['z']);floor=min(points,key=lambda v:math.hypot(v[0]-x,v[2]-z))
 assert math.hypot(floor[0]-x,floor[2]-z)<.001,'mountain mesh includes the exact creek cross-section'
 assert abs(floor[1]-p['y'])<.001,'the stream floor is cut into the mountain mesh'
 assert abs(nav['water_source'][i]['y']-floor[1]-.025)<.001,'flow sits above the real valley floor, with no floating trough'
for p in nav['alpine_peaks']:assert p['z']<-110 and p['y']>30
print('PASS three lake-side peaks, snow-line headwater at %.1fm, shared exported valley floor, downhill flow, %s mountain triangles'%(PROFILE[0]['y'],meta['triangles']))
