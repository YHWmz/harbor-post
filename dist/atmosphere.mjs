import * as THREE from 'three';
// Runtime weather overlays a static Blender landscape. No additional floating HUD.
export function createAtmosphere(scene,settings){
 let rainy=false,wet=0;
 const button=document.createElement('button');button.id='weatherBtn';button.textContent='☀ 晴天';button.setAttribute('aria-label','切换晴天或雨天');button.setAttribute('aria-pressed','false');settings.appendChild(button);
 button.onclick=()=>{rainy=!rainy;button.textContent=rainy?'☂ 雨天':'☀ 晴天';button.setAttribute('aria-pressed',String(rainy));};
 const uniforms={wet:{value:0},night:{value:0}};
 const sky=new THREE.Mesh(new THREE.SphereGeometry(390,32,16),new THREE.ShaderMaterial({side:THREE.BackSide,depthWrite:false,fog:false,uniforms,vertexShader:`varying vec3 dir;void main(){dir=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,fragmentShader:`varying vec3 dir;uniform float wet,night;void main(){float h=smoothstep(-.05,.35,normalize(dir).y);vec3 c=mix(vec3(.84,.83,.74),vec3(.43,.66,.75),h);c=mix(c,mix(vec3(.65,.70,.68),vec3(.46,.55,.58),h),wet*.8);c=mix(c,mix(vec3(.045,.075,.13),vec3(.009,.02,.05),h),night*.99);gl_FragColor=vec4(c,1.);#include <tonemapping_fragment>\n#include <colorspace_fragment>}`.replace(';#include',';\n#include')}));sky.renderOrder=-100;scene.add(sky);
 function discTexture(cloud=false){const c=document.createElement('canvas');c.width=256;c.height=128;const g=c.getContext('2d');
 if(cloud){for(let i=0;i<17;i++){const x=32+i*12,y=61+Math.sin(i*1.7)*12,r=18+Math.sin(i*2.3)*7;const grad=g.createRadialGradient(x,y,2,x,y,r);grad.addColorStop(0,'rgba(253,253,242,.45)');grad.addColorStop(.7,'rgba(253,253,242,.3)');grad.addColorStop(1,'rgba(253,253,242,0)');g.fillStyle=grad;g.fillRect(x-r,y-r,r*2,r*2);}}
 else{const grad=g.createRadialGradient(128,64,13,128,64,54);grad.addColorStop(0,'rgba(255,226,160,.98)');grad.addColorStop(.45,'rgba(255,226,160,.90)');grad.addColorStop(.56,'rgba(255,224,155,.18)');grad.addColorStop(1,'rgba(255,225,170,0)');g.fillStyle=grad;g.fillRect(0,0,256,128);}
 const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return t;}
 const sun=new THREE.Sprite(new THREE.SpriteMaterial({map:discTexture(),transparent:true,depthWrite:false,fog:false}));sun.position.set(-70,27,175);sun.scale.set(44,22,1);scene.add(sun);
 // A soft paper moon with irregular crater washes, separate from the daylight sun.
 const moonCanvas=document.createElement('canvas');moonCanvas.width=moonCanvas.height=256;const mg=moonCanvas.getContext('2d');const halo=mg.createRadialGradient(128,128,45,128,128,124);halo.addColorStop(0,'rgba(228,237,230,.18)');halo.addColorStop(1,'rgba(228,237,230,0)');mg.fillStyle=halo;mg.fillRect(0,0,256,256);mg.fillStyle='#e7ead8';mg.beginPath();mg.arc(128,128,54,0,Math.PI*2);mg.fill();mg.save();mg.clip();for(let i=0;i<23;i++){mg.fillStyle=`rgba(139,167,169,${.025+(i%4)*.014})`;mg.beginPath();mg.ellipse(85+(i*31%90),85+(i*47%90),3+i%8,3+i%6,i,0,Math.PI*2);mg.fill();}mg.restore();const moonMap=new THREE.CanvasTexture(moonCanvas);moonMap.colorSpace=THREE.SRGBColorSpace;const moon=new THREE.Sprite(new THREE.SpriteMaterial({map:moonMap,transparent:true,depthWrite:false,fog:false}));moon.position.set(129,23,155);moon.scale.set(34,34,1);scene.add(moon);
 const cloudMap=discTexture(true),clouds=[];
 for(let i=0;i<16;i++){const a=i*2.39996,r=135+(i%4)*17;const o=new THREE.Sprite(new THREE.SpriteMaterial({map:cloudMap,transparent:true,depthWrite:false,fog:false,color:'#ffffff',opacity:.72}));o.position.set(Math.sin(a)*r,19+i%5*2,Math.cos(a)*r);o.scale.set(38+i%3*14,14+i%3*4,1);scene.add(o);clouds.push({o,x:o.position.x,z:o.position.z});}
 const count=650,positions=new Float32Array(count*6),seeds=[];
 for(let i=0;i<count;i++)seeds.push({x:Math.sin(i*127.1)*22,z:Math.cos(i*73.3)*22,y:(i*.618033%1)*20});
 const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.BufferAttribute(positions,3));
 const rain=new THREE.LineSegments(geometry,new THREE.LineBasicMaterial({color:'#bdcfc9',transparent:true,opacity:0,depthWrite:false}));rain.frustumCulled=false;scene.add(rain);
 const ripples=[];for(let i=0;i<22;i++){const r=new THREE.Mesh(new THREE.RingGeometry(.28,.30,16),new THREE.MeshBasicMaterial({color:'#cad8cd',transparent:true,opacity:0,depthWrite:false,side:THREE.DoubleSide}));r.rotation.x=-Math.PI/2;scene.add(r);ripples.push(r);}
 return {update(dt,t,state,camera,night,immersive=true){wet=THREE.MathUtils.damp(wet,Number(rainy),1.3,dt);uniforms.wet.value=wet;uniforms.night.value=night;sky.position.copy(camera.position);sun.visible=immersive;sun.material.opacity=(1-wet*.97)*(1-THREE.MathUtils.smoothstep(night,.05,.65));moon.visible=immersive&&night>.01;moon.material.opacity=night*(1-wet*.88);
 for(let i=0;i<clouds.length;i++){const {o,x,z}=clouds[i];o.visible=immersive;o.position.x=x+Math.sin(t*.008+i)*8;o.position.z=z+Math.cos(t*.006+i)*4;o.material.color.set(wet>.4?'#a4b3b1':'#ffffff').lerp(new THREE.Color('#728aa4'),night*.83);o.material.opacity=.66+wet*.24;}
 rain.visible=wet>.01;rain.material.opacity=wet*.45;
 if(rain.visible){for(let i=0;i<count;i++){const s=seeds[i],y=(state.y||0)+((s.y-t*14)%20+20)%20,x=state.x+s.x+Math.sin(t*.12)*2,z=state.z+s.z;positions.set([x,y,z,x+.16,y+.70,z-.08],i*6);}geometry.attributes.position.needsUpdate=true;}
 ripples.forEach((o,i)=>{const phase=(t*1.5+i*.618)%1;o.visible=wet>.05;o.position.set(state.x+Math.sin(i*73)*16,-.142,state.z+Math.cos(i*39)*16);o.scale.setScalar(.3+phase*1.8);o.material.opacity=wet*(1-phase)*.17;});return wet;
 }};
}
