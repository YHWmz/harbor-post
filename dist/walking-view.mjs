import * as THREE from 'three';
import {GLTFLoader} from './vendor/GLTFLoader.js';
import {paintMaterial,sketchEdges} from './paint.mjs';
export function loadWalking(scene,onReady,onError){
 const loader=new GLTFLoader();let bridges=null,courier=null,phase=0,displayY=null;
 function painted(root){root.traverse(o=>{if(o.isMesh){o.castShadow=o.receiveShadow=true;for(const m of (Array.isArray(o.material)?o.material:[o.material]))paintMaterial(m);o.add(sketchEdges(o.geometry,35,.4));}});scene.add(root);}
 Promise.all([loader.loadAsync('./assets/walking-town.glb'),loader.loadAsync('./assets/walker.glb'),fetch('./assets/walking-navigation.json').then(r=>{if(!r.ok)throw new Error('Walking navigation unavailable');return r.json();})]).then(([b,p,nav])=>{
  bridges=b.scene;courier=p.scene;painted(bridges);painted(courier);courier.visible=false;
  const left=courier.getObjectByName('LeftLeg'),right=courier.getObjectByName('RightLeg'),la=courier.getObjectByName('LeftArm'),ra=courier.getObjectByName('RightArm');
  onReady({bridges,courier,nav,update(dt,state,visible){courier.visible=visible;if(!visible){displayY=null;return;}phase+=dt*Math.abs(state.speed)*3.4;const swing=Math.sin(phase)*Math.min(.65,Math.abs(state.speed)*.17);for(const [o,v] of [[left,swing],[right,-swing],[la,-swing*.7],[ra,swing*.7]])if(o)o.rotation.x=v;
   displayY=displayY===null?state.y:THREE.MathUtils.lerp(displayY,state.y,1-Math.exp(-dt*20));courier.position.set(state.x,displayY+.015,state.z);courier.rotation.y=state.heading;
  }});
 }).catch(onError);
}
