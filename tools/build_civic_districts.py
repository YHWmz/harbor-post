"""Native Blender district additions. Executed by build_european_town.py with its shared palette/builders.
Geometry stays in its own export, while navigation and reuse metadata remain authoritative.
"""
district_features=[]
def feature(name,kind,x,z,w,d):
 wx,wz=river(x,z);district_features.append(dict(name=name,kind=kind,x=wx,z=wz,width=w,depth=d,base_x=x,base_z=z,ground=18.35 if kind=='summit_garden' else .35,footprint=[river(x+a*w/2,z+b*d/2) for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]))
def paving(x,z,w,d,y=.40):box(x,y,z,w,.045,d,'Path')
def hedge(x,z,w,d,y=.35):
 box(x,y+.38,z,w,.65,d,'Leaf');box(x,y+.045,z,w+.18,.12,d+.18,'Stone')
def parterre(x,z,w,d,y=.35):
 box(x,y+.05,z,w,.10,d,'Wood');box(x,y+.12,z,w-.22,.06,d-.22,'Rose')
 for side in [-1,1]:box(x+side*(w/2-.15),y+.26,z,.25,.3,d,'Leaf')
 for side in [-1,1]:box(x,y+.26,z+side*(d/2-.15),w,.3,.25,'Leaf')
 for k in range(3):cylinder(x+(k-1)*w*.25,y+.4,z,.28,.16,'Flowers',5,.12)
