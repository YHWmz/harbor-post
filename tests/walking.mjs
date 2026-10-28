import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {setWalkingWorld,findLanding,surfaceAt,canReturnToBoat,canDeliverOnFoot,stepWalker,planWalkRoute} from '../dist/walking-logic.mjs';
import {BANKS,STOPS,SPAWN,boatBlocked} from '../dist/logic.mjs';
import {CARRIAGE} from '../dist/world.mjs';
const nav=JSON.parse(readFileSync(new URL('../dist/assets/walking-navigation.json',import.meta.url)));
setWalkingWorld(nav);assert.ok(nav.nodes.length>70000);assert.equal(nav.coverage.length,20);assert.ok(nav.coverage.every(b=>b.nodes>0));
// Independently flood every shipped layer. The graph must be one connected component.
const cells=new Map(),key=(c,h)=>c+':'+h;for(const [c,h] of nav.nodes){const ys=cells.get(c)||[];ys.push(h);cells.set(c,ys);}
const queue=[nav.nodes[0]],seen=new Set([key(...nav.nodes[0])]);for(let head=0;head<queue.length;head++){const [c,h]=queue[head];for(const dc of [1,-1,nav.nx,-nav.nx]){const nc=c+dc;if(Math.abs(dc)===1&&Math.floor(nc/nav.nx)!==Math.floor(c/nav.nx))continue;for(const nh of cells.get(nc)||[]){const k=key(nc,nh);if(Math.abs(nh-h)<=65&&!seen.has(k)){seen.add(k);queue.push([nc,nh]);}}}}assert.equal(seen.size,nav.nodes.length,'all shipped pedestrian surfaces form one physical connected component');
const landing=findLanding({...STOPS[0],speed:0},7);assert.ok(landing,'post-office land entry');assert.equal(findLanding({...STOPS[0],speed:4},7),null,'cannot jump ashore at speed');
// A resting vessel can remain on the water within boarding distance of its land entry.
let moored=null;for(let i=0;i<32&&!moored;i++){const a=i*Math.PI/16,p={x:landing.x+Math.sin(a)*3.3,z:landing.z+Math.cos(a)*3.3,heading:a+Math.PI,speed:0};if(!boatBlocked(p.x,p.z,p.heading))moored=p;}
assert.ok(moored);assert.ok(findLanding(moored));assert.ok(canReturnToBoat(landing,moored));assert.equal(canReturnToBoat({...landing,y:18},moored),false);assert.ok(canDeliverOnFoot(landing,STOPS[0]));
const destinations=[...nav.checkpoints,{...CARRIAGE.castle,y:18.4,name:'castle summit'},...STOPS.map(s=>({...findLanding({...s,speed:0},12),name:s.name}))];
for(const dest of destinations){assert.ok(Number.isFinite(dest.x),dest.name);const route=planWalkRoute(landing,dest);assert.ok(route.length>0,dest.name+' is reachable on foot');assert.ok(Math.hypot(route.at(-1).x-dest.x,route.at(-1).z-dest.z)<1,dest.name+' route reaches actual land checkpoint');}
// A representative continuous character movement traverses an entire bridge and its approach.
const b=nav.bridges.find(b=>!b.existing&&b.banks.includes(14));const route=planWalkRoute(b.points[0],b.points.at(-1));assert.ok(route.length>15);let walker={...route[0],heading:0,speed:0};let peak=0;
for(const target of route.slice(1)){
 for(let k=0;k<80&&Math.hypot(walker.x-target.x,walker.z-target.z)>.08;k++){
  walker.heading=Math.atan2(target.x-walker.x,target.z-walker.z);walker=stepWalker(walker,{forward:true},1/60);peak=Math.max(peak,walker.y);
 }
 assert.ok(Math.hypot(walker.x-target.x,walker.z-target.z)<.13,'continuous input follows collision-checked bridge');
}assert.ok(peak>3,'walking actually climbs the visible bridge, rather than walking through water');
assert.equal(surfaceAt(80,95,.4),null,'open sea has no pedestrian floor');assert.equal(surfaceAt(landing.x,landing.z,18),null,'cannot switch arbitrarily between elevations');
let collisionStop={...landing,heading:Math.atan2(moored.x-landing.x,moored.z-landing.z),speed:0};for(let i=0;i<180;i++)collisionStop=stepWalker(collisionStop,{forward:true,slow:true},1/60);assert.ok(surfaceAt(collisionStop.x,collisionStop.z,collisionStop.y),'water edge always retains a valid floor');assert.ok(Math.hypot(collisionStop.x-moored.x,collisionStop.z-moored.z)>1,'cannot walk out to the floating boat over water');
let total=0;for(const f of ['european-water-town.glb','civic-districts.glb','approved-harbor-v5.glb','painted-hills.glb','cliff-carriage.glb','walking-town.glb','walker.glb']){const buf=readFileSync(new URL('../dist/assets/'+f,import.meta.url)),doc=JSON.parse(buf.toString('utf8',20,20+buf.readUInt32LE(12)));total+=doc.meshes.flatMap(m=>m.primitives).reduce((n,p)=>n+doc.accessors[p.indices].count/3,0);if(f==='walker.glb'){assert.ok(doc.nodes.some(n=>n.name==='LeftLeg'));assert.ok(doc.nodes.some(n=>n.name==='RightArm'));assert.ok(!doc.images?.length);}}
assert.ok(total<320000);console.log(`PASS ${nav.nodes.length} connected walk nodes, 20 land areas, ${destinations.length} destinations incl. summit, shore boarding, continuous bridge traversal, water collision; ${total} scene triangles`);
