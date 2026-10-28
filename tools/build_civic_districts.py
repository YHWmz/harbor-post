"""Native Blender district additions. Executed by build_european_town.py with its shared palette/builders.
Geometry stays in its own export, while navigation and reuse metadata remain authoritative.
"""
district_features=[]
def feature(name,kind,x,z,w,d):
 wx,wz=river(x,z);district_features.append(dict(name=name,kind=kind,x=wx,z=wz,width=w,depth=d,base_x=x,base_z=z,ground=18.35 if kind=='summit_garden' else .35,footprint=[river(x+a*w/2,z+b*d/2) for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]))
def paving(x,z,w,d,y=.40):box(x,y,z,w,.045,d,'Path')
def hedge(x,z,w,d,y=.35):
 box(x,y+.38,z,w,.65,d,'Leaf');box(x,y+.045,z,w+.18,.12,d+.18,'Stone')
def blossom(x,y,z,r,mat,n=12):
 verts=[(x,y+.07,z)]+[(x+r*(1 if i%2==0 else .88)*math.cos(i*math.tau/n),y+.015*math.sin(i*2.1),z+r*(1 if i%2==0 else .88)*math.sin(i*math.tau/n)) for i in range(n)]
 add(verts,[(0,(i+1)%n+1,i+1) for i in range(n)],mat)
def parterre(x,z,w,d,y=.35):
 # Rounded clipped hedges, a recessed soil bed and separate soft flower clusters.
 r=min(.7,w*.2,d*.2);outline=[]
 for cx,cz,t in [(x+w/2-r,z+d/2-r,0),(x-w/2+r,z+d/2-r,90),(x-w/2+r,z-d/2+r,180),(x+w/2-r,z-d/2+r,270)]:
  for j in range(5):
   a=math.radians(t+j*22.5);outline.append((cx+r*math.cos(a),cz+r*math.sin(a)))
 inner=[(x+(a-x)*max(.3,(w-.48)/w),z+(b-z)*max(.3,(d-.48)/d)) for a,b in outline]
 add([(a,y+.1,b) for a,b in outline],[tuple(range(len(outline)-1,-1,-1))],'Meadow')
 for i,(a,b) in enumerate(outline):
  c,e=outline[(i+1)%len(outline)];f,g=inner[i];h,k=inner[(i+1)%len(inner)]
  add([(a,y+.12,b),(c,y+.12,e),(c,y+.5,e),(a,y+.5,b),(f,y+.5,g),(h,y+.5,k)],[(0,1,2,3),(3,2,5,4)],'Leaf')
 for j in range(12):
  col=j%3;row=j//3;phase=j*2.3+x*.7+z*.3
  xx=x+(col-1)*w*.23+.16*math.sin(phase);zz=z+(row-1.5)*d*.18+.13*math.cos(phase*1.7)
  radius=min(.42,w*.12,d*.14)*(1+.13*math.sin(phase))
  blossom(xx,y+.22,zz,radius*1.3,'Willow',8)
  blossom(xx+.07*math.sin(j),y+.32,zz+.08*math.cos(j),radius*.63,'Flowers' if j%3 else 'FlowersLavender',8)
  if j%4==0:blossom(xx+.10,y+.39,zz-.08,radius*.2,'Cream',6)
def garden_path(points,width=1.2,y=.44):
 sampled=[]
 for k in range(len(points)-1):
  p0=Vector(points[max(0,k-1)]);p1=Vector(points[k]);p2=Vector(points[k+1]);p3=Vector(points[min(len(points)-1,k+2)])
  for j in range(10):
   t=j/10;v=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t);sampled.append(v)
 sampled.append(Vector(points[-1]))
 for a,b in zip(sampled,sampled[1:]):
  v=b-a;n=Vector((-v.y,v.x)).normalized();h=width/2
  def pp(p,d,yy):return (p.x+n.x*d,yy,p.y+n.y*d)
  add([pp(a,-h,y),pp(b,-h,y),pp(b,h,y),pp(a,h,y)],[(0,1,2,3)],'Path')
  for side in [-1,1]:add([pp(a,side*h,y+.012),pp(b,side*h,y+.012),pp(b,side*(h+.065),y+.012),pp(a,side*(h+.065),y+.012)],[(0,1,2,3)],'Cream')
def ring_garden(x,z,rx,rz,y=.35):
 for i in range(28):
  a=i*math.tau/28;b=(i+1)*math.tau/28
  if min(abs(math.sin(a)),abs(math.cos(a)))<.2:continue
  def q(t,r,yy):return (x+(rx-r)*math.cos(t),yy,z+(rz-r)*math.sin(t))
  add([q(a,0,y+.08),q(b,0,y+.08),q(a,.08,y+.55),q(b,.08,y+.55),q(a,.4,y+.55),q(b,.4,y+.55),q(a,.48,y+.08),q(b,.48,y+.08)],[(0,1,3,2),(2,3,5,4),(4,5,7,6)],'Leaf')
  if i%4==0:
   xx=x+(rx-.7)*math.cos(a);zz=z+(rz-.7)*math.sin(a)
   blossom(xx,y+.36,zz,.5,'Flowers',8);blossom(xx+.18,y+.43,zz,.16,'Cream',6)
