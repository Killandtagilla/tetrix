import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="테트리스 클라이머", page_icon="🧱", layout="centered")
st.title("🧱 테트리스 클라이머")

html = """<!DOCTYPE html><html><head><style>
body{margin:0;display:flex;flex-direction:column;align-items:center;background:#0e1117;color:#fff;font-family:sans-serif;user-select:none}
.row{width:310px;display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;gap:4px}
.box{background:#1e2130;padding:7px 10px;border-radius:8px;border:1px solid #333952;box-sizing:border-box}
.lbtn{flex:1;padding:5px 0;font-weight:bold;background:#1e2130;color:#aaa;border:1px solid #333952;border-radius:5px;cursor:pointer}
.lbtn.on{background:#4CAF50;color:#fff}
button{padding:7px 11px;font-weight:bold;background:#2b3044;color:#fff;border:1px solid #4a5270;border-radius:5px;cursor:pointer}
#re{background:#e53935;border:none;font-size:12px}
canvas{border-radius:6px;background:#131520}
#gc{border:3px solid #4CAF50;outline:none;cursor:pointer}
</style></head><body>
<div class="row" id="lvB"></div>
<div class="row box">
  <div style="font-size:13px;font-weight:bold"><div id="lvT"></div><div>⏱️<span id="tm">0.0</span>s | 📏<span id="ht">0</span>/16</div></div>
  <button id="re" onclick="init()">🔄 재시작</button>
  <div style="text-align:center;font-size:10px;color:#aaa">NEXT<br><canvas id="nc" width="60" height="44"></canvas></div>
</div>
<canvas id="gc" width="310" height="520" tabindex="0"></canvas>
<div class="row" style="margin-top:6px;justify-content:center">
  <button onclick="mv(-1)">⬅️</button><button onclick="rot()">🔄</button><button onclick="mv(1)">➡️</button>
  <button onclick="drp()">⬇️</button><button onclick="hdrp()">⏬</button>
</div>
<div style="font-size:11px;color:#999">⬅️➡️이동 | ⬆️회전 | ⬇️하강 | Space낙하 | R재시작</div>
<script>
const gc=document.getElementById("gc"),ctx=gc.getContext("2d"),nctx=document.getElementById("nc").getContext("2d");
const C=10,R=20,S=26,OX=25,G=4;
const LVS=[
  {n:"Lv.1 입문",sp:650,t1:35,t2:55,o:"16,2 16,3 12,6 12,7 8,3 8,4"},
  {n:"Lv.2 초급",sp:550,t1:32,t2:50,o:"17,1 17,2 14,6 14,7 14,8 10,2 10,3 7,5 7,6"},
  {n:"Lv.3 중급",sp:470,t1:30,t2:48,o:"17,4 17,5 14,1 14,2 14,7 14,8 11,4 11,5 8,2 8,7 6,4 6,5"},
  {n:"Lv.4 고급",sp:400,t1:28,t2:45,o:"17,2 17,3 17,7 15,5 13,1 13,2 13,8 11,4 11,5 9,2 9,7 7,4 7,5 7,6"},
  {n:"Lv.5 극한",sp:330,t1:25,t2:40,o:"17,1 17,4 17,8 15,2 15,6 13,0 13,4 13,9 11,2 11,7 9,3 9,5 7,1 7,4 7,8"}
];
const SHP=[
  ["#00F0F0","0000","1111","0000","0000"],["#F0F000","11","11"],["#A000F0","010","111","000"],
  ["#2979FF","100","111","000"],["#FF9100","001","111","000"],["#00E676","011","110","000"],["#FF1744","110","011","000"]
].map(([c,...r])=>({c,m:r.map(s=>[...s].map(Number))}));

let lv=0,brd,cur,nxt,t0,el=0,dc=0,lt=0,st="PLAY",msg="",aid;
document.getElementById("lvB").innerHTML=LVS.map((_,i)=>`<button class="lbtn" onclick="setLv(${i})">Lv.${i+1}</button>`).join("");

function setLv(i){lv=i;document.querySelectorAll(".lbtn").forEach((b,idx)=>b.classList.toggle("on",idx===i));init();}
function rnd(){let s=SHP[Math.random()*7|0];return{m:s.m.map(r=>[...r]),c:s.c,x:5-(s.m.length/2|0),y:0};}
function init(){
  cancelAnimationFrame(aid);
  brd=Array.from({length:R},()=>Array(C).fill(0));
  LVS[lv].o.split(" ").forEach(s=>{let[r,c]=s.split(",").map(Number);brd[r][c]="OBS";});
  document.getElementById("lvT").innerText=LVS[lv].n;
  nxt=rnd();spw();t0=lt=performance.now();dc=0;st="PLAY";gc.focus();
  aid=requestAnimationFrame(loop);
}
function spw(){
  cur=nxt;nxt=rnd();nctx.clearRect(0,0,60,44);
  let m=nxt.m,z=10,sx=(60-m.length*z)/2,sy=(44-m.length*z)/2;
  m.forEach((r,y)=>r.forEach((v,x)=>{if(v){nctx.fillStyle=nxt.c;nctx.fillRect(sx+x*z,sy+y*z,z-1,z-1);}}));
  let h=hit(cur);if(h)over(h==="OBS"?"장애물 충돌!":"천장 도달!");
}
function hit(p){
  for(let y=0;y<p.m.length;y++)for(let x=0;x<p.m[y].length;x++)if(p.m[y][x]){
    let ny=p.y+y,nx=p.x+x;
    if(nx<0||nx>=C||ny>=R)return"W";
    if(ny>=0&&brd[ny][nx])return brd[ny][nx]==="OBS"?"OBS":"B";
  }
}
function fix(){
  let hi=R,mx=0;
  cur.m.forEach((r,y)=>r.forEach((v,x)=>{if(v&&cur.y+y>=0){brd[cur.y+y][cur.x+x]=cur.c;hi=Math.min(hi,cur.y+y);}}));
  brd.forEach((r,y)=>r.forEach(v=>{if(v&&v!=="OBS")mx=Math.max(mx,R-y);}));
  document.getElementById("ht").innerText=Math.min(16,mx);
  hi<=G?st="CLR":spw();
}
function over(m){st="OVR";msg=m;}
function mv(d){if(st==="PLAY"){cur.x+=d;let h=hit(cur);h==="OBS"?over("장애물 충돌!"):h&&(cur.x-=d);}}
function rot(){
  if(st!=="PLAY")return;
  let pm=cur.m;cur.m=cur.m.map((_,i)=>cur.m.map(r=>r[i]).reverse());
  let h=hit(cur),off=1;
  if(h==="OBS")return over("장애물 충돌!");
  while(h){cur.x+=off;off=-(off+(off>0?1:-1));h=hit(cur);if(h==="OBS")return over("장애물 충돌!");if(off>cur.m.length){cur.m=pm;return;}}
}
function drp(){if(st==="PLAY"){cur.y++;let h=hit(cur);h==="OBS"?over("장애물 충돌!"):h&&(cur.y--,fix());dc=0;}}
function hdrp(){if(st==="PLAY"){let h;while(!(h=hit(cur)))cur.y++;if(h==="OBS")return over("장애물 충돌!");cur.y--;fix();dc=0;}}

function drawB(x,y,c,obs){
  let px=OX+x*S,py=y*S;ctx.fillStyle=obs?"#D32F2F":c;ctx.fillRect(px,py,S-1,S-1);
  if(obs){ctx.strokeStyle="#FFCDD2";ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(px+4,py+4);ctx.lineTo(px+S-5,py+S-5);ctx.moveTo(px+S-5,py+4);ctx.lineTo(px+4,py+S-5);ctx.stroke();}
}
function draw(){
  ctx.clearRect(0,0,310,520);ctx.strokeStyle="#1f2336";ctx.lineWidth=1;
  for(let i=0;i<=R;i++){ctx.beginPath();ctx.moveTo(OX,i*S);ctx.lineTo(OX+C*S,i*S);ctx.stroke();}
  for(let i=0;i<=C;i++){ctx.beginPath();ctx.moveTo(OX+i*S,0);ctx.lineTo(OX+i*S,R*S);ctx.stroke();}
  ctx.strokeStyle="#FFD700";ctx.lineWidth=2;ctx.setLineDash([5,4]);
  ctx.beginPath();ctx.moveTo(OX,G*S);ctx.lineTo(OX+C*S,G*S);ctx.stroke();ctx.setLineDash([]);
  ctx.fillStyle="#FFD700";ctx.font="bold 11px sans-serif";ctx.fillText("🏁 GOAL",OX+4,G*S-5);
  brd.forEach((r,y)=>r.forEach((v,x)=>v&&drawB(x,y,v,v==="OBS")));
  if(st==="PLAY")cur.m.forEach((r,y)=>r.forEach((v,x)=>v&&drawB(cur.x+x,cur.y+y,cur.c)));
  if(st!=="PLAY"){
    ctx.fillStyle="rgba(0,0,0,0.84)";ctx.fillRect(0,0,310,520);ctx.textAlign="center";
    if(st==="CLR"){
      let d=LVS[lv],star=el<=d.t1?3:el<=d.t2?2:1,pts=(lv+1)*500+Math.max(0,((60-el)*40)|0);
      ctx.fillStyle="#4CAF50";ctx.font="bold 24px sans-serif";ctx.fillText(`🎉 ${d.n} 클리어!`,155,170);
      ctx.font="36px sans-serif";ctx.fillText("⭐".repeat(star)+"☆".repeat(3-star),155,225);
      ctx.fillStyle="#fff";ctx.font="16px sans-serif";ctx.fillText(`시간: ${el.toFixed(2)}초 | ${pts.toLocaleString()} P`,155,275);
      ctx.fillStyle="#4CAF50";ctx.font="bold 14px sans-serif";ctx.fillText(lv<4?"클릭 / [Enter] 다음 레벨 ▶":"🏆 전체 레벨 정복!",155,340);
    }else{
      ctx.fillStyle="#FF4B4B";ctx.font="bold 28px sans-serif";ctx.fillText("💥 게임 오버!",155,210);
      ctx.fillStyle="#fff";ctx.font="16px sans-serif";ctx.fillText(msg,155,255);
      ctx.fillStyle="#4CAF50";ctx.font="bold 14px sans-serif";ctx.fillText("클릭 / [R, Enter] 재시작",155,310);
    }
  }
}
function loop(t=0){
  if(st==="PLAY"){el=(t-t0)/1000;document.getElementById("tm").innerText=el.toFixed(1);dc+=t-lt;lt=t;if(dc>LVS[lv].sp)drp();}
  draw();if(st==="PLAY")aid=requestAnimationFrame(loop);
}
gc.onclick=()=>st==="CLR"&&lv<4?setLv(lv+1):st!=="PLAY"?init():gc.focus();
document.onkeydown=e=>{
  if(e.code==="KeyR"){e.preventDefault();return init();}
  if(st!=="PLAY"&&e.code==="Enter"){e.preventDefault();return st==="CLR"&&lv<4?setLv(lv+1):init();}
  if(st!=="PLAY")return;
  if(["ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Space"].includes(e.code))e.preventDefault();
  ({ArrowLeft:()=>mv(-1),ArrowRight:()=>mv(1),ArrowDown:drp,ArrowUp:rot,Space:hdrp}[e.code]||(()=>0))();
};
setLv(0);
</script></body></html>"""

components.html(html, height=670)
