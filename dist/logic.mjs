import {WORLD_BOUNDS,BANKS,DOCKS,BRIDGE,STOPS,DELIVERY_COUNT,SPAWN} from './world.mjs';
export {WORLD_BOUNDS,BANKS,DOCKS,BRIDGE,STOPS,DELIVERY_COUNT,SPAWN};
export function circleBox(x,z,r,b){const dx=x-Math.max(b.minX,Math.min(x,b.maxX)),dz=z-Math.max(b.minZ,Math.min(z,b.maxZ));return dx*dx+dz*dz<r*r;}
export function circlePolygon(x,z,r,poly){let inside=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){
 const [ax,az]=poly[i],[bx,bz]=poly[j];if((az>z)!==(bz>z)&&x<(bx-ax)*(z-az)/(bz-az)+ax)inside=!inside;
 const dx=bx-ax,dz=bz-az,t=Math.max(0,Math.min(1,((x-ax)*dx+(z-az)*dz)/(dx*dx+dz*dz)));if(Math.hypot(x-ax-t*dx,z-az-t*dz)<r)return true;
 }return inside;}
function polygonBlocked(x,z,r,b){if(b.minX!==undefined&&(x<b.minX-r||x>b.maxX+r||z<b.minZ-r||z>b.maxZ+r))return false;return circlePolygon(x,z,r,b.polygon);}
export function obstacles(bridgeOpen=true){return [...BANKS,...DOCKS,...(bridgeOpen?[]:[BRIDGE])];}
export function boatBlocked(x,z,heading,boxes=obstacles()){
 if(x<WORLD_BOUNDS.minX||x>WORLD_BOUNDS.maxX||z<WORLD_BOUNDS.minZ||z>WORLD_BOUNDS.maxZ)return true;
 for(const offset of [-1.07,0,1.07]){const px=x+Math.sin(heading)*offset,pz=z+Math.cos(heading)*offset;if(boxes.some(b=>b.polygon?polygonBlocked(px,pz,.86,b):circleBox(px,pz,.86,b)))return true;}return false;
}
export const DEFAULT_SPEED_SCALE=1.5;
export function normalizeSpeedScale(value){if(value===null||value==='')return DEFAULT_SPEED_SCALE;const n=Number(value);return Number.isFinite(n)?Math.max(.75,Math.min(2.5,n)):DEFAULT_SPEED_SCALE;}
export function stepBoat(state,input,dt,boxes=obstacles(),speedScale=DEFAULT_SPEED_SCALE){
 speedScale=normalizeSpeedScale(speedScale);
 dt=Math.min(.05,Math.max(0,dt));let {x,z,heading,speed}=state;const throttle=(input.forward?1:0)-(input.back?1:0);
 speed+=throttle*(throttle*speed<0?5:2.5)*speedScale*dt;speed*=Math.exp(-(throttle?.35:1.5)*dt);speed=Math.max(-1.1*speedScale,Math.min(input.slow?1.5:5.4*speedScale,speed));if(input.brake)speed*=Math.exp(-8*dt);
 const steering=(input.left?1:0)-(input.right?1:0);const nh=heading+steering*(speed<-.08?-1:1)*(.30+.70*Math.min(1,Math.abs(speed)/.5))*1.1*dt;
 if(!boatBlocked(x,z,nh,boxes))heading=nh;
 const nx=x+Math.sin(heading)*speed*dt,nz=z+Math.cos(heading)*speed*dt;let hit=false;
 if(!boatBlocked(nx,nz,heading,boxes)){x=nx;z=nz;}else{hit=true;speed*=.25;if(!boatBlocked(nx,z,heading,boxes))x=nx;if(!boatBlocked(x,nz,heading,boxes))z=nz;}
 return {x,z,heading,speed,hit};
}
export function canDeliver(state,stop){return Math.hypot(state.x-stop.x,state.z-stop.z)<1.48&&Math.abs(state.speed)<.85;}
export function restoreProgress(data){if(!data||data.version!==6)return {index:0};return {index:Math.min(DELIVERY_COUNT+1,Math.max(0,Math.floor(Number(data.index)||0)))};}
// Cached world-scale occupancy grid and a binary-heap A* search.
const grids=new Map();
function navigationGrid(boxes){const key=JSON.stringify(boxes);if(grids.has(key))return grids.get(key);const step=.65,minX=WORLD_BOUNDS.minX+1.6,minZ=WORLD_BOUNDS.minZ+1.6,nx=Math.floor((WORLD_BOUNDS.maxX-minX-1.6)/step)+1,nz=Math.floor((WORLD_BOUNDS.maxZ-minZ-1.6)/step)+1,clear=new Uint8Array(nx*nz);
 for(let id=0;id<clear.length;id++){const x=minX+(id%nx)*step,z=minZ+Math.floor(id/nx)*step;clear[id]=!boxes.some(b=>b.polygon?polygonBlocked(x,z,1.8,b):circleBox(x,z,1.8,b));}
 const grid={step,minX,minZ,nx,nz,clear};grids.set(key,grid);return grid;}