def urn(x,z,y=.4):
 cylinder(x,y+.12,z,.3,.24,'Stone',8);cylinder(x,y+.45,z,.20,.45,'Cream',8,.38);cylinder(x,y+.72,z,.42,.13,'Stone',10)
 foliage(x,y+.92,z,.40,'Leaf',.6);cylinder(x,y+1.04,z,.24,.10,'Flowers',7,.12)
def arbor(x,z):
 for dx in [-1.55,1.55]:
  for dz in [-.9,.9]:box(x+dx,1.65,z+dz,.15,2.6,.15,'Cream');box(x+dx,.55,z+dz,.35,.3,.35,'Stone')
 for dz in [-1.0,-.5,0,.5,1.0]:box(x,3.02,z+dz,3.7,.14,.12,'Wood')
 for dx in [-1.65,1.65]:box(x+dx,2.95,z,.14,.16,2.4,'Wood')
 for dx,dz in [(-1.4,-.8),(-1.4,.6),(1.4,-.5),(1.4,.8)]:foliage(x+dx,2.8,z+dz,.62,'Willow',.45)
 for dx in [-1.5,1.5]:cylinder(x+dx,2.9,z,.25,.12,'Flowers',7,.12)

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
 def arch(a,b,c,ww,hh,material,sign=1):
  rr=ww/2;cy=b+hh/2-rr
  vv=[p(a-rr,b-hh/2,c),p(a+rr,b-hh/2,c)]+[p(a+rr*math.cos(j*math.pi/10),cy+rr*math.sin(j*math.pi/10),c) for j in range(11)]
  add(vv,[tuple(range(len(vv))) if sign>0 else tuple(range(len(vv)-1,-1,-1))],material)
 def hiproof(a,c,ww,dd,hh,base):
  ridge=max(.6,ww/2-dd*.28);vv=[p(a-ww/2-.25,base,c-dd/2-.25),p(a+ww/2+.25,base,c-dd/2-.25),p(a+ww/2+.25,base,c+dd/2+.25),p(a-ww/2-.25,base,c+dd/2+.25),p(a-ridge,base+hh,c),p(a+ridge,base+hh,c)]
  add(vv,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],'Slate')
 def dressed_window(a,b,c,sign=1,shutters=False):
  arch(a,b,c,1.14,1.86,'Cream',sign);arch(a,b-.035,c+sign*.025,.91,1.58,'Ink',sign);arch(a,b-.035,c+sign*.045,.79,1.43,'Glass',sign)
  bx(a,b-.12,c+sign*.075,.045,1.35,.04,'Cream');bx(a,b-.14,c+sign*.08,.79,.045,.04,'Cream');bx(a,b-.99,c+sign*.02,1.35,.14,.25,'Stone');bx(a,b+.97,c+sign*.025,.22,.22,.15,'Stone')
  if shutters:
   for side in [-1,1]:
    panel(a+side*.73,b-.18,c+sign*.04,.24,1.4,'Sage',sign)
    for yy in [-.45,0,.45]:bx(a+side*.73,b-.18+yy,c+sign*.065,.25,.035,.025,'Cream')
 def chimney(a,c,y):
  bx(a,y+.6,c,.65,1.2,.8,'Stone');bx(a,y+1.2,c,.82,.18,.94,'Cream')
  for dx in [-.2,.2]:cylinder(*p(a+dx,y+1.5,c),.12,.5,'Roof',7)
 wall='Cream' if kind in ['hall','manor'] else 'Rose' if kind=='restaurant' else 'Plaster'
 bx(0,.6,0,w+.3,.5,d+.3,'Stone');bx(0,.85+h/2,0,w,h,d,wall);bx(0,.95+h,0,w+.4,.25,d+.4,'Cream')
 hiproof(0,0,w,d,2.3,h+1.1) if kind=='manor' else roof(0,0,w,d,1.7,h+1.1,'Roof' if kind in ['restaurant','winery'] else 'Slate')
 # Cornices, corners and varied facade rhythms read clearly at gameplay distance.
 for side in [-1,1]:bx(side*(w/2-.15),.9+h/2,d/2+.05,.3,h,.22,'Stone')
 floors=2 if h>5 else 1;columns=max(3,int(w/2))
 for floor in range(floors):
  yy=2.45+floor*2.75
  for k in range(columns):
   xx=-w/2+1+(w-2)*k/(columns-1)
   for sign in [-1,1]:
    if kind in ['manor','hall']:
     if not (floor==0 and sign==1 and abs(xx)<1.4):dressed_window(xx,yy,sign*(d/2+.07),sign,kind=='manor' and sign==1)
    else:
     panel(xx,yy,sign*(d/2+.03),.82,1.3,'Ink',sign);panel(xx,yy,sign*(d/2+.09),.68,1.15,'Glass',sign);bx(xx,yy+.72,sign*(d/2+.13),1.05,.12,.18,'Cream');bx(xx,yy,sign*(d/2+.14),.035,1.15,.03,'Cream')
 def side_window(a,b,c,sign):
  def face(xx,ww,hh,material):
   rr=ww/2;cy=b+hh/2-rr;vv=[p(xx,b-hh/2,c-rr),p(xx,b-hh/2,c+rr)]+[p(xx,cy+rr*math.sin(j*math.pi/8),c+rr*math.cos(j*math.pi/8)) for j in range(9)]
   add(vv,[tuple(range(len(vv)))],material)
  face(a,1.15,1.85,'Cream');face(a+sign*.035,.89,1.57,'Glass')
  bx(a+sign*.07,b-.12,c,.045,1.4,.045,'Cream');bx(a+sign*.07,b-.12,c,.045,.045,.89,'Cream');bx(a+sign*.02,b-1,c,.25,.14,1.35,'Stone')
 for side in [-1,1]:
  if kind in ['hall','manor']:
   for floor in ([0,1] if kind=='hall' else [1]):
    for k in [-1,1]:side_window(side*(w/2+.06),2.45+floor*2.75,k*d*.25,side)
   if kind=='manor':
    for zz in [-2.3,.6]:side_window(side*(w/2+4.27),2.65,zz,side)
  else:
   for k in [-1,1]:bx(side*(w/2+.05),2.2,k*d*.25,.08,1.2,.8,'Glass')
 if kind not in ['manor','hall']:bx(0,1.8,d/2+.13,1.25,2,.14,'Wood');bx(0,2.95,d/2+.3,1.8,.18,.65,'Cream')
 for j in range(3):bx(0,.4+j*.14,d/2+(1.6 if kind in ['manor','hall'] else .8)-j*.2,4.8 if kind in ['manor','hall'] else 2.2,.14,1.6-j*.3,'Stone')
 if kind=='manor':
  for side in [-1,1]:
   a=side*(w/2+2.1);bx(a,2.5,-.7,4.3,4.2,d-1,'Plaster');hiproof(a,-.7,4.3,d-1,1.6,4.7)
   for dx in [-1.0,1.0]:dressed_window(a+dx,2.65,(d-1)/2-.7+.05,1,True)
  # A hipped slate roof, dormers and paired chimneys give the estate its own silhouette.
  for a in [-3.7,0,3.7]:
   bx(a,h+2.1,2.45,1.45,1.3,1.25,'Cream');roof(a,2.45,1.55,1.4,.6,h+2.8);panel(a,h+2.15,3.10,.75,.9,'Glass',1);bx(a,h+2.15,3.13,.04,.9,.035,'Cream')
  for a in [-4.7,4.7]:chimney(a,-1.4,h+2.4)
  for a in [-1.8,1.8]:
   cylinder(*p(a,2.35,d/2+1.15),.14,2.9,'Cream',8);bx(a,.86,d/2+1.15,.42,.18,.42,'Stone');bx(a,3.85,d/2+1.15,.45,.18,.45,'Stone')
  arch(0,2.0,d/2+.2,1.7,2.35,'Cream');arch(0,1.96,d/2+.24,1.42,2.12,'Wood');bx(0,1.7,d/2+.28,.04,1.8,.04,'Cream')
  bx(0,3.55,d/2+.06,w,.12,.13,'Stone');bx(0,6.85,d/2+.06,w,.14,.18,'Cream')
  for a in [-(w/2-.18),w/2-.18]:
   for yy in [1.2,1.9,2.6,3.3,4.2,4.9,5.6,6.3]:bx(a,yy,d/2+.1,.32,.22,.18,'Stone')
  bx(0,4.1,d/2+.65,4.4,.16,1.5,'Stone')
  for k in range(7):ln((-2+k*.66,4.15,d/2+1.35),(-2+k*.66,4.85,d/2+1.35),.035,'Ink')
  ln((-2.2,4.85,d/2+1.35),(2.2,4.85,d/2+1.35),.045,'Ink')
 elif kind=='hall':
  # Clock tower and columned civic porch, built from the same paper palette.
  bx(0,h+3.0,-.5,2.8,5.8,3,'Cream');roof(0,-.5,3.1,3.3,2.2,h+6.1)
  for yy in [h+.3,h+1.1,h+5.7]:bx(0,yy,-.5,3.2,.16,3.35,'Stone')
  for a in [-4.1,4.1]:chimney(a,-1.0,h+1.1)
  face=p(0,h+3.95,1.06)
  vv=[p(.85*math.cos(i*math.tau/16),h+3.95+.85*math.sin(i*math.tau/16),1.06) for i in range(16)]
  add(vv,[tuple(range(16))],'Ink');add([p(.74*math.cos(i*math.tau/16),h+3.95+.74*math.sin(i*math.tau/16),1.08) for i in range(16)],[tuple(range(16))],'Cream')
  for k in range(12):
   angle=k*math.tau/12;ln((.59*math.sin(angle),h+3.95+.59*math.cos(angle),1.12),(.68*math.sin(angle),h+3.95+.68*math.cos(angle),1.12),.023,'Ink')
  ln((0,h+3.95,1.11),(0,h+4.45,1.11),.035,'Ink');ln((0,h+3.95,1.11),(.4,h+3.75,1.11),.035,'Ink')
  bx(0,3.9,d/2+1.05,5.8,.3,2.2,'Stone')
  for a in [-2.35,-.8,.8,2.35]:
   cylinder(*p(a,2.1,d/2+1.65),.15,3.3,'Cream',8);bx(a,.5,d/2+1.65,.44,.2,.44,'Stone')
  roof(0,d/2+1.05,5.8,2.2,1.15,4.1,'Slate')
  add([p(-2.4,4.25,d/2+2.43),p(2.4,4.25,d/2+2.43),p(0,5.14,d/2+2.43)],[(0,1,2)],'Cream')
  for a in [-.9,.9]:arch(a,2,d/2+.19,1.35,2.3,'Cream');arch(a,1.98,d/2+.23,1.1,2.05,'Wood')
  for yy in [3.6,6.6]:bx(0,yy,d/2+.07,w,.16,.16,'Stone')
  for a in [-(w/2-.12),w/2-.12]:
   for yy in [1.3,2.2,3.1,4.0,4.9,5.8]:bx(a,yy,d/2+.09,.25,.25,.2,'Stone')
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
hedge(75,-51,31,.7)
for xx in [65.7,84.3]:hedge(xx,-34.8,12.4,.7)
for xx in [73,77]:
 box(xx,1.25,-34.8,.55,1.8,.55,'Cream');cylinder(xx,2.28,-34.8,.4,.3,'Stone',8,.16)
