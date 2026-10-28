import * as THREE from 'three';
import {GLTFLoader} from './vendor/GLTFLoader.js';
import {paintMaterial,sketchEdges} from './paint.mjs';
export function loadCarriage(scene,onReady,onError){
 new GLTFLoader().load('./assets/cliff-carriage.glb',g=>{
  const root=new THREE.Group();root.add(g.scene);scene.add(root);const legs=[],wheels=[];
  g.scene.traverse(o=>{if(o.name.startsWith('HorseLeg'))legs.push(o);if(o.name.startsWith('CartWheel'))wheels.push(o);if(!o.isMesh)return;o.castShadow=o.receiveShadow=true;for(const m of Array.isArray(o.material)?o.material:[o.material])paintMaterial(m);o.add(sketchEdges(o.geometry,38,.48));});
  let time=0;onReady({root,update(dt,pose,moving){time+=dt;root.position.set(pose.x,pose.y,pose.z);root.rotation.y=pose.heading;const motion=Math.min(1,Math.abs(moving)/1.2);legs.forEach((o,i)=>{o.rotation.x=Math.sin(time*8.5+(i===0||i===3?0:Math.PI))*.30*motion;});wheels.forEach(o=>o.rotation.x-=moving*dt/.48);g.scene.position.y=Math.sin(time*9)*.012*motion;}});
 },undefined,onError);
}
