import assert from 'node:assert/strict';
import {DEFAULT_SPEED_SCALE,normalizeSpeedScale,SPAWN,STOPS,DELIVERY_COUNT,WORLD_BOUNDS,BANKS,BRIDGE,obstacles,boatBlocked,stepBoat,canDeliver,circlePolygon,planRoute,restoreProgress} from '../dist/logic.mjs';

let forward=stepBoat({...SPAWN},{forward:true},.05);assert.ok((forward.z-SPAWN.z)*Math.cos(SPAWN.heading)+(forward.x-SPAWN.x)*Math.sin(SPAWN.heading)>0,'W follows the visible source boat bow');
assert.ok((WORLD_BOUNDS.maxX-WORLD_BOUNDS.minX)*(WORLD_BOUNDS.maxZ-WORLD_BOUNDS.minZ)>15*26*21,'explorable water area exceeds fifteen times the original bounds');
assert.equal(boatBlocked(SPAWN.x,SPAWN.z,SPAWN.heading),false,'approved boat spawn is navigable');
assert.ok(BANKS.some(b=>b.polygon.length>50),'Blender exports sampled curved shorelines');
for(const stop of STOPS)assert.equal(boatBlocked(stop.x,stop.z,0),false,`${stop.name} has boat clearance`);
assert.equal(canDeliver({...STOPS[0],speed:2},STOPS[0]),false,'moving vessel cannot deliver');
assert.equal(canDeliver({...STOPS[0],speed:0},STOPS[0]),true,'moored vessel can deliver');
assert.deepEqual(restoreProgress({version:1,index:2}),{index:0},'obsolete map progress is ignored');
assert.deepEqual(restoreProgress({version:6,index:99}),{index:DELIVERY_COUNT+1},'progress is bounded');
let state={...SPAWN};let total=0;
import {LANDMARKS} from '../dist/world.mjs';
for(const stop of [...STOPS,...LANDMARKS,{name:'近海航道',x:0,z:100}]){
 let reached=false,collisions=0;
 for(let tick=0;tick<16000;tick++){
  if(tick%30===0||!globalThis.route){globalThis.route=planRoute(state,stop);}
  const nav=globalThis.route.find(p=>Math.hypot(state.x-p.x,state.z-p.z)>.55)||stop;
  const desired=Math.atan2(nav.x-state.x,nav.z-state.z);
  let error=((desired-state.heading+Math.PI*3)%(Math.PI*2))-Math.PI;
  const distance=Math.hypot(state.x-stop.x,state.z-stop.z);
  if(distance<1.30&&Math.abs(state.speed)<.7){reached=true;break;}
  const input={forward:Math.abs(error)<.35&&distance>1.15,left:error>.08,right:error<-.08,slow:true,brake:Math.abs(error)>.45||distance<1.15};
  state=stepBoat(state,input,1/60,obstacles(true));if(state.hit)collisions++;
  assert.equal(boatBlocked(state.x,state.z,state.heading,obstacles(true)),false,'integration must not penetrate a bank');
  total++;
 }
 assert.equal(reached,true,`route to ${stop.name} can be navigated with the actual steering model`);
 if(STOPS.includes(stop))assert.equal(canDeliver(state,stop),true,`delivery permitted at ${stop.name}`);
 console.log(`PASS ${stop.name}: (${state.x.toFixed(2)}, ${state.z.toFixed(2)}), ${collisions} collision contacts`);
 delete globalThis.route;
}
console.log(`PASS full five-letter route and return (${(total/60).toFixed(0)} simulated seconds)`);
// Assert that runtime geometry is the approved exported asset, not a generated substitute.
import {readFileSync} from 'node:fs';
const glb=readFileSync(new URL('../dist/assets/approved-harbor-v5.glb',import.meta.url));
assert.equal(glb.toString('ascii',0,4),'glTF');
const jsonLength=glb.readUInt32LE(12),asset=JSON.parse(glb.toString('utf8',20,20+jsonLength));
const triangleCount=asset.meshes.flatMap(m=>m.primitives).reduce((s,p)=>s+asset.accessors[p.indices].count/3,0);
assert.equal(triangleCount,17411,'all 484 approved geometry objects survive batching');
assert.equal(asset.meshes.length,14,'static geometry uses 14 material batches');
assert.ok(asset.nodes.find(n=>n.name==='ApprovedMailboat'));
assert.ok(asset.nodes.find(n=>n.name==='ApprovedLiftBridge'));
console.log('PASS approved Blender v5 asset: 17,411 triangles / 14 batches / independent boat and bridge');
// Blender's collision export and visible bank vertices must agree, not just look similar.
const nav=JSON.parse(readFileSync(new URL('../dist/assets/town-navigation.json',import.meta.url),'utf8'));
assert.deepEqual(nav.banks,BANKS,'runtime bank polygons come directly from Blender export');
assert.deepEqual(nav.spawn,SPAWN,'spawn is exported in the same coordinate space');
const town=readFileSync(new URL('../dist/assets/european-water-town.glb',import.meta.url));
const townJsonLength=town.readUInt32LE(12),townData=JSON.parse(town.toString('utf8',20,20+townJsonLength));
const meadow=townData.meshes.find(m=>m.name==='GEO_Meadow');assert.ok(meadow,'native Blender terrain mesh exists');
const acc=townData.accessors[meadow.primitives[0].attributes.POSITION],view=townData.bufferViews[acc.bufferView];
const start=20+townJsonLength+8+(view.byteOffset||0)+(acc.byteOffset||0),stride=view.byteStride||12;
const sample=BANKS[0].polygon[0];let nearest=Infinity;
for(let i=0;i<acc.count;i++){const off=start+i*stride;nearest=Math.min(nearest,Math.hypot(town.readFloatLE(off)-sample[0],town.readFloatLE(off+8)-sample[1]));}
assert.ok(nearest<.0001,'visible GLB bank and collision polygon share the same vertices');
const townTriangles=townData.meshes.flatMap(m=>m.primitives).reduce((n,p)=>n+townData.accessors[p.indices].count/3,0);
assert.ok(townTriangles<220000,'native scene meets web geometry budget');
console.log(`PASS Blender town GLB: ${townTriangles} triangles; bank geometry/navigation agree`);

