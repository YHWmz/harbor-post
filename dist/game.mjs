import {CARRIAGE,ROAD_LENGTH,carriagePose,stepCarriage,canBoardCoach,atSummit,atFoot} from './carriage-logic.mjs';
import {loadCarriage} from './carriage-view.mjs';
import {createPaintedWater} from './water.mjs';
import {createAtmosphere} from './atmosphere.mjs';
import {MAP_REGIONS,WORLD_BOUNDS} from './world.mjs';
import {buildTown} from './town.mjs';
import {createTownLighting} from './town-lighting.mjs';
import {paintMaterial,sketchEdges,createPaperPass} from './paint.mjs';
import * as THREE from 'three';
import {GLTFLoader} from './vendor/GLTFLoader.js';
import {BANKS,DOCKS,STOPS,DELIVERY_COUNT,SPAWN,BRIDGE,obstacles,planRoute,stepBoat,canDeliver,restoreProgress,DEFAULT_SPEED_SCALE,normalizeSpeedScale} from './logic.mjs';
const $=id=>document.getElementById(id),clamp=THREE.MathUtils.clamp;
let renderer;
try{renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});}catch(e){$('fatal').classList.remove('hidden');$('fatal').textContent='浏览器未能启动 WebGL，请在开启硬件加速的浏览器中打开。';throw e;}
renderer.setPixelRatio(Math.min(devicePixelRatio,1.8));renderer.setSize(innerWidth,innerHeight);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.setClearColor('#ddd7c2');renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;$('world').appendChild(renderer.domElement);renderer.domElement.tabIndex=0;renderer.domElement.setAttribute('aria-label','驾驶场景');
let paintedLandscape=null;const scene=new THREE.Scene();scene.fog=new THREE.Fog('#ddd7c2',65,180);
const overviewCamera=new THREE.OrthographicCamera(-15,15,10,-10,.1,650),chaseCamera=new THREE.PerspectiveCamera(52,innerWidth/innerHeight,.12,450);let camera=overviewCamera;const paperPass=createPaperPass(renderer);
const hemi=new THREE.HemisphereLight('#f4e6ce','#6e8b82',1.20);scene.add(hemi);
const sun=new THREE.DirectionalLight('#ffe9cd',2.0);sun.position.set(-9,18,12);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);sun.shadow.camera.left=-17;sun.shadow.camera.right=17;sun.shadow.camera.top=13;sun.shadow.camera.bottom=-13;sun.shadow.normalBias=.035;sun.shadow.bias=-.0004;sun.shadow.radius=4;scene.add(sun);
const edgeMat=new THREE.LineBasicMaterial({color:'#334e49',transparent:true,opacity:.30});
const {water,shadowPlane,uniforms:waterUniforms,reflect:reflectWater}=createPaintedWater(scene,renderer);
const boat=new THREE.Group();scene.add(boat);let approvedBoat,bridge,modelReady=false,bridgeAmount=0,manualBridge=false;
const goldMaterials=[];const BOAT_FORWARD=0;
let coachView=null,coachReady=false,aboard=false,castleDialog=false,coach={distance:0,speed:0,facing:1},cliffDelivered=false;
try{cliffDelivered=localStorage.getItem('cliff-letter-v1')==='delivered';}catch{}
let trackingCliff=!cliffDelivered;
loadCarriage(scene,view=>{coachView=view;coachReady=true;checkReady();},e=>{console.error(e);$('loadingText').textContent='马车加载失败，请刷新重试';});
$('startBtn').disabled=true;$('startBtn').style.opacity='.5';
new GLTFLoader().load('./assets/approved-harbor-v5.glb',gltf=>{
 const root=gltf.scene;approvedBoat=root.getObjectByName('ApprovedMailboat');bridge=root.getObjectByName('ApprovedLiftBridge');
 if(!approvedBoat||!bridge)throw new Error('Approved asset hierarchy is incomplete');
 root.traverse(o=>{if(!o.isMesh)return;o.castShadow=o.receiveShadow=true;const materials=Array.isArray(o.material)?o.material:[o.material];for(const m of materials){paintMaterial(m);if(m.name.includes('Lamplight'))goldMaterials.push(m);}
 // Source ink curves already exported as geometry; edge lines only supplement silhouettes.
 if(!o.name.includes('Ink')&&!o.name.includes('Wash')){const e=sketchEdges(o.geometry,35,.63);o.add(e);}
 });
 root.remove(approvedBoat);approvedBoat.position.set(0,0,0);boat.add(approvedBoat);
 bridge=null;modelReady=true;checkReady();
},undefined,err=>{$('loadingText').textContent='场景加载失败，请刷新重试';$('fatal').classList.remove('hidden');$('fatal').textContent='确认过的水乡模型未能加载，请刷新页面重试。';console.error(err);});
// The far watercolor landscape is a separate Blender export, beyond the navigable town.
new GLTFLoader().load('./assets/painted-hills.glb',g=>{paintedLandscape=g.scene;paintedLandscape.visible=true;g.scene.traverse(o=>{if(o.isMesh){o.castShadow=false;o.receiveShadow=false;paintMaterial(o.material);}});scene.add(g.scene);},undefined,e=>console.warn('Distant landscape could not load',e));
// Runtime effects only; architecture and shorelines are loaded from Blender GLB.
const wake=[];for(let i=0;i<14;i++){const o=new THREE.Mesh(new THREE.RingGeometry(.48,.50,24),new THREE.MeshBasicMaterial({color:'#d4ddc6',transparent:true,opacity:0,side:THREE.DoubleSide,depthWrite:false}));o.rotation.x=-Math.PI/2;o.position.y=-.145;scene.add(o);wake.push({o,age:10});}let wakeTimer=0,wakeIndex=0;
const targetRing=new THREE.Mesh(new THREE.RingGeometry(.62,.65,40),new THREE.MeshBasicMaterial({color:'#e7bc75',transparent:true,opacity:.55,side:THREE.DoubleSide,depthWrite:false}));targetRing.rotation.x=-Math.PI/2;targetRing.position.y=-.14;scene.add(targetRing);
function textSprite(text){const c=document.createElement('canvas');c.width=128;c.height=128;const ctx=c.getContext('2d');ctx.fillStyle='#eee5ce';ctx.beginPath();ctx.arc(64,64,42,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#ad7951';ctx.lineWidth=2;ctx.stroke();ctx.fillStyle='#966345';ctx.textAlign='center';ctx.textBaseline='middle';ctx.font='45px serif';ctx.fillText(text,64,64);const tx=new THREE.CanvasTexture(c);tx.colorSpace=THREE.SRGBColorSpace;const s=new THREE.Sprite(new THREE.SpriteMaterial({map:tx,transparent:true,depthTest:false}));s.scale.set(.8,.8,1);return s;}
const pin=textSprite('✉');pin.userData.skipReflection=true;targetRing.userData.skipReflection=true;for(const w of wake)w.o.userData.skipReflection=true;scene.add(pin);
let modulesReady=false,town;const cameraOccluders=[];const cameraRay=new THREE.Raycaster();let cameraCheck=0,cameraClearance=40,coachCameraSide=1;
new GLTFLoader().load('./assets/european-water-town.glb',gltf=>{
 town=buildTown(scene,gltf.scene);gltf.scene.traverse(o=>{if(o.isMesh&&!/Glass|Leaf|Flowers|WaterWash|Ink/.test(o.material?.name||''))cameraOccluders.push(o);});modulesReady=true;checkReady();
},undefined,e=>{console.error(e);$('loadingText').textContent='运河街区加载失败，请刷新重试';});

function checkReady(){if(modelReady&&modulesReady&&coachReady){$('startBtn').disabled=false;$('startBtn').style.opacity='1';$('loadingText').textContent='小镇已就绪 · 马车等在悬崖码头';}}
// Game state and compact persistent delivery progress.
let restored={index:0};try{restored=restoreProgress(JSON.parse(localStorage.getItem('blender-canal-post-v6')));}catch{}
let index=restored.index,state={...SPAWN},started=false,paused=false,dialogOpen=false,complete=index>DELIVERY_COUNT,night=0,nightTarget=0,zoom=15,toastTimer=0;
// A shareable castle-route entry starts at the dock without changing saved mail progress.
if(new URLSearchParams(location.search).get('route')==='castle'){state={...SPAWN,x:CARRIAGE.dock.x,z:CARRIAGE.dock.z,heading:Math.PI,speed:0};trackingCliff=true;}
let speedScale=DEFAULT_SPEED_SCALE;try{speedScale=normalizeSpeedScale(localStorage.getItem('canal-boat-speed'));}catch{}
const input={forward:false,back:false,left:false,right:false,brake:false,slow:false};const clearInput=()=>{for(const k of Object.keys(input))input[k]=false;document.querySelectorAll('[data-key]').forEach(b=>b.classList.remove('pressed'));};
function persist(){try{localStorage.setItem('blender-canal-post-v6',JSON.stringify({version:6,index}));}catch{}}
function toast(text){$('toast').textContent=text;$('toast').classList.add('visible');toastTimer=3.4;}
function mailStop(){return STOPS[Math.min(index,DELIVERY_COUNT)];}
function currentStop(){
 if(aboard){const home=coach.facing<0;return {...(home?CARRIAGE.route[0]:CARRIAGE.castle),name:home?'山脚驿站':'崖顶城堡',person:'城堡管家',stamp:'堡',letter:home?'返回码头，换乘小船':'一封城堡来信'};}
 if(trackingCliff)return {...CARRIAGE.dock,stamp:'堡',person:'城堡管家',letter:cliffDelivered?'再访崖顶':'靠岸换马车，上崖送信'};
 return mailStop();
}
function availableInteraction(){
 if(aboard){if(atSummit(coach)&&coach.facing>0)return {kind:cliffDelivered?'turn':'castle',label:cliffDelivered?'调转马车，返回码头':'交付城堡来信'};if(atFoot(coach))return {kind:'boat',label:'下车，回到小船'};return null;}
 if(coachReady&&canBoardCoach(state))return {kind:'board',label:'靠岸，换乘马车'};
 if(!trackingCliff&&!complete&&canDeliver(state,mailStop()))return {kind:'mail',label:index===DELIVERY_COUNT?'返回邮局交班':'靠岸，交付这封信'};return null;
}
function persistCastle(){try{localStorage.setItem('cliff-letter-v1',cliffDelivered?'delivered':'pending');}catch{}}
function interact(){
 if(!started||paused||dialogOpen)return;const action=availableInteraction();if(!action)return;clearInput();
 if(action.kind==='mail'){deliver();return;}
 if(action.kind==='board'){state.speed=0;aboard=true;trackingCliff=true;coach={distance:0,speed:0,facing:1};cameraHeading=carriagePose(coach).heading;toast('已换乘马车 · W/S 沿山路前进倒退，空格停车');}
 if(action.kind==='boat'){aboard=false;coach={distance:0,speed:0,facing:1};trackingCliff=!cliffDelivered;cameraHeading=state.heading;toast(cliffDelivered?'城堡来信已送达 · 继续水乡邮路吧':'已回到小船，马车会在驿站等你');}
 if(action.kind==='turn'){coach.facing=-1;coach.speed=0;toast('马车已调头 · 按 W 沿山路返回码头');}
 if(action.kind==='castle'){
  coach.speed=0;cliffDelivered=true;persistCastle();castleDialog=true;dialogOpen=true;
  $('dialogEyebrow').textContent='山路来信 · 已送达';$('dialogTitle').textContent='崖顶城堡';$('dialogSeal').textContent='堡';$('dialogBody').textContent='管家在城门前接过信：「老公爵等这封远方来信，已经很久了。」山下的河流绕过小镇，流向波光粼粼的大海。';$('collectedStamps').replaceChildren();const stamp=document.createElement('span');stamp.textContent='堡';$('collectedStamps').appendChild(stamp);$('continueBtn').textContent='乘马车返回码头 →';$('dialogOverlay').classList.remove('hidden');$('continueBtn').focus();playBell();
 }
 cameraCheck=0;updateQuest();if(!dialogOpen)renderer.domElement.focus({preventScroll:true});
}
function updateQuest(){const st=currentStop();$('destination').textContent=st.name;$('recipient').textContent='收信人 · '+st.person;$('letterType').textContent=st.letter;$('stamp').textContent=st.stamp;$('progress').textContent=aboard?(coach.facing<0?'返 回 码 头':cliffDelivered?'已 送 达':'山 路 来 信'):trackingCliff?'城 堡 来 信':complete?'已 送 达':index>=DELIVERY_COUNT?'返 航':`${String(index+1).padStart(2,'0')} / ${String(DELIVERY_COUNT).padStart(2,'0')}`;$('game').classList.toggle('coach-mode',aboard);const view=$('viewBtn');if(view)view.textContent=follow?(aboard?'跟车':'跟船'):'全景';if(typeof quietHint!=='undefined')quietHint.textContent=aboard?'W/S 沿山路前进倒退 · 空格停车 · E 交互':'W/S 行舟 · A/D 转舵 · 空格刹船';$('resumeBtn').textContent=aboard?'继续驾车 →':'继续行舟 →';const track=$('cliffTrackBtn');if(track){track.textContent=trackingCliff?'追踪水乡邮路':'追踪城堡来信';track.disabled=aboard;}}
function begin(){if(!modelReady||!modulesReady||!coachReady)return;started=true;cameraHeading=state.heading;chaseCamera.position.set(state.x-Math.sin(state.heading)*15+Math.cos(state.heading)*3.2,7.7,state.z-Math.cos(state.heading)*15-Math.sin(state.heading)*3.2);cameraTarget.set(state.x+Math.sin(state.heading)*5.5,2.2,state.z+Math.cos(state.heading)*5.5);paused=false;$('intro').classList.add('hidden');renderer.domElement.focus({preventScroll:true});if(trackingCliff)toast('先去悬崖码头，慢下来按 E 换马车上崖送信。');else if(index>0)toast(complete?'今日邮路已完成，可以自在行舟。':`已接续邮路 · 下一站 ${currentStop().name}`);else toast(trackingCliff?'先去悬崖码头，换马车送城堡来信。':'船上有五封信，先去运河邮局。');}
$('startBtn').addEventListener('click',begin);
function setPause(value){if(!started||dialogOpen)return;paused=value;clearInput();$('pauseOverlay').classList.toggle('hidden',!value);if(value)$('resumeBtn').focus();else $('pauseBtn').focus();}
$('pauseBtn').onclick=()=>setPause(!paused);$('helpBtn').onclick=()=>setPause(true);$('resumeBtn').onclick=()=>setPause(false);
function restart(){aboard=false;coach={distance:0,speed:0,facing:1};cliffDelivered=false;trackingCliff=true;persistCastle();index=0;complete=false;state={...SPAWN};persist();updateQuest();paused=false;dialogOpen=false;clearInput();$('pauseOverlay').classList.add('hidden');$('dialogOverlay').classList.add('hidden');toast('新的一日，五封信又装上了小舟。');}
$('restartBtn').onclick=restart;
function deliver(){if(!started||paused||dialogOpen||complete)return;const st=mailStop();if(!canDeliver(state,st))return;clearInput();state.speed=0;dialogOpen=true;const done=index===DELIVERY_COUNT;index++;complete=index>DELIVERY_COUNT;persist();$('dialogEyebrow').textContent=done?'今日邮路 · 圆满交班':'一封牵挂，送到了';$('dialogTitle').textContent=done?'这一程，辛苦了':st.name;$('dialogSeal').textContent=st.stamp;$('dialogBody').textContent=st.message;$('collectedStamps').replaceChildren(...STOPS.slice(0,Math.min(index,DELIVERY_COUNT)).map(s=>{const e=document.createElement('span');e.textContent=s.stamp;return e;}));$('continueBtn').textContent=done?'留在小镇，自在行舟 →':index===DELIVERY_COUNT?'返回邮局交班 →':'继续这一程 →';$('dialogOverlay').classList.remove('hidden');$('continueBtn').focus();playBell();updateQuest();}
$('interactBtn').onclick=interact;$('continueBtn').onclick=()=>{dialogOpen=false;$('dialogOverlay').classList.add('hidden');clearInput();if(castleDialog){castleDialog=false;coach.facing=-1;coach.speed=0;updateQuest();toast('按 W 沿山路返回，码头的小船还在等你。');}else if(index===DELIVERY_COUNT&&!complete)toast('五封信已送达，回运河邮局交班吧。');renderer.domElement.focus({preventScroll:true});};
const keyMap={KeyW:'forward',ArrowUp:'forward',KeyS:'back',ArrowDown:'back',KeyA:'left',ArrowLeft:'left',KeyD:'right',ArrowRight:'right',Space:'brake',ShiftLeft:'slow',ShiftRight:'slow'};
addEventListener('keydown',e=>{if(['INPUT','TEXTAREA'].includes(e.target.tagName))return;if(keyMap[e.code]){e.preventDefault();if(started&&!paused&&!dialogOpen)input[keyMap[e.code]]=true;}if(e.repeat)return;if(e.code==='KeyE'){e.preventDefault();interact();}if(e.code==='Escape'||e.code==='KeyP'){e.preventDefault();setPause(!paused);}if(e.code==='Enter'&&!started)begin();});addEventListener('keyup',e=>{if(keyMap[e.code]){input[keyMap[e.code]]=false;e.preventDefault();}});addEventListener('blur',()=>{clearInput();if(started&&!dialogOpen)setPause(true);});document.addEventListener('visibilitychange',()=>{if(document.hidden){clearInput();if(started&&!dialogOpen)setPause(true);}});
for(const b of document.querySelectorAll('[data-key]')){b.addEventListener('pointerdown',e=>{e.preventDefault();b.setPointerCapture(e.pointerId);if(started&&!paused&&!dialogOpen){input[b.dataset.key]=true;b.classList.add('pressed');}});for(const ev of ['pointerup','pointercancel','lostpointercapture'])b.addEventListener(ev,()=>{input[b.dataset.key]=false;b.classList.remove('pressed');});}
$('timeBtn').onclick=()=>{nightTarget=nightTarget?0:1;$('timeBtn').innerHTML=nightTarget?'☾ <span>夜晚</span>':'☀ <span>日光</span>';$('timeBtn').setAttribute('aria-label',nightTarget?'切换到日光':'切换到夜晚');};
$('mapToggle').onclick=()=>{setPause(false);toggleWorldMap();};$('zoomIn').onclick=()=>{zoom=limitZoom(zoom-1.3);};$('zoomOut').onclick=()=>{zoom=limitZoom(zoom+1.3);};
// Optional synthesized water and a delivery bell; no audio downloads or autoplay.
let audioCtx=null,audioGain=null,sound=false;
function audioStart(){audioCtx=new (window.AudioContext||window.webkitAudioContext)();audioGain=audioCtx.createGain();audioGain.gain.value=0;audioGain.connect(audioCtx.destination);const buffer=audioCtx.createBuffer(1,audioCtx.sampleRate*3,audioCtx.sampleRate),data=buffer.getChannelData(0);let brown=0;for(let i=0;i<data.length;i++){brown=(brown+.015*(Math.random()*2-1))/1.015;data[i]=brown*1.7;}const noise=audioCtx.createBufferSource();noise.buffer=buffer;noise.loop=true;const filter=audioCtx.createBiquadFilter();filter.type='lowpass';filter.frequency.value=550;noise.connect(filter);filter.connect(audioGain);noise.start();}
$('soundBtn').onclick=async()=>{try{if(!audioCtx)audioStart();await audioCtx.resume();sound=!sound;audioGain.gain.setTargetAtTime(sound?.16:0,audioCtx.currentTime,.2);$('soundBtn').innerHTML=sound?'♫ <span>水声</span>':'♫ <span>静音</span>';$('soundBtn').setAttribute('aria-label',sound?'关闭环境声音':'打开环境声音');}catch{toast('此浏览器暂时无法播放声音。');}};
function playBell(){if(!sound||!audioCtx)return;for(let i=0;i<2;i++){const o=audioCtx.createOscillator(),g=audioCtx.createGain(),t=audioCtx.currentTime+i*.15;o.type='sine';o.frequency.value=i?784:587;o.connect(g);g.connect(audioCtx.destination);g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.08,t+.012);g.gain.exponentialRampToValueAtTime(.0001,t+1.1);o.start(t);o.stop(t+1.2);}}
// Functional chart of the original Blender quays, pier, repair island and bridge.
let routePoints=[],routeTimer=1;
let mapExpanded=false;
const expandMap=document.createElement('button');expandMap.id='expandMap';expandMap.textContent='展开 M';expandMap.setAttribute('aria-label','展开或收起完整航海地图');document.querySelector('.map-heading').appendChild(expandMap);
function toggleWorldMap(){mapExpanded=!mapExpanded;$('mapPanel').classList.toggle('hidden',!mapExpanded);$('mapPanel').classList.toggle('expanded',mapExpanded);expandMap.textContent=mapExpanded?'收起 M':'展开 M';clearInput();if(mapExpanded)state.speed=0;}
expandMap.onclick=toggleWorldMap;addEventListener('keydown',e=>{if(e.code==='KeyM'&&!e.repeat&&started&&!dialogOpen){e.preventDefault();toggleWorldMap();}});
const mc=$('map').getContext('2d');
function drawMap(){const c=mc,scale=1.12,xx=x=>180+x*scale,zz=z=>130+z*scale;c.setTransform(2,0,0,2,0,0);c.clearRect(0,0,360,280);c.fillStyle='#9bb1a5';c.fillRect(0,0,360,280);
 for(const b of BANKS){c.beginPath();const points=b.polygon||[[b.minX,b.minZ],[b.maxX,b.minZ],[b.maxX,b.maxZ],[b.minX,b.maxZ]];points.forEach(([x,z],i)=>i?c.lineTo(xx(x),zz(z)):c.moveTo(xx(x),zz(z)));c.closePath();c.fillStyle='#d8d4b6';c.fill();c.strokeStyle='#788d7d';c.stroke();}
 for(const b of DOCKS){c.fillStyle='#ad9671';c.fillRect(xx(b.minX),zz(b.minZ),(b.maxX-b.minX)*scale,(b.maxZ-b.minZ)*scale);}
 
 if(trackingCliff||aboard||!complete){c.setLineDash([3,4]);c.strokeStyle='#9a7742';c.beginPath();c.moveTo(xx(state.x),zz(state.z));for(const p of routePoints)c.lineTo(xx(p.x),zz(p.z));c.stroke();c.setLineDash([]);}
 STOPS.forEach((s,i)=>{if(i===DELIVERY_COUNT)return;c.save();c.translate(xx(s.x),zz(s.z));c.rotate(Math.PI/4);c.fillStyle=i<index?'#986850':i===index?'#e3ad48':'#e9e2cb';c.fillRect(-3,-3,6,6);c.restore();});
 c.strokeStyle='#9a7859';c.lineWidth=1.5;c.beginPath();CARRIAGE.route.forEach((p,i)=>i?c.lineTo(xx(p.x),zz(p.z)):c.moveTo(xx(p.x),zz(p.z)));c.stroke();c.lineWidth=1;c.fillStyle='#405e51';c.fillText('崖顶城堡',xx(CARRIAGE.castle.x),zz(CARRIAGE.castle.z)-7);
 c.textAlign='center';c.font='9px "Songti SC",serif';c.fillStyle='#405e51';for(const d of MAP_REGIONS)c.fillText(d.name,xx(d.x),zz(d.z)-18);
 const marker=aboard?carriagePose(coach):state;c.save();c.translate(xx(marker.x),zz(marker.z));c.rotate(-marker.heading);c.fillStyle='#344e4b';c.beginPath();c.moveTo(0,7);c.lineTo(-4,-4);c.lineTo(0,-2);c.lineTo(4,-4);c.closePath();c.fill();c.restore();
}
function limitZoom(value){return clamp(value,follow?9:4.5,follow?32:165);}
let follow=true;const viewButton=document.createElement('button');viewButton.id='viewBtn';viewButton.textContent='跟船';viewButton.setAttribute('aria-label','切换全景或跟随当前交通工具');document.querySelector('nav').prepend(viewButton);viewButton.onclick=()=>{follow=!follow;zoom=follow?15:160;viewButton.textContent=follow?(aboard?'跟车':'跟船'):'全景';};
// One quiet menu contains secondary controls; the scene stays clear while sailing.
const settings=document.createElement('div');settings.className='settings';$('pauseOverlay').querySelector('section').insertBefore(settings,$('resumeBtn'));
for(const id of ['viewBtn','timeBtn','soundBtn','mapToggle'])settings.appendChild($(id));
const atmosphere=createAtmosphere(scene,settings);const townLighting=createTownLighting(scene);
const cliffTrack=document.createElement('button');cliffTrack.id='cliffTrackBtn';settings.appendChild(cliffTrack);cliffTrack.onclick=()=>{if(aboard)return;trackingCliff=!trackingCliff;updateQuest();toast(trackingCliff?'已追踪悬崖码头 · 靠岸按 E 换乘马车':'已接续水乡邮路');};
const speedControl=document.createElement('label');speedControl.className='speed-setting';speedControl.htmlFor='boatSpeed';speedControl.innerHTML='<span>船速 <output id="boatSpeedValue"></output></span><input id="boatSpeed" aria-label="船速倍率" type="range" min="0.75" max="2.5" step="0.25"><small>舒缓 <span>轻快</span></small>';
settings.after(speedControl);$('boatSpeed').value=String(speedScale);$('boatSpeedValue').textContent=speedScale.toFixed(2).replace(/0$/,'')+'×';
$('boatSpeed').oninput=e=>{speedScale=normalizeSpeedScale(e.target.value);$('boatSpeedValue').textContent=speedScale.toFixed(2).replace(/0$/,'')+'×';try{localStorage.setItem('canal-boat-speed',String(speedScale));}catch{}};
$('pauseBtn').textContent='☰';$('pauseBtn').setAttribute('aria-label','打开菜单');
$('mapToggle').textContent='河道图 M';$('mapToggle').setAttribute('aria-expanded','false');
$('mapPanel').classList.add('hidden');
const quietHint=document.createElement('p');quietHint.className='quiet-hint';quietHint.textContent='W/S 行舟 · A/D 转舵 · 空格刹船';document.querySelector('.bottom-hud').appendChild(quietHint);
const originalTarget=new THREE.Vector3(-8,20,-36),cameraTarget=originalTarget.clone(),cameraOffset=new THREE.Vector3(3,20,32),sunDay=new THREE.Color('#ffe9cd'),sunNight=new THREE.Color('#b4c6ce'),hemiDay=new THREE.Color('#f4e6ce'),hemiNight=new THREE.Color('#7f949c');let weatherWet=0;let cameraHeading=SPAWN.heading;let last=performance.now(),t=0,uiTimer=0,lastHitToast=-10;
function resize(){renderer.setSize(innerWidth,innerHeight);chaseCamera.aspect=innerWidth/innerHeight;chaseCamera.fov=innerWidth<innerHeight?62:52;chaseCamera.updateProjectionMatrix();}addEventListener('resize',resize);resize();updateQuest();
function animate(now){requestAnimationFrame(animate);const dt=Math.min(.05,(now-last)/1000);last=now;t+=dt;const active=started&&!paused&&!dialogOpen&&!mapExpanded;
 if(town)town.update(dt,night);const nearBridge=true;const open=manualBridge||nearBridge;bridgeAmount+=(Number(open)-bridgeAmount)*Math.min(1,dt*1.3);if(bridge)bridge.rotation.z=70*Math.PI/180*bridgeAmount;
 if(active&&!aboard){state=stepBoat(state,input,dt,obstacles(bridgeAmount>.89),speedScale);if(state.hit&&t-lastHitToast>4){toast('留意浅滩与岸边 · 转舵或倒船避让');lastHitToast=t;}}
 if(active&&aboard)coach=stepCarriage(coach,input,dt);const focus=aboard?carriagePose(coach):{...state,y:0};if(coachView)coachView.update(dt,carriagePose(coach),aboard?coach.speed:0);
 boat.position.set(state.x,Math.sin(t*1.6)*.018,state.z);boat.rotation.set(0,state.heading-BOAT_FORWARD,Math.sin(t*1.7)*.006);
 wakeTimer+=dt;if(active&&!aboard&&Math.abs(state.speed)>.35&&wakeTimer>.24){wakeTimer=0;const w=wake[wakeIndex++%wake.length];w.age=0;w.o.position.set(state.x-Math.sin(state.heading)*1.3,-.145,state.z-Math.cos(state.heading)*1.3);w.o.rotation.z=-state.heading;}
 for(const w of wake){w.age+=dt;let k=w.age/2.3;w.o.visible=k<1;if(k<1){w.o.scale.set(1+k*1.4,.5+k*.6,1);w.o.material.opacity=(1-k)*.18;}}
 const target=currentStop();routeTimer+=dt;if(routeTimer>.8){routeTimer=0;routePoints=aboard?CARRIAGE.route.filter((_,i)=>i%4===0):planRoute(state,target);}const navPoint=aboard?carriagePose({...coach,distance:coach.distance+coach.facing*5}):routePoints.find(p=>Math.hypot(p.x-state.x,p.z-state.z)>.8)||target;targetRing.visible=pin.visible=started&&(trackingCliff||aboard||!complete);targetRing.position.set(target.x,aboard?target.y+.04:-.14,target.z);targetRing.scale.setScalar(1+Math.sin(t*2)*.05);pin.position.set(target.x,(aboard?target.y:0)+1.5+Math.sin(t*1.8)*.09,target.z);
 night+=(nightTarget-night)*Math.min(1,dt*1.6);waterUniforms.uTime.value=t;waterUniforms.uNight.value=night;waterUniforms.uRain.value=weatherWet;townLighting.update(dt,night,focus);hemi.intensity=1.2-night*.83;hemi.color.copy(hemiDay).lerp(hemiNight,night);sun.position.set(focus.x-9,focus.y+18,focus.z+12);sun.target.position.set(focus.x,focus.y,focus.z);sun.target.updateMatrixWorld();sun.intensity=(2.0-night*1.55)*(1-weatherWet*.64);sun.color.copy(sunDay).lerp(sunNight,night);for(const m of goldMaterials)m.emissiveIntensity=.45+night*.8;
 const immersive=follow&&started;
 if(immersive){
  camera=chaseCamera;const arrival=aboard&&atSummit(coach)&&coach.facing>0;const lookHeading=arrival?Math.atan2(CARRIAGE.castle_look.x-focus.x,CARRIAGE.castle_look.z-focus.z):focus.heading;const angleDelta=Math.atan2(Math.sin(lookHeading-cameraHeading),Math.cos(lookHeading-cameraHeading));cameraHeading+=angleDelta*(1-Math.exp(-dt*1.7));
  const f=new THREE.Vector3(Math.sin(cameraHeading),0,Math.cos(cameraHeading)),r=new THREE.Vector3(Math.cos(cameraHeading),0,-Math.sin(cameraHeading));
  const distance=arrival?Math.max(24,zoom):aboard?Math.max(18,zoom):clamp(zoom,9,32);let pos=new THREE.Vector3(focus.x,0,focus.z).addScaledVector(f,-distance).addScaledVector(r,aboard?coachCameraSide*6:3.2);pos.y=focus.y+(aboard?10:6.2)+distance*.10;
  cameraCheck-=dt;if(cameraCheck<=0){cameraCheck=.16;const origin=new THREE.Vector3(focus.x,focus.y+1.6,focus.z);
   const clearance=p=>{const delta=p.clone().sub(origin);cameraRay.set(origin,delta.clone().normalize());cameraRay.far=delta.length();const hit=cameraRay.intersectObjects(cameraOccluders,false)[0];return hit?Math.max(6,hit.distance-1.3):delta.length();};
   cameraClearance=clearance(pos);if(aboard){const other=pos.clone().addScaledVector(r,-coachCameraSide*12),otherClearance=clearance(other);if(otherClearance>cameraClearance+2.5){coachCameraSide*=-1;pos.copy(other);cameraClearance=otherClearance;}}
  }
  const origin=new THREE.Vector3(focus.x,focus.y+1.6,focus.z),delta=pos.clone().sub(origin);if(delta.length()>cameraClearance)pos.copy(origin).addScaledVector(delta.normalize(),cameraClearance);
  const wanted=new THREE.Vector3(focus.x,focus.y+(arrival?6.5:2.2),focus.z).addScaledVector(f,5.5);cameraTarget.lerp(wanted,1-Math.exp(-dt*3.0));camera.position.lerp(pos,1-Math.exp(-dt*3.2));camera.lookAt(cameraTarget);
  scene.fog.near=70-weatherWet*35;scene.fog.far=320-weatherWet*165;
 }else{
  camera=overviewCamera;cameraTarget.lerp(originalTarget,1-Math.exp(-dt*2));const span=started?zoom:42,viewDistance=Math.max(1,span/18);camera.position.copy(cameraTarget).addScaledVector(cameraOffset,viewDistance);camera.lookAt(cameraTarget);const a=innerWidth/innerHeight;camera.left=-span;camera.right=span;camera.top=span/a;camera.bottom=-span/a;camera.updateProjectionMatrix();scene.fog.near=45+cameraOffset.length()*viewDistance;scene.fog.far=180+cameraOffset.length()*viewDistance;
 }
 if(paintedLandscape)paintedLandscape.visible=true;weatherWet=atmosphere.update(dt,t,focus,camera,night,immersive);scene.fog.color.set('#ddd7c2').lerp(new THREE.Color('#8faaa9'),weatherWet*.72).lerp(new THREE.Color('#354c66'),night*.82);reflectWater(camera);paperPass.render(scene,camera);
 uiTimer+=dt;if(uiTimer>.1){uiTimer=0;const d=aboard?(coach.facing>0?ROAD_LENGTH-coach.distance:coach.distance):Math.hypot(target.x-state.x,target.z-state.z),action=availableInteraction(),ready=active&&!!action;$('distance').textContent=aboard?`${d.toFixed(0)} 米山路`:(!trackingCliff&&complete)?'邮路完成':`${d.toFixed(1)} 米`;$('speedValue').textContent=Math.abs(focus.speed).toFixed(1);$('speedBar').style.width=Math.abs(focus.speed)/(aboard?6:5.4*speedScale)*95+'px';$('motionState').textContent=paused?'泊舟片刻':aboard?'沿山路驾车':Math.abs(state.speed)<.1?'泊舟待发':state.speed<0?'缓缓倒船':'水乡慢行';$('interactBtn').disabled=!ready;$('interactBtn').classList.toggle('ready',ready);$('interactText').textContent=action?.label||(aboard?'沿山路前往目的地':trackingCliff?'靠近悬崖码头，慢下来换马车':'靠近码头后送信');$('guideText').textContent=ready?action.label:aboard?`沿山路 → ${target.name} · ${d.toFixed(0)} 米`:`循航道 → ${target.name} · ${d.toFixed(1)} 米`;
 const from=new THREE.Vector3(focus.x,focus.y,focus.z).project(camera),to=new THREE.Vector3(navPoint.x,navPoint.y||0,navPoint.z).project(camera);$('directionArrow').style.transform=`rotate(${Math.atan2(to.x-from.x,to.y-from.y)}rad)`;drawMap();}
 if(toastTimer>0){toastTimer-=dt;if(toastTimer<=0)$('toast').classList.remove('visible');}
}
requestAnimationFrame(animate);

renderer.domElement.addEventListener('wheel',e=>{if(!started)return;e.preventDefault();zoom=limitZoom(zoom+Math.sign(e.deltaY)*.65);},{passive:false});
let pinchStart=null;renderer.domElement.addEventListener('touchstart',e=>{if(e.touches.length===2){pinchStart={d:Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY),z:zoom};}},{passive:true});
renderer.domElement.addEventListener('touchmove',e=>{if(e.touches.length===2&&pinchStart){e.preventDefault();const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);zoom=limitZoom(pinchStart.z*pinchStart.d/d);}},{passive:false});renderer.domElement.addEventListener('touchend',()=>pinchStart=null);
