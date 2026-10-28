// Collision-aware land graph exported by Blender, including bridge and mountain-road levels.
let world=null,cells=new Map(),cachedLanding=null;
export function setWalkingWorld(data){world=data;cells=new Map();for(const [cell,y] of data.nodes){const a=cells.get(cell)||[];a.push(y/100);cells.set(cell,a);}cachedLanding=null;return world;}
export function walkingWorld(){return world;}
export function surfaceAt(x,z,height=.4,maxRise=.66){
 if(!world)return null;const gx=Math.round((x-world.minX)/world.step),gz=Math.round((z-world.minZ)/world.step);if(gx<0||gz<0||gx>=world.nx||gz>=world.nz)return null;
 const ys=cells.get(gx+gz*world.nx);if(!ys)return null;let y=null,d=Infinity;for(const h of ys){if(Math.abs(h-height)<=maxRise&&Math.abs(h-height)<d){y=h;d=Math.abs(h-height);}}return y===null?null:{x,z,y};
}
export function findLanding(boat,maxDistance=4.2){
 if(!world||Math.abs(boat.speed||0)>.85)return null;
 if(cachedLanding&&cachedLanding.maxDistance===maxDistance&&Math.hypot(boat.x-cachedLanding.boatX,boat.z-cachedLanding.boatZ)<.05)return cachedLanding.point;
 let best=null,d=maxDistance;const gx=Math.round((boat.x-world.minX)/world.step),gz=Math.round((boat.z-world.minZ)/world.step),r=Math.ceil(maxDistance/world.step);
 for(let dz=-r;dz<=r;dz++)for(let dx=-r;dx<=r;dx++){
  const xx=gx+dx,zz=gz+dz;if(xx<0||zz<0||xx>=world.nx||zz>=world.nz)continue;
  const ys=cells.get(xx+zz*world.nx);if(!ys)continue;const x=world.minX+xx*world.step,z=world.minZ+zz*world.step,dist=Math.hypot(x-boat.x,z-boat.z);
  if(dist>=d)continue;const y=ys.find(h=>h>=.25&&h<=1.0);if(y!==undefined){best={x,z,y,heading:Math.atan2(x-boat.x,z-boat.z),speed:0};d=dist;}
 }
 cachedLanding={maxDistance,boatX:boat.x,boatZ:boat.z,point:best};return best;
}
export function canReturnToBoat(walker,boat){return walker.y<1.1&&Math.hypot(walker.x-boat.x,walker.z-boat.z)<4.2;}
export function canDeliverOnFoot(walker,stop){const landing=findLanding({...stop,speed:0},12);return landing&&Math.hypot(walker.x-landing.x,walker.z-landing.z)<2.4&&Math.abs(walker.y-landing.y)<.8;}
export function stepWalker(state,input,dt){
 dt=Math.min(.05,Math.max(0,dt));let {x,y,z,heading}=state;heading+=((input.left?1:0)-(input.right?1:0))*2.2*dt;
 const throttle=Number(!!input.forward)-Number(!!input.back),speed=input.brake?0:throttle*(input.slow?4.6:2.6);const dx=Math.sin(heading)*speed*dt,dz=Math.cos(heading)*speed*dt;
 let moved=0;const count=Math.max(1,Math.ceil(Math.hypot(dx,dz)/.09));
 for(let i=0;i<count;i++){
  let next=surfaceAt(x+dx/count,z+dz/count,y);
  if(next){x=next.x;z=next.z;y=next.y;moved+=Math.hypot(dx,dz)/count;continue;}
  next=surfaceAt(x+dx/count,z,y);if(next){x=next.x;y=next.y;moved+=Math.abs(dx)/count;}
  next=surfaceAt(x,z+dz/count,y);if(next){z=next.z;y=next.y;moved+=Math.abs(dz)/count;}
 }
 return {x,y,z,heading,speed:dt?Math.sign(speed)*moved/dt:0,hit:!!speed&&moved<Math.hypot(dx,dz)*.2};
}
// Optional pedestrian chart route. Failure is explicit: never draw a line over water.
export function planWalkRoute(from,to){
 if(!world)return [];const point=(cell,y)=>({x:world.minX+(cell%world.nx)*world.step,z:world.minZ+Math.floor(cell/world.nx)*world.step,y});
 const key=(c,y)=>c+':'+y,nearest=p=>{let best=null,d=Infinity;for(const [cell,ys] of cells){const q=point(cell,0),dd=(q.x-p.x)**2+(q.z-p.z)**2;if(dd>d)continue;for(const y of ys){const score=dd+((y-(p.y||.4))*3)**2;if(score<d){d=score;best={cell,y};}}}return best;};
 const a=nearest(from),b=nearest(to);if(!a||!b)return [];const ak=key(a.cell,a.y),bk=key(b.cell,b.y),queue=[a],prev=new Map([[ak,null]]);let goal=null;
 for(let head=0;head<queue.length;head++){
  const n=queue[head],nk=key(n.cell,n.y);if(nk===bk){goal=n;break;}
  for(const dc of [1,-1,world.nx,-world.nx]){const cell=n.cell+dc;if(Math.abs(dc)===1&&Math.floor(cell/world.nx)!==Math.floor(n.cell/world.nx))continue;for(const y of cells.get(cell)||[]){const k=key(cell,y);if(Math.abs(y-n.y)>.65||prev.has(k))continue;prev.set(k,n);queue.push({cell,y});}}
 }
 if(!goal)return [];const out=[];for(let n=goal;n;n=prev.get(key(n.cell,n.y)))out.push(point(n.cell,n.y));return out.reverse();
}
