import * as THREE from 'three';
import {GLTFLoader} from './vendor/GLTFLoader.js';
import {paintMaterial,sketchEdges} from './paint.mjs';
export function paintCourier(root){
 root.traverse(o=>{if(!o.isMesh)return;o.castShadow=o.receiveShadow=true;
  for(const m of (Array.isArray(o.material)?o.material:[o.material])){
   if(m.userData.courierPaint)continue;m.userData.courierPaint=true;paintMaterial(m);const paper=m.onBeforeCompile,face=/Skin|Hair|Ink/.test(m.name);
   m.onBeforeCompile=shader=>{paper(shader);shader.fragmentShader=shader.fragmentShader.replace('stroke*.77','stroke*'+(face?'.11':'.35')).replace('stroke*.45','stroke*'+(face?'.04':'.13'));
    shader.fragmentShader=shader.fragmentShader.replace('#include <opaque_fragment>',`float courierEdge=1.-abs(dot(normalize(normal),normalize(vViewPosition)));outgoingLight*=1.-smoothstep(.85,.99,courierEdge)*${face?'.12':'.20'};\n#include <opaque_fragment>`);
   };m.customProgramCacheKey=()=>face?'paper-courier-face-v1':'paper-courier-cloth-v1';
  }
  // Static EdgesGeometry would remain in the imported T-pose on a skinned mesh.
 });
}
export function createCourierAnimator(root,clips){
 const mixer=new THREE.AnimationMixer(root),actions=Object.fromEntries(clips.map(c=>[c.name,mixer.clipAction(c)]));
 for(const [name,action] of Object.entries(actions))action.setEffectiveWeight(name==='Idle'?1:0).play();
 const weights={Idle:1,Walk:0,Run:0};
 return {actions,mixer,update(dt,speed){
  const v=Math.abs(speed),moving=THREE.MathUtils.smoothstep(v,.05,.55),run=THREE.MathUtils.smoothstep(v,4.0,6.0),wanted={Idle:1-moving,Walk:moving*(1-run),Run:moving*run};
  for(const name of ['Idle','Walk','Run']){weights[name]=THREE.MathUtils.lerp(weights[name],wanted[name],1-Math.exp(-dt*9));actions[name].setEffectiveWeight(weights[name]);}
  const direction=speed<-.05?-1:1;actions.Walk.setEffectiveTimeScale(direction*THREE.MathUtils.clamp(v/1.8,.45,2.3));actions.Run.setEffectiveTimeScale(direction*THREE.MathUtils.clamp(v/4.3,.6,1.7));mixer.update(dt);
 }};
}
export function loadWalking(scene,onReady,onError){
 const loader=new GLTFLoader();let displayY=null;
 Promise.all([loader.loadAsync('./assets/walking-town.glb'),loader.loadAsync('./assets/walker.glb'),fetch('./assets/walking-navigation.json').then(r=>{if(!r.ok)throw new Error('Walking navigation unavailable');return r.json();})]).then(([b,p,nav])=>{
  const bridges=b.scene,courier=p.scene;bridges.traverse(o=>{if(o.isMesh){o.castShadow=o.receiveShadow=true;paintMaterial(o.material);o.add(sketchEdges(o.geometry,35,.4));}});scene.add(bridges);
  paintCourier(courier);scene.add(courier);courier.visible=false;const animator=createCourierAnimator(courier,p.animations);
  onReady({bridges,courier,nav,update(dt,state,visible){courier.visible=visible;if(!visible){displayY=null;return;}animator.update(dt,state.speed);
   displayY=displayY===null?state.y:THREE.MathUtils.lerp(displayY,state.y,1-Math.exp(-dt*20));courier.position.set(state.x,displayY+.015,state.z);courier.rotation.y=state.heading;
  }});
 }).catch(onError);
}
