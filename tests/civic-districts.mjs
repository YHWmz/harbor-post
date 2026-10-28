import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {BANKS,LANDMARKS} from '../dist/world.mjs';
import {circlePolygon,boatBlocked,planRoute} from '../dist/logic.mjs';
const nav=JSON.parse(readFileSync(new URL('../dist/assets/town-navigation.json',import.meta.url)));
const district=JSON.parse(readFileSync(new URL('../dist/assets/civic-districts.json',import.meta.url)));
assert.equal(nav.northern_closures.length,2,'both requested mountain-side outlets are infilled');
for(const bank of nav.northern_closures){
 assert.equal(bank.name,'NorthernClosure');
 const x=bank.polygon.reduce((n,p)=>n+p[0],0)/bank.polygon.length,z=bank.polygon.reduce((n,p)=>n+p[1],0)/bank.polygon.length;
 assert.ok(boatBlocked(x,z,0),'boat cannot cross the new land at either old sea outlet');
}
assert.deepEqual(district.features,nav.district_features);
for(const kind of ['manor','restaurant','hall','winery','formal_garden','summit_garden','neighborhood_garden'])assert.ok(district.features.some(f=>f.kind===kind),kind+' is exported');
assert.ok(district.triangles>10000&&district.triangles<28000,'district has an independent bounded scene budget');
for(const f of district.features){
 assert.ok(BANKS.some(b=>circlePolygon(f.x,f.z,.1,b.polygon)),f.name+' is on solid land');
 if(['manor','restaurant','hall','winery'].includes(f.kind))for(const [x,z] of f.footprint)assert.ok(BANKS.some(b=>circlePolygon(x,z,.05,b.polygon)),f.name+' building footprint stays on land');
 if(f.kind==='summit_garden')assert.equal(f.ground,18.35,'castle garden matches the cliff summit');
}
const lake=LANDMARKS.find(l=>l.name==='雪山湖');for(let i=0;i<8;i++){const a=i*Math.PI/4;assert.equal(boatBlocked(lake.x+Math.cos(a)*12,lake.z+Math.sin(a)*12,a),false,'lake remains open');}
const blob=readFileSync(new URL('../dist/assets/civic-districts.glb',import.meta.url));const doc=JSON.parse(blob.toString('utf8',20,20+blob.readUInt32LE(12)));
assert.ok(doc.nodes.every(n=>!n.mesh||n.name.startsWith('SM_District_')),'district geometry is native Blender export');
const tris=doc.meshes.flatMap(m=>m.primitives).reduce((n,p)=>n+doc.accessors[p.indices].count/3,0);assert.equal(tris,district.triangles);
console.log(`PASS two northern closures, manor/restaurant/hall/winery and gardens on land; native district ${tris} triangles`);