def building(cx,cz,w=10,d=7,h=6,rot=0,kind='manor'):
 global rigid
 old=rigid;wx,wz=river(cx,cz);rigid=(cx,cz,rot,wx,wz,heading(cx,cz,rot))
 def p(a,b,c):return (cx+math.cos(rot)*a+math.sin(rot)*c,b,cz-math.sin(rot)*a+math.cos(rot)*c)
 def bx(a,b,c,ww,hh,dd,m):box(*p(a,b,c),ww,hh,dd,m,rot)
 def ln(a,b,r=.035,m='Cream'):tube(p(*a),p(*b),r,m,5)
 def panel(a,b,c,ww,hh,m,sign):
  add([p(a-ww/2,b-hh/2,c),p(a+ww/2,b-hh/2,c),p(a+ww/2,b+hh/2,c),p(a-ww/2,b+hh/2,c)],[(0,1,2,3) if sign>0 else (3,2,1,0)],m)
 def roof(a,c,ww,dd,hh,base,mat='Slate'):
  verts=[p(a+u,yy,c+v) for v in [-dd/2-.25,dd/2+.25] for u,yy in [(-ww/2-.25,base),(0,base+hh),(ww/2+.25,base)]]
  add(verts,[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)],mat)
 wall='Cream' if kind in ['hall','manor'] else 'Rose' if kind=='restaurant' else 'Plaster'
 bx(0,.6,0,w+.3,.5,d+.3,'Stone');bx(0,.85+h/2,0,w,h,d,wall);bx(0,.95+h,0,w+.4,.25,d+.4,'Cream')
 roof(0,0,w,d,2.3 if kind=='manor' else 1.7,h+1.1,'Roof' if kind in ['restaurant','winery'] else 'Slate')
 # Cornices, corners and varied facade rhythms read clearly at gameplay distance.
 for side in [-1,1]:bx(side*(w/2-.15),.9+h/2,d/2+.05,.3,h,.22,'Stone')
 floors=2 if h>5 else 1;columns=max(3,int(w/2))
 for floor in range(floors):
  yy=2.2+floor*2.45
  for k in range(columns):
   xx=-w/2+1+(w-2)*k/(columns-1)
   for sign in [-1,1]:
    panel(xx,yy,sign*(d/2+.03),.82,1.3,'Ink',sign);panel(xx,yy,sign*(d/2+.09),.68,1.15,'Lamplight' if k%3==0 else 'Glass',sign);bx(xx,yy+.72,sign*(d/2+.13),1.05,.12,.18,'Cream');bx(xx,yy,sign*(d/2+.14),.035,1.15,.03,'Cream')
 for side in [-1,1]:
  for k in [-1,1]:bx(side*(w/2+.05),2.2,k*d*.25,.08,1.2,.8,'Glass')
 bx(0,1.8,d/2+.13,1.25,2,.14,'Wood');bx(0,2.95,d/2+.3,1.8,.18,.65,'Cream')
 for j in range(3):bx(0,.4+j*.14,d/2+.8-j*.2,2.2,.14,1.2-j*.25,'Stone')
 if kind=='manor':
  for side in [-1,1]:
   a=side*(w/2+2.1);bx(a,2.5,-.7,4.3,4.2,d-1,'Plaster');roof(a,-.7,4.3,d-1,1.6,4.7)
  # Raised central dormer and a low balcony distinguish the manor from town houses.
  bx(0,h+1.65,d*.25,2.8,1.8,2.7,'Cream');roof(0,d*.25,2.8,2.7,1.1,h+2.55)
  bx(0,4.1,d/2+.65,4.4,.16,1.5,'Stone')
  for k in range(7):ln((-2+k*.66,4.15,d/2+1.35),(-2+k*.66,4.85,d/2+1.35),.035,'Ink')
  ln((-2.2,4.85,d/2+1.35),(2.2,4.85,d/2+1.35),.045,'Ink')
 elif kind=='hall':
  # Clock tower and columned civic porch, built from the same paper palette.
  bx(0,h+2.4,-.5,2.8,4.6,3,'Cream');roof(0,-.5,3.1,3.3,2.2,h+4.9)
  face=p(0,h+2.65,1.06)
  vv=[p(.85*math.cos(i*math.tau/16),h+2.65+.85*math.sin(i*math.tau/16),1.06) for i in range(16)]
  add(vv,[tuple(range(16))],'Ink');add([p(.74*math.cos(i*math.tau/16),h+2.65+.74*math.sin(i*math.tau/16),1.08) for i in range(16)],[tuple(range(16))],'Cream')
  ln((0,h+2.65,1.11),(0,h+3.15,1.11),.035,'Ink');ln((0,h+2.65,1.11),(.4,h+2.45,1.11),.035,'Ink')
  bx(0,3.9,d/2+1.05,5.8,.3,2.2,'Stone')
  for a in [-2.35,-.8,.8,2.35]:
   cylinder(*p(a,2.1,d/2+1.65),.15,3.3,'Cream',8);bx(a,.5,d/2+1.65,.44,.2,.44,'Stone')
  roof(0,d/2+1.05,5.8,2.2,.8,4.1,'Roof')
 elif kind=='restaurant':
  # Striped canvas over the lake-facing dining facade.
  for k in range(8):
   aa=-w/2+k*w/8
   add([p(aa,3.45,d/2),p(aa+w/8,3.45,d/2),p(aa+w/8,2.9,d/2+2.2),p(aa,2.9,d/2+2.2)],[(0,1,2,3)],'Cream' if k%2 else 'Rose')
  for a in [-w/2,w/2]:ln((a,.45,d/2+2.2),(a,2.95,d/2+2.2),.05,'Wood')
 else:
  bx(w*.3,1.9,d/2+.25,1.3,1.1,.18,'Wood')
 rigid=old
 return feature({'manor':'湖畔庄园','hall':'市政厅','restaurant':'湖畔餐厅','winery':'城堡酒庄'}.get(kind,'花园会馆'),kind,cx,cz,abs(math.cos(rot))*w+abs(math.sin(rot))*d,abs(math.sin(rot))*w+abs(math.cos(rot))*d)
def dining_table(x,z,y=.4):
 cylinder(x,y+.85,z,.7,.12,'Wood',10);tube((x,y,z),(x,y+.85,z),.08,'Ink',5)
 for s in [-1,1]:
  box(x+s*.95,y+.42,z,.48,.1,.52,'Wood');box(x+s*1.13,y+.75,z,.1,.65,.52,'Wood')
  for zz in [-.2,.2]:tube((x+s*.95,y,z+zz),(x+s*.95,y+.4,z+zz),.035,'Ink',4)
 # Paper canvas parasol, not a flat colored disc.
 cylinder(x,y+2.3,z,1.25,.4,'Cream',8,.08);tube((x,y+.85,z),(x,y+2.6,z),.035,'Wood',5)

# EAST LAKE ESTATE: occupies the large empty shore, not the open lake.
building(75,-61,13,8,6.5,kind='manor');paving(75,-52.6,23,3)
paving(75,-43,2.4,17);paving(75,-43,31,2)
for xx in [64,69,81,86]:
 for zz in [-48,-38]:parterre(xx,zz,4.1,5.5)
