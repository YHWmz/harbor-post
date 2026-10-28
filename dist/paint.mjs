import * as THREE from 'three';
// World-anchored pigment and pencil strokes move with the Blender geometry.
export function paintMaterial(material){
 if(material.userData.paperPaint)return;material.userData.paperPaint=true;
 const name=material.name||'',nature=/Meadow|Leaf|Willow|Flowers/.test(name),glass=/Glass/.test(name),ink=/Ink|WaterWash/.test(name);
 material.roughness=1;material.metalness=0;
 if(glass||ink)return;
 material.onBeforeCompile=shader=>{
 shader.vertexShader=shader.vertexShader.replace('#include <common>',`#include <common>\nvarying vec3 vPaperPosition;varying vec3 vPaperNormal;`)
 .replace('#include <worldpos_vertex>',`#include <worldpos_vertex>\nvPaperPosition=(modelMatrix*vec4(transformed,1.0)).xyz;vPaperNormal=normalize(mat3(modelMatrix)*objectNormal);`);
 shader.fragmentShader=shader.fragmentShader.replace('#include <common>',`#include <common>
 varying vec3 vPaperPosition;varying vec3 vPaperNormal;
 float paperHash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
 float paperNoise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(paperHash(i),paperHash(i+vec2(1,0)),f.x),mix(paperHash(i+vec2(0,1)),paperHash(i+vec2(1,1)),f.x),f.y);}
 float pencil(vec2 p,float slope,float frequency){float q=(p.x+slope*p.y)*frequency+.14*sin(p.y*9.)+.09*sin(p.x*14.);float w=max(fwidth(q)*.38,.035);return 1.-smoothstep(w,w*2.,abs(fract(q)-.5));}
 `).replace('#include <color_fragment>',`#include <color_fragment>
 vec3 pn=normalize(vPaperNormal);vec2 pu=abs(pn.y)>.6?vPaperPosition.xz:(abs(pn.x)>.6?vec2(vPaperPosition.z,vPaperPosition.y):vPaperPosition.xy);
 float wash=paperNoise(pu*1.7)+.45*paperNoise(pu*5.3);float grain=paperHash(floor(pu*170.));
 diffuseColor.rgb*=.91+wash*.13+(grain-.5)*.075;
 float shade=1.-clamp(dot(pn,normalize(vec3(-.45,.8,.4))),0.,1.);
 float hatch=pencil(pu,.68,${nature?'5.5':'8.5'});float cross=pencil(pu,-.82,${nature?'7.0':'11.0'});
 float stroke=hatch*(.20+shade*.38)*(.65+.35*paperNoise(pu*4.5))+cross*smoothstep(.32,.85,shade)*.23;
 diffuseColor.rgb*=1.-stroke*${nature?'.36':'.77'};
 diffuseColor.rgb=mix(diffuseColor.rgb,diffuseColor.rgb*vec3(1.07,1.025,.93),.38);
 `).replace('#include <opaque_fragment>',`outgoingLight*=1.-stroke*${nature?'.10':'.45'};\n#include <opaque_fragment>`);
 };
 material.customProgramCacheKey=()=>nature?'paper-nature-v1':'paper-building-v1';material.needsUpdate=true;
}
export function sketchEdges(geometry,threshold=35,opacity=.48){
 const material=new THREE.LineBasicMaterial({color:'#404b40',transparent:true,opacity});
 material.onBeforeCompile=s=>{s.vertexShader=s.vertexShader.replace('#include <begin_vertex>',`#include <begin_vertex>\ntransformed+=vec3(sin(position.y*17.3+position.z*13.1),sin(position.x*19.7+position.z*11.7),sin(position.x*12.1+position.y*16.3))*.007;`);};
 return new THREE.LineSegments(new THREE.EdgesGeometry(geometry,threshold),material);
}
// A single full-screen pass supplies silhouettes, paper fibres and restrained ink pooling.
export function createPaperPass(renderer){
 const target=new THREE.WebGLRenderTarget(1,1,{minFilter:THREE.LinearFilter,magFilter:THREE.LinearFilter});target.texture.colorSpace=THREE.LinearSRGBColorSpace;target.depthTexture=new THREE.DepthTexture(1,1,THREE.UnsignedIntType);
 const uniforms={tColor:{value:target.texture},tDepth:{value:target.depthTexture},uTexel:{value:new THREE.Vector2(1,1)},uNear:{value:.1},uFar:{value:650},uPerspective:{value:1}};
 const material=new THREE.ShaderMaterial({uniforms,depthTest:false,depthWrite:false,vertexShader:`varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}`,fragmentShader:`
 varying vec2 vUv;uniform sampler2D tColor,tDepth;uniform vec2 uTexel;uniform float uNear,uFar,uPerspective;
 float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
 float depthAt(vec2 uv){float d=texture2D(tDepth,uv).r;return mix(uNear+(uFar-uNear)*d,(uNear*uFar)/(uFar+(uNear-uFar)*d),uPerspective);}
 void main(){vec3 col=texture2D(tColor,vUv).rgb;float d=depthAt(vUv);vec2 stepUv=uTexel*1.05;
 float curvature=abs(depthAt(vUv+vec2(stepUv.x,0))+depthAt(vUv-vec2(stepUv.x,0))-2.*d)+abs(depthAt(vUv+vec2(0,stepUv.y))+depthAt(vUv-vec2(0,stepUv.y))-2.*d);
 float edge=smoothstep(.0035,.018,curvature/max(d,1.));float grain=hash(floor(gl_FragCoord.xy));float fibre=sin(gl_FragCoord.y*1.7+sin(gl_FragCoord.x*.07))*sin(gl_FragCoord.x*.91);
 col=mix(col,vec3(.075,.095,.067),edge*.67*(1.-smoothstep(65.,145.,d)));float lum=dot(col,vec3(.299,.587,.114));col=mix(vec3(lum),col,.9);
 col*=.975+(grain-.5)*.055+fibre*.012;col=mix(col,col*vec3(1.04,1.015,.965),.45);
 float vignette=smoothstep(.8,.24,length(vUv-.5));col*=.96+.04*vignette;gl_FragColor=vec4(col,1.);
 #include <colorspace_fragment>
 }`});
 const postScene=new THREE.Scene(),postCamera=new THREE.Camera();postScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2,2),material));let w=0,h=0;
 return {render(scene,camera){const size=renderer.getDrawingBufferSize(new THREE.Vector2());if(size.x!==w||size.y!==h){w=size.x;h=size.y;target.setSize(w,h);uniforms.uTexel.value.set(1/w,1/h);}uniforms.uNear.value=camera.near;uniforms.uFar.value=camera.far;uniforms.uPerspective.value=camera.isPerspectiveCamera?1:0;renderer.setRenderTarget(target);renderer.render(scene,camera);renderer.setRenderTarget(null);renderer.render(postScene,postCamera);}};
}
