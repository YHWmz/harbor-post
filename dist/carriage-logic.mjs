import {CARRIAGE} from './world.mjs';
export {CARRIAGE};
const route=CARRIAGE.route;
export const ROAD_LENGTH=route.reduce((sum,p,i)=>i?sum+Math.hypot(p.x-route[i-1].x,p.y-route[i-1].y,p.z-route[i-1].z):0,0);
const cumulative=[0];for(let i=1;i<route.length;i++)cumulative.push(cumulative.at(-1)+Math.hypot(route[i].x-route[i-1].x,route[i].y-route[i-1].y,route[i].z-route[i-1].z));
export function carriagePose(state){
 const distance=Math.max(0,Math.min(ROAD_LENGTH,state.distance));let i=1;while(i<cumulative.length-1&&cumulative[i]<distance)i++;
 const a=route[i-1],b=route[i],t=(distance-cumulative[i-1])/(cumulative[i]-cumulative[i-1]||1);
 return {x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t,z:a.z+(b.z-a.z)*t,heading:Math.atan2((b.x-a.x)*state.facing,(b.z-a.z)*state.facing),speed:state.speed,vehicle:'carriage'};
}
export function stepCarriage(state,input,dt){
 dt=Math.min(.05,Math.max(0,dt));const throttle=Number(!!input.forward)-Number(!!input.back);let speed=state.speed;
 speed+=throttle*(throttle*speed<0?8:4)*dt;speed*=Math.exp(-(throttle?.28:3)*dt);speed=Math.max(-2.2,Math.min(6,speed));if(input.brake)speed*=Math.exp(-10*dt);
 const next=state.distance+speed*state.facing*dt,distance=Math.max(0,Math.min(ROAD_LENGTH,next));if(next!==distance)speed=0;
 return {...state,distance,speed};
}
export function canBoardCoach(boat){return Math.hypot(boat.x-CARRIAGE.dock.x,boat.z-CARRIAGE.dock.z)<3.2&&Math.abs(boat.speed)<.85;}
export function atSummit(coach){return ROAD_LENGTH-coach.distance<2.1&&Math.abs(coach.speed)<.7;}
export function atFoot(coach){return coach.distance<1.8&&Math.abs(coach.speed)<.7;}
