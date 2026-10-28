import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {CARRIAGE,ROAD_LENGTH,carriagePose,stepCarriage,canBoardCoach,atSummit,atFoot} from '../dist/carriage-logic.mjs';
import {boatBlocked,planRoute,SPAWN,circlePolygon} from '../dist/logic.mjs';
assert.equal(boatBlocked(CARRIAGE.dock.x,CARRIAGE.dock.z,Math.PI),false,'castle dock has full boat clearance');
assert.ok(planRoute(SPAWN,CARRIAGE.dock).length>1,'dock is connected to the existing river network');
assert.ok(canBoardCoach({...CARRIAGE.dock,speed:0}));assert.ok(!canBoardCoach({...CARRIAGE.dock,speed:2}),'moving boat cannot transfer');assert.ok(!canBoardCoach({...SPAWN,speed:0}),'cannot teleport from elsewhere');
assert.ok(ROAD_LENGTH>150&&ROAD_LENGTH<400,'substantial but playable coach road');
let coach={distance:0,speed:0,facing:1};assert.ok(atFoot(coach));
for(let i=0;i<9000&&!atSummit(coach);i++)coach=stepCarriage(coach,{forward:true},1/60);
for(let i=0;i<90;i++)coach=stepCarriage(coach,{brake:true},1/60);
assert.ok(atSummit(coach),'actual controls reach the castle');let pose=carriagePose(coach);assert.ok(pose.y>18&&pose.y<19);assert.ok(Math.hypot(pose.x-CARRIAGE.castle.x,pose.z-CARRIAGE.castle.z)<2.1);
coach={...coach,facing:-1,speed:0};for(let i=0;i<9000&&!atFoot(coach);i++)coach=stepCarriage(coach,{forward:true},1/60);for(let i=0;i<90;i++)coach=stepCarriage(coach,{brake:true},1/60);assert.ok(atFoot(coach),'W returns the turned coach to the boat');
for(const initial of [0,ROAD_LENGTH]){for(const facing of [1,-1]){let c={distance:initial,speed:0,facing};for(let i=0;i<1000;i++){c=stepCarriage(c,{forward:true},.05);assert.ok(c.distance>=0&&c.distance<=ROAD_LENGTH,'coach stays on the authored road');}}}
let maxGrade=0;for(let i=1;i<CARRIAGE.route.length;i++){const a=CARRIAGE.route[i-1],b=CARRIAGE.route[i];maxGrade=Math.max(maxGrade,Math.abs(b.y-a.y)/Math.hypot(b.x-a.x,b.z-a.z));assert.ok(Math.hypot(b.x-a.x,b.y-a.y,b.z-a.z)<2,'continuous road samples');}assert.ok(maxGrade<.65,'no vertical road jumps');
const glb=readFileSync(new URL('../dist/assets/cliff-carriage.glb',import.meta.url)),j=JSON.parse(glb.toString('utf8',20,20+glb.readUInt32LE(12)));assert.equal(j.nodes.filter(n=>/^HorseLeg\d$/.test(n.name||'')).length,4,'four leg animation pivots');assert.equal(j.nodes.filter(n=>n.name?.startsWith('CartWheel')).length,4,'four wheel animation pivots');
const nav=JSON.parse(readFileSync(new URL('../dist/assets/town-navigation.json',import.meta.url)));assert.deepEqual(nav.carriage,CARRIAGE,'road and transport metadata come from Blender');assert.equal(nav.water_rocks.length,12);for(const rock of nav.water_rocks){const x=rock.polygon.reduce((s,p)=>s+p[0],0)/rock.polygon.length,z=rock.polygon.reduce((s,p)=>s+p[1],0)/rock.polygon.length;assert.ok(boatBlocked(x,z,0),'visible water rocks have real collision');}
console.log(`PASS dock transfer, ${ROAD_LENGTH.toFixed(1)}m coach ascent, 18m summit, delivery approach and return; max grade ${(maxGrade*100).toFixed(0)}%; 12 rocks with collision`);

{
const buf=readFileSync(new URL('../dist/assets/european-water-town.glb',import.meta.url)),len=buf.readUInt32LE(12),j=JSON.parse(buf.toString('utf8',20,20+len)),pts=[];
for(const m of j.meshes.filter(m=>m.name.startsWith('GEO_Castle_')))for(const p of m.primitives){const a=j.accessors[p.attributes.POSITION],v=j.bufferViews[a.bufferView],start=20+len+8+(v.byteOffset||0)+(a.byteOffset||0);for(let i=0;i<a.count;i++){const at=start+i*(v.byteStride||12),x=buf.readFloatLE(at),y=buf.readFloatLE(at+4),z=buf.readFloatLE(at+8);if(y<22.8)pts.push([x,z]);}}
const points=[...new Map(pts.map(p=>[p.join(','),p])).values()].sort((a,b)=>a[0]-b[0]||a[1]-b[1]);const cross=(o,a,b)=>(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]);const half=ps=>{const h=[];for(const p of ps){while(h.length>1&&cross(h.at(-2),h.at(-1),p)<=0)h.pop();h.push(p);}h.pop();return h;};const hull=[...half(points),...half([...points].reverse())];
const failures=[];for(let d=0;d<ROAD_LENGTH;d+=.5){const p=carriagePose({distance:d,facing:1,speed:0});if(p.y<17)continue;for(const off of [-2.5,0,2.4])if(circlePolygon(p.x+Math.sin(p.heading)*off,p.z+Math.cos(p.heading)*off,.95,hull)){failures.push({d:+d.toFixed(1),x:+p.x.toFixed(1),z:+p.z.toFixed(1)});break;}}

assert.equal(failures.length,0,'whole coach footprint clears castle buildings along summit approach');
const cliff=nav.banks.find(b=>b.name==='NorthwestCliff');for(let d=0;d<ROAD_LENGTH;d+=.5){const p=carriagePose({distance:d,facing:1,speed:0});if(p.y>=18.15)continue;for(const off of [-2.4,0,2.4])assert.equal(circlePolygon(p.x+Math.sin(p.heading)*off,p.z+Math.cos(p.heading)*off,.65,cliff.polygon),false,'lower road stays outside the solid cliff');}
console.log('PASS carriage geometry clears solid cliff and castle walls, including summit turn');

}
