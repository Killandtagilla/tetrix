import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="테트리스 클라이머", page_icon="🧱", layout="centered")
st.title("🧱 테트리스 클라이머")
st.markdown("**레벨별 장애물**을 피해 블록을 쌓아 **목표 라인(노란 점선)**까지 최대한 빠르게 올라가세요!")

game_html = """<!DOCTYPE html><html><head><style>
body{margin:0;display:flex;flex-direction:column;align-items:center;background:#0e1117;color:#fff;font-family:sans-serif;user-select:none}
#lvl-bar{width:320px;display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;gap:4px}
.lbtn{flex:1;padding:6px 0;font-size:13px;font-weight:bold;background:#1e2130;color:#aaa;border:1px solid #333952;border-radius:6px;cursor:pointer}
.lbtn.active{background:#4CAF50;color:#fff;border-color:#4CAF50}
#top{width:320px;display:flex;justify-content:space-between;align-items:center;background:#1e2130;padding:8px 12px;border-radius:8px;border:2px solid #333952;margin-bottom:8px;box-sizing:border-box}
.info{display:flex;flex-direction:column;gap:4px;font-size:14px;font-weight:bold}
#next-box{display:flex;flex-direction:column;align-items:center;font-size:11px;color:#aaa}
#nextC{background:#131520;border:1px solid #444;border-radius:4px;margin-top:2px}
#gameC{border:3px solid #4CAF50;border-radius:8px;background:#1e2130;outline:none;cursor:pointer}
.btns{display:flex;gap:6px;margin-top:8px}
button{padding:8px 12px;font-size:14px;font-weight:bold;background:#2b3044;color:#fff;border:1px solid #4a5270;border-radius:5px;cursor:pointer}
button:hover{background:#3c435e}
#reBtn{background:#e53935;border:none;padding:6px 10px;font-size:12px;border-radius:5px;color:#fff;font-weight:bold;cursor:pointer}
</style></head><body>
<div id="lvl-bar">
  <button class="lbtn active" onclick="setLvl(1)">Lv.1</button>
  <button class="lbtn" onclick="setLvl(2)">Lv.2</button>
  <button class="lbtn" onclick="setLvl(3)">Lv.3</button>
  <button class="lbtn" onclick="setLvl(4)">Lv.4</button>
  <button class="lbtn" onclick="setLvl(5)">Lv.5</button>
</div>
<div id="top">
  <div class="info">
    <span>🏆 <span id="lvTxt">Lv.1 (입문)</span></span>
    <span>⏱️ <span id="tm">0.0</span>초 | 📏 <span id="ht">0</span>/16</span>
  </div>
  <button id="reBtn" onclick="init()">🔄 재시작</button>
  <div id="next-box"><span>NEXT</span><canvas id="nextC" width="68" height="48"></canvas></div>
</div>
<canvas id="gameC" width="320" height="540" tabindex="0"></canvas>
<div class="btns">
  <button onclick="mv(-1)">⬅️</button><button onclick="rotP()">🔄 회전</button><button onclick="mv(1)">➡️</button>
  <button onclick="drop()">⬇️</button><button onclick="hDrop()">⏬ 낙하</button>
</div>
<div style="margin-top:6px;font-size:12px;color:#bbb">⬅️➡️ 이동 | ⬆️ 회전 | ⬇️ 내리기 | <b>Space</b> 낙하 | <b>R</b> 재시작</div>
<script>
const c=document.getElementById("gameC"),ctx=c.getContext("2d"),nc=document.getElementById("nextC"),nctx=nc.getContext("2d");
const tmEl=document.getElementById("tm"),htEl=document.getElementById("ht"),lvEl=document.getElementById("lvTxt");
const COLS=10,ROWS=20,BS=27,OX=25,GOAL=4;
const LEVELS={
  1:{name:"Lv.1 (입문)",spd:650,starT:,obs:"16,2 16,3 12,6 12,7 8,3 8,4"},
  2:{name:"Lv.2 (초급)",spd:550,starT:,obs:"17,1 17,2 14,6 14,7 14,8 10,2 10,3 7,5 7,6"},
  3:{name:"Lv.3 (중급)",spd:470,starT:,obs:"17,4 17,5 14,1 14,2 14,7 14,8 11,4 11,5 8,2 8,7 6,4 6,5"},
  4:{name:"Lv.4 (고급)",spd:400,starT:,obs:"17,2 17,3 17,7 15,5 13,1 13,2 13,8 11,4 11,5 9,2 9,7 7,4 7,5 7,6"},
  5:{name:"Lv.5 (극한)",spd:330,starT:,obs:"17,1 17,4 17,8 15,2 15,6 13,0 13,4 13,9 11,2 11,7 9,3 9,5 7,1 7,4 7,8"}
};
const DEFS=[
  {c:"#00F0F0",r:["0000","1111","0000","0000"]},{c:"#F0F000",r:["11","11"]},{c:"#A000F0",r:["010","111","000"]},
  {c:"#2979FF",r:["100","111","000"]},{c:"#FF9100",r:["001","111","000"]},{c:"#00E676",r:["011","110","000"]},{c:"#FF1744",r:["110","011","000"]}
];
const SHAPES=DEFS.map(d=>({c:d.c,m:d.r.map(s=>s.split("").map(Number))}));
let curLvl=1,brd=[],cur=null,nxt=null,stT=0,elT=0,dCnt=0,lT=0,state="PLAY",overMsg="",aid=null;

function setLvl(lv){
  curLvl=lv;
  document.querySelectorAll(".lbtn").forEach((b,i)=>b.classList.toggle("active",i+1===lv));
  init();
}
function mkBrd(){
  let b=Array.from({length:ROWS},()=>Array(COLS).fill(0));
  LEVELS[curLvl].obs.split(" ").forEach(s=>{
    let p=s.split(",");
    b[Number(p)][Number(p)]="OBS";
  });
  return b;
}
function rndP(){
  let s=SHAPES[Math.floor(Math.random()*SHAPES.length)];
  return{m:s.m.map(r=>[...r]),c:s.c,x:Math.floor(COLS/2)-Math.ceil(s.m.length/2),y:0};
}
function init(){
  if(aid)cancelAnimationFrame(aid);
  lvEl.innerText=LEVELS[curLvl].name;
  brd=mkBrd();nxt=rndP();spawn();stT=performance.now();lT=stT;dCnt=0;state="PLAY";overMsg="";
  tmEl.innerText="0.0";htEl.innerText="0";c.focus();
  aid=requestAnimationFrame(loop);
}
function spawn(){
  cur=nxt;nxt=rndP();
  nctx.clearRect(0,0,68,48);
  let m=nxt.m,sz=11,sx=(68-m.length*sz)/2,sy=(48-m.length*sz)/2;
  m.forEach((row,r)=>row.forEach((v,col)=>{if(v){nctx.fillStyle=nxt.c;nctx.fillRect(sx+col*sz,sy+r*sz,sz-1,sz-1);}}));
  let res=col(brd,cur);
  if(res)end("OVER",res==="OBS"?"장애물에 부딪혔습니다!":"블록이 천장에 닿았습니다.");
}
function col(b,p){
  for(let r=0;r<p.m.length;r++)for(let cl=0;cl<p.m[r].length;cl++)
    if(p.m[r][cl]){
      let ny=p.y+r,nx=p.x+cl;
      if(nx<0||nx>=COLS||ny>=ROWS)return "WALL";
      if(ny>=0&&b[ny][nx]!==0)return b[ny][nx]==="OBS"?"OBS":"BLOCK";
    }
  return null;
}
function merge(b,p){
  let hi=ROWS;
  p.m.forEach((row,r)=>row.forEach((v,cl)=>{if(v&&p.y+r>=0){b[p.y+r][p.x+cl]=p.c;if(p.y+r<hi)hi=p.y+r;}}));
  let mx=0;
  for(let r=0;r<ROWS;r++)for(let cl=0;cl<COLS;cl++)if(b[r][cl]!==0&&b[r][cl]!=="OBS")mx=Math.max(mx,ROWS-r);
  htEl.innerText=Math.min(16,mx);
  if(hi<=GOAL)end("CLEAR");
}
function mv(d){
  if(state!=="PLAY")return;
  cur.x+=d;let res=col(brd,cur);
  if(res==="OBS")end("OVER","장애물에 부딪혔습니다!");
  else if(res)cur.x-=d;
}
function rotP(){
  if(state!=="PLAY")return;
  let pm=cur.m;cur.m=cur.m.map((_,i)=>cur.m.map(r=>r[i]).reverse());
  let res=col(brd,cur);
  if(res==="OBS"){end("OVER","장애물에 부딪혔습니다!");return;}
  let off=1;
  while(res){
    cur.x+=off;off=-(off+(off>0?1:-1));res=col(brd,cur);
    if(res==="OBS"){end("OVER","장애물에 부딪혔습니다!");return;}
    if(off>cur.m.length){cur.m=pm;return;}
  }
}
function drop(){
  if(state!=="PLAY")return;
  cur.y++;let res=col(brd,cur);
  if(res==="OBS"){end("OVER","장애물에 부딪혔습니다!");}
  else if(res){cur.y--;merge(brd,cur);if(state==="PLAY")spawn();}
  dCnt=0;
}
function hDrop(){
  if(state!=="PLAY")return;
  let res=null;
  while(!(res=col(brd,cur)))cur.y++;
  if(res==="OBS"){end("OVER","장애물에 부딪혔습니다!");return;}
  cur.y--;merge(brd,cur);if(state==="PLAY")spawn();dCnt=0;
}
function end(s,msg=""){state=s;overMsg=msg;}
function drawB(x,y,clr,obs=false){
  let px=OX+x*BS,py=y*BS;
  if(obs){
    ctx.fillStyle="#D32F2F";ctx.fillRect(px,py,BS-1,BS-1);ctx.strokeStyle="#FFCDD2";ctx.lineWidth=2;
    ctx.beginPath();ctx.moveTo(px+4,py+4);ctx.lineTo(px+BS-5,py+BS-5);ctx.moveTo(px+BS-5,py+4);ctx.lineTo(px+4,py+BS-5);ctx.stroke();
  }else{ctx.fillStyle=clr;ctx.fillRect(px,py,BS-1,BS-1);}
}
function draw(){
  ctx.clearRect(0,0,320,540);ctx.fillStyle="#131520";ctx.fillRect(OX,0,COLS*BS,ROWS*BS);
  ctx.strokeStyle="#1f2336";ctx.lineWidth=1;
  for(let r=0;r<=ROWS;r++){ctx.beginPath();ctx.moveTo(OX,r*BS);ctx.lineTo(OX+COLS*BS,r*BS);ctx.stroke();}
  for(let cl=0;cl<=COLS;cl++){ctx.beginPath();ctx.moveTo(OX+cl*BS,0);ctx.lineTo(OX+cl*BS,ROWS*BS);ctx.stroke();}
  let gy=GOAL*BS;ctx.strokeStyle="#FFD700";ctx.lineWidth=2;ctx.setLineDash(new Array(6,4));
  ctx.beginPath();ctx.moveTo(OX,gy);ctx.lineTo(OX+COLS*BS,gy);ctx.stroke();ctx.setLineDash(new Array());
  ctx.fillStyle="#FFD700";ctx.font="bold 12px sans-serif";ctx.fillText("🏁 GOAL LINE",OX+5,gy-6);
  for(let r=0;r<ROWS;r++)for(let cl=0;cl<COLS;cl++)if(brd[r][cl])drawB(cl,r,brd[r][cl],brd[r][cl]==="OBS");
  if(state==="PLAY"&&cur)cur.m.forEach((row,r)=>row.forEach((v,cl)=>{if(v)drawB(cur.x+cl,cur.y+r,cur.c);}));
  if(state!=="PLAY"){
    ctx.fillStyle="rgba(0,0,0,0.84)";ctx.fillRect(0,0,320,540);ctx.textAlign="center";
    if(state==="CLEAR"){
      let lv=LEVELS[curLvl],st=elT<=lv.starT?3:elT<=lv.starT?2:1;
      let pts=(curLvl*500)+500+Math.max(0,Math.floor((60-elT)*40));
      ctx.fillStyle="#4CAF50";ctx.font="bold 26px sans-serif";ctx.fillText(`🎉 ${lv.name} 클리어!`,160,175);
      ctx.font="38px sans-serif";ctx.fillText("⭐".repeat(st)+"☆".repeat(3-st),160,235);
      ctx.fillStyle="#fff";ctx.font="17px sans-serif";ctx.fillText(`클리어 시간: ${elT.toFixed(2)}초`,160,290);
      ctx.fillStyle="#FFD700";ctx.font="bold 22px sans-serif";ctx.fillText(`획득 포인트: ${pts.toLocaleString()} P`,160,330);
      ctx.fillStyle="#4CAF50";ctx.font="bold 15px sans-serif";
      ctx.fillText(curLvl<5?"▶ 클릭 또는 [Enter]로 다음 레벨 도전!":"🏆 모든 레벨을 정복했습니다!",160,390);
    }else{
      ctx.fillStyle="#FF4B4B";ctx.font="bold 30px sans-serif";ctx.fillText("💥 게임 오버!",160,220);
      ctx.fillStyle="#fff";ctx.font="16px sans-serif";ctx.fillText(overMsg,160,265);
      ctx.fillStyle="#4CAF50";ctx.font="bold 15px sans-serif";ctx.fillText("🔄 클릭 또는 [R / Enter]로 다시 도전",160,330);
    }
  }
}
function nextStep(){
  if(state==="CLEAR"&&curLvl<5)setLvl(curLvl+1);
  else init();
}
function loop(t=0){
  if(state==="PLAY"){let dt=t-lT;lT=t;elT=(t-stT)/1000;tmEl.innerText=elT.toFixed(1);dCnt+=dt;if(dCnt>LEVELS[curLvl].spd)drop();}
  draw();if(state==="PLAY")aid=requestAnimationFrame(loop);
}
c.addEventListener("click",()=>state!=="PLAY"?nextStep():c.focus());
document.addEventListener("keydown",e=>{
  if(e.code==="KeyR"){e.preventDefault();init();return;}
  if(state!=="PLAY"&&e.code==="Enter"){e.preventDefault();nextStep();return;}
  if(state!=="PLAY")return;
  if(["ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Space"].includes(e.code))e.preventDefault();
  if(e.code==="ArrowLeft")mv(-1);else if(e.code==="ArrowRight")mv(1);else if(e.code==="ArrowDown")drop();
  else if(e.code==="ArrowUp")rotP();else if(e.code==="Space")hDrop();
});
init();
"""
components.html(game_html, height=730)