for xx in [60.5,89.5]:urn(xx,-51.5)
arbor(60.5,-43)
garden_path([(60,-52.6),(57.5,-48),(58,-43),(58,-38),(62,-34)],1.1)
garden_path([(88,-52.6),(92,-48),(92.5,-42),(91.5,-37),(88,-34)],1.1)
public_asset('fountain-round-detail',75,-43,1.15)
ring_garden(75,-43,4.8,3.8)
for xx,zz in [(73.5,-33.7),(76.5,-33.7)]:urn(xx,zz)
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
box(82,.7,18,1.45,.6,1.45,'Stone');box(82,1.08,18,1.15,.16,1.15,'Cream');curated_asset('horse_statue',82,18,2.15,rotation=math.pi/2,y=1.16)
for xx in [75,89]:urn(xx,17.7)
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

# Distinct public gardens: curving walks, reading courts and a rose pergola.
park_index=0
for side in [-1,1]:
 for zmid in [-12.5,12.5,37]:
  if side==1 and zmid==12.5:continue
  xx=side*85;park_index+=1
  if park_index in [1,4]:
   garden_path([(xx-12,zmid+3),(xx-8,zmid-2),(xx-1,zmid-3),(xx+6,zmid+2),(xx+12,zmid-2)],1.35)
   curated_asset('gazebo',xx+2,zmid-1,4.8,y=.40)
   ring_garden(xx-7,zmid+2,3.0,2.0)
  elif park_index==2:
   garden_path([(xx-12,zmid),(xx-6,zmid-3),(xx,zmid),(xx+6,zmid+3),(xx+12,zmid)],1.3)
   arbor(xx,zmid)
   for dx,dz in [(-7,2.5),(7,-2.5)]:parterre(xx+dx,zmid+dz,4.5,3)
  else:
   garden_path([(xx-12,zmid-2),(xx-5,zmid),(xx+3,zmid+2),(xx+12,zmid)],1.3)
   for dx,dz in [(-7,2.7),(7,-2.7)]:parterre(xx+dx,zmid+dz,4.5,3)
   if park_index==5:public_asset('fountain-round-detail',xx,zmid-1,.85)
  for dx in [-11,11]:tree(xx+dx,zmid,.9)
  if park_index in [1,2,4]:curated_asset('garden_bench',xx-3,zmid+4.0,1.8,rotation=math.pi)
  else:public_asset('stall-bench',xx-3,zmid+1.6,.85)
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