for xx in [59,91]:hedge(xx,-43,1,16)
for zz in [-51,-34.8]:hedge(75,zz,31,.7)
public_asset('fountain-round-detail',75,-43,1.0)
for xx,zz in [(61,-43),(89,-43),(69,-52),(81,-52)]:public_asset('stall-bench',xx,zz,1)
# Orchard and productive kitchen gardens carry detail to the eastern boundary.
for xx in [86,93]:
 for zz in [-77,-70,-63]:tree(xx,zz,.95)
for xx in [64,70,76,82]:
 for zz in [-80,-74]:parterre(xx,zz,3.7,2.5)
paving(85,-70,1.5,24);paving(71,-71,28,1.5)
feature('庄园花园','formal_garden',75,-43,31,17)
feature('庄园果园与菜圃','orchard',79,-74,31,16)

# LAKESIDE RESTAURANT: terrace stays inland from the curved shore.
building(55,-75,8,6,4.2,rot=-math.pi/2,kind='restaurant')
paving(48.8,-75,6,10)
for xx in [47.5,50.5]:
 for zz in [-78,-72]:dining_table(xx,zz)
paving(58,-75,1.4,18);paving(65,-61,13,1.6)
feature('餐厅露台','dining_terrace',49,-75,6,10)

# TOWN HALL AND PUBLIC COURT: a civic landmark integrated with the outer town street.
building(82,11.2,11,6,6.6,kind='hall')
paving(82,18,22,3.5);paving(73,12,2.1,12);paving(67,12,10,1.8)
for xx in [72.5,91.5]:
 for zz in [8.1,18]:parterre(xx,zz,2.3,1.6)
for xx in [76,88]:public_asset('stall-bench',xx,19,1)
feature('市政厅前庭','civic_court',82,17.5,22,4)

# WESTERN CLOSURE: the old sea mouth becomes vineyard, winery and a garden promenade.
building(-88,-25,7.6,5.2,4.3,kind='winery');paving(-88,-20.8,16,2)
paving(-78.5,-25,1.8,14);paving(-88,-31.5,21,1.5)
for xx in [-98,-94,-83]:
 for zz in [-31,-18]:parterre(xx,zz,2.7,2)
for xx in [-98,-94,-90,-86]:
 for zz in [-42,-36]:tree(xx,zz,.85)
for xx in [-98,-95,-92]:
 hedge(xx,-49,1,9)
 for zz in [-52,-49,-46]:
  tube((xx,.4,zz),(xx,1.65,zz),.04,'Wood',4);foliage(xx,1.25,zz,.35,'Willow',.6)
feature('西岸葡萄园','vineyard',-94,-48,12,13)
feature('封口花园','closure_garden',-88,-25,29,17)

# Smaller landscaped courtyards replace the other long bare outer lawns.
for side in [-1,1]:
 for zmid in [-12.5,12.5,37]:
  if side==1 and zmid==12.5:continue # City hall occupies this court.
  xx=side*85
  paving(xx,zmid,24,1.5);paving(xx,zmid,1.4,10)
  for dx in [-7,7]:
   for dz in [-3.5,3.5]:parterre(xx+dx,zmid+dz,5,3.2)
  for dx in [-11,11]:tree(xx+dx,zmid,.9)
  public_asset('stall-bench',xx-3,zmid+1.6,.85)
  feature('街区庭园','neighborhood_garden',xx,zmid,25,11)
# A south-west garden cafe and quiet dining court break up the seaside lawn.
building(-84,37,7,5,3.8,kind='restaurant')
for xx in [-90,-78]:dining_table(xx,37)

# Castle-side formal planting follows the real 18.35m summit, clear of the coach road.
for zz in [-90,-81,-72,-63]:
 parterre(-83,zz,3.8,4.8,y=18.35)
paving(-80,-77,1.0,29,y=18.43)
for zz in [-87,-69]:public_asset('stall-bench',-85.4,zz,.85,math.pi/2,y=18.4)
feature('崖顶玫瑰庭园','summit_garden',-83,-77,6,31)
detail_counts.update(manors=1,restaurants=2,town_halls=1,wineries=1,formal_gardens=1,neighborhood_gardens=5,summit_gardens=1)