export function planRoute(from,to,boxes=obstacles(true)){
 const {step,minX,minZ,nx,nz,clear}=navigationGrid(boxes),pos=id=>({x:minX+(id%nx)*step,z:minZ+Math.floor(id/nx)*step});
 function nearest(p){const x=Math.max(0,Math.min(nx-1,Math.round((p.x-minX)/step))),z=Math.max(0,Math.min(nz-1,Math.round((p.z-minZ)/step)));if(clear[x+z*nx])return x+z*nx;for(let r=1;r<15;r++){let best=-1,d=Infinity;for(let dz=-r;dz<=r;dz++)for(let dx=-r;dx<=r;dx++){if(Math.abs(dx)!==r&&Math.abs(dz)!==r)continue;const xx=x+dx,zz=z+dz;if(xx<0||zz<0||xx>=nx||zz>=nz||!clear[xx+zz*nx])continue;const dd=dx*dx+dz*dz;if(dd<d){best=xx+zz*nx;d=dd;}}if(best>=0)return best;}return -1;}
 const start=nearest(from),goal=nearest(to);if(start<0||goal<0)return [to];
 const goalPos=pos(goal),g=new Float64Array(clear.length).fill(Infinity),previous=new Int32Array(clear.length).fill(-1),closed=new Uint8Array(clear.length),heap=[];
 function push(id,f){const v={id,f};let i=heap.length;heap.push(v);while(i){const p=(i-1)>>1;if(heap[p].f<=f)break;heap[i]=heap[p];i=p;}heap[i]=v;}
 function pop(){const out=heap[0],last=heap.pop();if(heap.length){let i=0;while(i*2+1<heap.length){let c=i*2+1;if(c+1<heap.length&&heap[c+1].f<heap[c].f)c++;if(heap[c].f>=last.f)break;heap[i]=heap[c];i=c;}heap[i]=last;}return out.id;}
 g[start]=0;push(start,0);let found=false;
 while(heap.length){const id=pop();if(closed[id])continue;if(id===goal){found=true;break;}closed[id]=1;const x=id%nx,z=Math.floor(id/nx);
 for(const [dx,dz] of [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]]){const xx=x+dx,zz=z+dz;if(xx<0||zz<0||xx>=nx||zz>=nz)continue;const n=xx+zz*nx;if(!clear[n]||closed[n])continue;if(dx&&dz&&(!clear[x+dx+z*nx]||!clear[x+(z+dz)*nx]))continue;const cost=g[id]+step*Math.hypot(dx,dz);if(cost<g[n]){g[n]=cost;previous[n]=id;const q=pos(n);push(n,cost+Math.hypot(q.x-goalPos.x,q.z-goalPos.z));}}
 }
 if(!found)return [to];let ids=[],id=goal;while(id>=0){ids.push(id);if(id===start)break;id=previous[id];}ids.reverse();const path=ids.map(pos),simple=[];
 const clearPoint=p=>!boxes.some(b=>b.polygon?polygonBlocked(p.x,p.z,1.8,b):circleBox(p.x,p.z,1.8,b));
 let a=0;while(a<path.length-1){let b=a+1;for(let j=path.length-1;j>a+1;j--){const p=path[a],q=path[j],n=Math.ceil(Math.hypot(q.x-p.x,q.z-p.z)/.22);let ok=true;for(let k=1;k<=n;k++)if(!clearPoint({x:p.x+(q.x-p.x)*k/n,z:p.z+(q.z-p.z)*k/n})){ok=false;break;}if(ok){b=j;break;}}simple.push(path[b]);a=b;}
 if(simple.length&&Math.hypot(simple.at(-1).x-to.x,simple.at(-1).z-to.z)<.9)simple[simple.length-1]=to;return simple.length?simple:[to];
}
