// Blender owns all architecture and terrain; Three.js applies a shared ink treatment.
import * as THREE from 'three';
import {paintMaterial,sketchEdges} from './paint.mjs';
export function buildTown(scene,root){
 const luminous=new Set(),falls={value:0};
 root.traverse(o=>{if(!o.isMesh)return;o.castShadow=o.receiveShadow=true;const mats=Array.isArray(o.material)?o.material:[o.material];for(const m of mats){paintMaterial(m);if(m.name.includes('Lamplight'))luminous.add(m);if(m.name.includes('Waterfall')){m.side=THREE.DoubleSide;const paper=m.onBeforeCompile;m.onBeforeCompile=shader=>{paper(shader);shader.uniforms.uCascadeTime=falls;shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>\nuniform float uCascadeTime;').replace('#include <color_fragment>','#include <color_fragment>\nfloat cascade=sin(vPaperPosition.y*15.+vPaperPosition.z*3.+uCascadeTime*6.);diffuseColor.rgb*=.85+.15*cascade;');};m.customProgramCacheKey=()=> 'paper-cascade-v1';}}
 const name=mats[0]?.name||'';if(name.includes('GreenhouseGlass')){o.castShadow=false;for(const m of mats){m.transparent=true;m.depthWrite=false;}}if(!/Leaf|Willow|Meadow|Flowers|WaterWash|Ink/.test(name)){const edges=sketchEdges(o.geometry,38,.60);o.add(edges);}
 });scene.add(root);const boats=[];root.traverse(o=>{const m=o.name.match(/^SM_HarborBoat(\d+)_/);if(m)boats.push({o,phase:Number(m[1])*1.7});});let time=0;return {update(dt,night=0){time+=dt;falls.value=time;for(const m of luminous)m.emissiveIntensity=.18+night*2.4;for(const {o,phase} of boats)o.position.y=Math.sin(time*.85+phase)*.025;}};
}
