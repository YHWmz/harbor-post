import * as THREE from 'three';
// A moving painted surface with a reduced-resolution planar scene reflection.
export function createPaintedWater(scene,renderer){
 const target=new THREE.WebGLRenderTarget(1,1,{minFilter:THREE.LinearFilter,magFilter:THREE.LinearFilter});target.texture.colorSpace=THREE.LinearSRGBColorSpace;
 const uniforms={uTime:{value:0},uNight:{value:0},uRain:{value:0},uReflection:{value:target.texture},uReflectionMatrix:{value:new THREE.Matrix4()},uTexel:{value:new THREE.Vector2(1/512,1/320)},uReady:{value:0}};
 const material=new THREE.ShaderMaterial({uniforms,vertexShader:`varying vec3 vPos;varying vec4 vReflection;uniform mat4 uReflectionMatrix;void main(){vec4 world=modelMatrix*vec4(position,1.);vPos=world.xyz;vReflection=uReflectionMatrix*world;gl_Position=projectionMatrix*viewMatrix*world;}`,fragmentShader:`
 varying vec3 vPos;varying vec4 vReflection;uniform float uTime,uNight,uRain,uReady;uniform sampler2D uReflection;uniform vec2 uTexel;
 float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
 float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
 void main(){vec2 p=vPos.xz;float sea=smoothstep(46.,100.,p.y),lake=1.-smoothstep(-50.,-32.,p.y);
 vec2 flow=normalize(vec2(.20+.40*sin(p.y*.045),1.));vec2 adv=p-flow*uTime*mix(.42,.13,lake);
 float w1=sin(dot(adv,vec2(.72,.36))*2.2),w2=sin(dot(adv,vec2(-.49,.91))*3.7+uTime*.55);
 float amplitude=mix(.035,.065,sea)*mix(1.,.55,lake);
 vec3 N=normalize(vec3((w1*.72-w2*.49)*amplitude,1.,(w1*.36+w2*.91)*amplitude));vec3 V=normalize(cameraPosition-vPos);
 float fresnel=.18+.46*pow(1.-max(dot(N,V),0.),3.);vec2 uv=vReflection.xy/vReflection.w;
 uv+=N.xz*.028+vec2(sin(p.y*2.1+uTime),cos(p.x*2.5-uTime*.7))*.0007;
 vec2 inset=uTexel*2.;uv=clamp(uv,inset,1.-inset);
 vec3 refl=texture2D(uReflection,uv).rgb*.40;
 refl+=(texture2D(uReflection,uv+vec2(uTexel.x*2.,0)).rgb+texture2D(uReflection,uv-vec2(uTexel.x*2.,0)).rgb+texture2D(uReflection,uv+vec2(0,uTexel.y*2.)).rgb+texture2D(uReflection,uv-vec2(0,uTexel.y*2.)).rgb)*.15;
 float wash=noise(adv*.28)*.05+noise(adv*.9)*.018;vec3 col=mix(vec3(.29,.42,.43),vec3(.15,.26,.30),uNight);col=mix(col,vec3(.24,.37,.43),sea*.24*(1.-uNight));col+=wash;
 col=mix(col,refl,fresnel*uReady*(1.-uRain*.15));
 vec3 L=normalize(vec3(-.36,.34,.87)),H=normalize(V+L);float sparkle=pow(max(dot(N,H),0.),110.);float broken=.25+.75*noise(adv*3.5);
 col+=vec3(.95,.78,.47)*sparkle*broken*.65*(1.-uNight*.8)*(1.-uRain*.9);
 vec2 cell=floor(adv*.85),q=fract(adv*.85);float id=hash(cell),curve=.48+.08*sin(q.x*6.+id*6.+uTime*.55);float width=max(fwidth(q.y),.009);
 float stroke=(1.-smoothstep(width,width*2.,abs(q.y-curve)))*smoothstep(.1,.28,q.x)*(1.-smoothstep(.63,.87,q.x))*step(.68,id);
 col*=1.-stroke*.11;float crest=pow(max(0.,sin(dot(adv,vec2(.35,.82))*4.)),18.)*noise(adv*.7);col+=crest*.026;
 col+=(hash(floor(p*140.))-.5)*.022;gl_FragColor=vec4(col,1.);
 #include <tonemapping_fragment>
 #include <colorspace_fragment>
 }`});
 const water=new THREE.Mesh(new THREE.PlaneGeometry(700,700),material);water.rotation.x=-Math.PI/2;water.position.y=-.17;scene.add(water);
 const shadowPlane=new THREE.Mesh(new THREE.PlaneGeometry(700,700),new THREE.ShadowMaterial({opacity:.10}));shadowPlane.rotation.x=-Math.PI/2;shadowPlane.position.y=-.165;shadowPlane.receiveShadow=true;scene.add(shadowPlane);
 // Exclude submerged geometry from the reflection; restore renderer state afterwards.
 const reflectionClip=[new THREE.Plane(new THREE.Vector3(0,1,0),.16)];
 const bias=new THREE.Matrix4().set(.5,0,0,.5,0,.5,0,.5,0,0,.5,.5,0,0,0,1);let mirror=null,frames=0,w=0,h=0;
 return {water,shadowPlane,uniforms,reflect(camera){
 if(frames++%3 && uniforms.uReady.value)return;
 const width=Math.max(240,Math.min(512,Math.round(innerWidth*.45))),height=Math.max(160,Math.round(width*innerHeight/innerWidth));if(w!==width||h!==height){w=width;h=height;target.setSize(w,h);uniforms.uTexel.value.set(1/w,1/h);}
 if(!mirror||mirror.type!==camera.type)mirror=camera.clone();else mirror.copy(camera,false);
 camera.updateMatrixWorld();const look=camera.getWorldDirection(new THREE.Vector3()).add(camera.position);mirror.position.copy(camera.position);mirror.position.y=-.34-camera.position.y;look.y=-.34-look.y;mirror.up.copy(camera.up);mirror.up.y*=-1;mirror.lookAt(look);mirror.updateMatrixWorld();
 uniforms.uReflectionMatrix.value.copy(bias).multiply(mirror.projectionMatrix).multiply(mirror.matrixWorldInverse);
 const hidden=[water,shadowPlane];scene.traverse(o=>{if(o.userData.skipReflection&&o.visible)hidden.push(o);});const visibility=hidden.map(o=>o.visible);hidden.forEach(o=>o.visible=false);
 const previous=renderer.getRenderTarget(),auto=renderer.shadowMap.autoUpdate,previousClip=renderer.clippingPlanes;renderer.clippingPlanes=reflectionClip;renderer.shadowMap.autoUpdate=false;
 try{renderer.setRenderTarget(target);renderer.clear();renderer.render(scene,mirror);uniforms.uReady.value=1;}finally{renderer.setRenderTarget(previous);renderer.clippingPlanes=previousClip;renderer.shadowMap.autoUpdate=auto;hidden.forEach((o,i)=>o.visible=visibility[i]);}
 }};
}
