"""Shared meter-scale terrain, snowmelt channel and shoreline definitions for Blender.
No bpy dependency: geometry exports and navigation checks use the same surface.
"""
import math
PEAKS=[dict(name='WestShoulder',x=-2,z=-125,height=36,rx=23,rz=27),dict(name='SnowmeltPeak',x=34,z=-139,height=54,rx=26,rz=27),dict(name='EastSummit',x=78,z=-124,height=42,rx=25,rz=29)]
MIN_X,MAX_X,MIN_Z,SHORE_Z=-32,108,-174,-82

def smooth(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3-2*t)

def river(x,z):
 return (x+math.tanh(x*.2)*max(0,z-32)*.25*math.exp(-abs(x)/45)+6.5*math.sin(z*.07)+2*math.sin(z*.16+.6)+2.2*math.sin(x*.17+z*.065),z+4.5*math.sin(x*.07+1)+2*math.sin(x*.145-z*.045)+1.2*math.sin(z*.14))

def center_x(z):
 return 24+5.7*math.sin((-z-82)*.115)*smooth(0,14,-z-82)

def channel_width(z):
 # A thin headwater opens into a small alluvial inlet instead of a uniform gutter.
 return .65+1.35*smooth(0,64,z+142)+1.0*smooth(-85,-78,z)

def raw_height(x,z):
 peak=max(p['height']*math.exp(-((x-p['x'])/p['rx'])**2-((z-p['z'])/p['rz'])**2) for p in PEAKS)
 shoulder=(.65*math.sin(x*.21+z*.09)+.45*math.sin(z*.26-x*.14))*min(1,peak/9)
 fade=smooth(0,25,-82-z)
 lateral=smooth(MIN_X,MIN_X+13,x)*(1-smooth(MAX_X-16,MAX_X,x))
 rear=smooth(MIN_Z,MIN_Z+14,z)
 return .35+max(0,peak+shoulder)*fade*lateral*rear

# Sample upstream to downstream and remove tiny uphill undulations from the bed.
PROFILE=[]
previous=float('inf')
for i in range(97):
 z=-142+i*(64/96);x=center_x(z)
 raw=.10+(raw_height(x,z)-.35)*.84 if z<=-82 else .10-(z+82)*.0675
 y=min(raw,previous-.002);previous=y
 PROFILE.append(dict(x=x,y=y,z=z,width=channel_width(z)))

def bed_height(z):
 t=max(0.,min(96.,(z+142)*1.5));i=min(95,int(t));f=t-i
 return PROFILE[i]['y']*(1-f)+PROFILE[i+1]['y']*f

def terrain_height(x,z):
 h=raw_height(x,z)
 if -144<=z<=-78:
  d=abs(x-center_x(z));w=channel_width(z);blend=1-smooth(w*.85,w+4.2,d)
  # Exact channel floor: both the creek ribbon and mountain mesh derive from this bed.
  h=h*(1-blend)+bed_height(z)*blend
 return h

def snowline(x,z):return 30.5+2.0*math.sin(x*.19)+1.5*math.sin(z*.13+x*.07)