assert.equal(DEFAULT_SPEED_SCALE,1.5,'new default is fifty percent faster');
assert.equal(normalizeSpeedScale(null),1.5);assert.equal(normalizeSpeedScale('bad'),1.5);assert.equal(normalizeSpeedScale(99),2.5);assert.equal(normalizeSpeedScale(-2),.75);
function accelerate(scale){let boat={x:0,z:0,heading:0,speed:0};for(let i=0;i<120;i++)boat=stepBoat(boat,{forward:true},1/60,[],scale);return boat;}
const oldSpeed=accelerate(1),newSpeed=accelerate(DEFAULT_SPEED_SCALE),fastSpeed=accelerate(2.5);
assert.ok(newSpeed.speed>oldSpeed.speed*1.45,'default acceleration and cruising are actually faster');assert.ok(fastSpeed.speed>newSpeed.speed,'slider changes the driving simulation');
let fast={x:0,z:0,heading:0,speed:13.5};const wall=[{minX:-50,maxX:50,minZ:5,maxZ:8}];
for(let i=0;i<100;i++){fast=stepBoat(fast,{forward:true},.05,wall,2.5);assert.equal(boatBlocked(fast.x,fast.z,fast.heading,wall),false,'maximum boat speed cannot pass through a bank');}
assert.ok(Object.keys(nav.architecture).length>=6,'six building silhouettes are exported');assert.ok(nav.roads.length>=20,'internal town street network is present');assert.ok(townData.nodes.some(n=>n.name.startsWith('SM_Castle_')),'castle is part of the Blender GLB');
console.log('PASS castle landing route, varied buildings, town streets, adjustable speed and high-speed collision');

const publicAssets=JSON.parse(readFileSync(new URL('../dist/assets/public-assets.json',import.meta.url),'utf8'));assert.equal(publicAssets.license,'CC0');assert.ok(Object.keys(publicAssets.usage).length>=10,'public models are actually reused in the scene');assert.deepEqual(publicAssets.usage,nav.public_assets,'reuse manifest matches the Blender navigation export');
console.log('PASS public CC0 component reuse manifest');

assert.ok(nav.details.approved_piers===2 && nav.details.approved_lighthouse===1,'town/seaside piers and mouth lighthouse reuse approved modules');
assert.ok(nav.details.water_buoys>=6 && nav.details.extra_riparian_trees>=16,'water decorations and riparian trees exported');
assert.ok(nav.docks.every(d=>d.polygon.length>=4 && d.maxX-d.minX>2),'pier collisions derived from real source geometry');
assert.ok(townData.nodes.filter(n=>n.name.startsWith('SM_Reused_')).length>=5,'approved pier/lighthouse meshes included in town GLB');
const mountains=readFileSync(new URL('../dist/assets/painted-hills.glb',import.meta.url));const mj=JSON.parse(mountains.toString('utf8',20,20+mountains.readUInt32LE(12)));
for(const m of mj.meshes){const a=mj.accessors[m.primitives[0].attributes.POSITION];assert.ok(a.max[2]<-50,'mountain ridges only behind the castle, never across the sea');}
assert.ok(mj.materials.some(m=>m.name==='MAT_Paper_Snow'),'snowcaps exported from Blender');
console.log('PASS north/snow geography, approved docks, estuary, offshore sailing, decorations');

const lake=LANDMARKS.find(l=>l.name==='雪山湖');assert.ok(lake,'mountain lake has a map landmark');
for(let i=0;i<8;i++){const a=i*Math.PI/4;assert.equal(boatBlocked(lake.x+Math.cos(a)*12,lake.z+Math.sin(a)*12,a),false,'lake has broad open water in every direction');}
assert.equal(nav.harbor_boats.length,8,'eight real reused vessels around the sea harbor');
for(const b of nav.harbor_boats)assert.equal(boatBlocked(b.x,b.z,b.rotation),true,'moored hulls have matching collisions');
const boatGroups=new Set(townData.nodes.flatMap(n=>{const m=n.name?.match(/^SM_HarborBoat(\d+)_/);return m?[m[1]]:[];}));assert.equal(boatGroups.size,8,'all fleet geometry exported by Blender');
const castleHeight=Math.max(...townData.meshes.filter(m=>m.name.startsWith('GEO_Castle_')).flatMap(m=>m.primitives.map(p=>townData.accessors[p.attributes.POSITION].max[1])));assert.ok(castleHeight>22,'expanded castle silhouette exceeds 22 meters');
console.log('PASS open mountain lake, eight CC0 hulls and collisions, expanded castle silhouette');
