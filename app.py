import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="테트리스 클라이머", page_icon="🧱", layout="centered")
st.title("🧱 테트리스 클라이머")
st.markdown("고정된 **붉은 장애물**을 피해 블록을 쌓아 **목표 라인(노란 점선)**까지 최대한 빠르게 올라가세요!")

game_html = """<!DOCTYPE html><html><head><style>
body{margin:0;display:flex;flex-direction:column;align-items:center;background:#0e1117;color:#fff;font-family:sans-serif;user-select:none}
#top{width:320px;display:flex;justify-content:space-between;align-items:center;background:#1e2130;padding:10px 15px;border-radius:8px;border:2px solid #333952;margin-bottom:10px;box-sizing:border-box}
.info{display:flex;flex-direction:column;gap:5px;font-size:16px;font-weight:bold}
#next-box{display:flex;flex-direction:column;align-items:center;font-size:12px;color:#aaa}
#nextC{background:#131520;border:1px solid #444;border-radius:4px;margin-top:3px}
#gameC{border:3px solid #4CAF50;border-radius:8px;background:#1e2130;outline:none;cursor:pointer}
.btns{display:flex;gap:8px;margin-top:10px}
button{padding:8px 14px;font-size:14px;font-weight:bold;background:#2b3044;color:#fff;border:1px solid #4a5270;border-radius:5px;cursor:pointer}
button:hover{background:#3c435e}
#reBtn{background:#4CAF50;border:none;padding:10px 25px;font-size:16px}
</style></head><body>
<div id="top">
  <div class="info"><span>⏱️ 시간: <span id="tm">0.0</span>초</span><span>📏 높이: <span id="ht">0</span> / 16층</span></div>
  <div id="next-box"><span>NEXT</span><canvas id="nextC" width="80" height="60"></canvas></div>
</div>
<canvas id="gameC" width="320" height="560" tabindex="0"></canvas>
<div class="btns">
  <button onclick="mv(-1)">⬅️</button><button onclick="rotP()">🔄 회전</button><button onclick="mv(1)">➡️</button>
  <button onclick="drop()">⬇️</button><button onclick="hDrop()">⏬ 낙하</button>
</div>
<div style="margin-top:8px;font-size:12px;color:#bbb">화면 클릭 후 조작: ⬅️➡️ 이동 | ⬆️ 회전 | ⬇️ 내리기 | <b>Space</b> 즉시 낙하</div>
<div class="btns"><button id="reBtn" onclick="init()" style="display:none">다시 시작</button></div>
<script>
const c=document.getElementById("gameC"),ctx=c.getContext("2d"),nc=document.getElementById("nextC"),nctx=nc.getContext("2d");
const tmEl=document.getElementById("tm"),htEl=document.getElementById("ht"),reBtn=document.getElementById("reBtn");
const COLS=10,ROWS=20,BS=28,OX=20,GOAL=4;
const DEFS=[
  {c:"#00F0F0",r:["0000","1111","0000","0000"]},{c:"#F0F000",r:["11","11"]},{c:"#A000F0",r:["010","111","000"]},
  {c:"#2979FF",r:["100","111","000"]},{c:"#FF9100",r:["001","111","000"]},{c:"#00E676",r:["011","110","000"]},{c:"#FF1744",r:["110","011","000"]}
];
const SHAPES=DEFS.map(d=>({c:d.c,m:d.r.map(s=>s.split("").map(Number))}));
let brd=[],cur=null,nxt=null,stT=0,elT=0,dCnt=0,lT=0,state="PLAY",aid=null;

function mkBrd(){
  let b=Array.from({length:ROWS},()=>Array(COLS).fill(0));
  [[16,2],[16,3],[13,6],[13,7],[10,1],[10,2],[7,4],[7,5],[7,6]].forEach(([r,col])=>b[r][col]="OBS");
  return b;
}
function rndP(){
  let s=SHAPES[Math.floor(Math.random()*SHAPES.length)];
  return{m:s.m.map(r=>[...r]),c:s.c,x:Math.floor(COLS/2)-Math.ceil(s.m.length/2),y:0};
}
function init(){
  brd=mkBrd();nxt=rndP();spawn();stT=performance.now();lT=stT;dCnt=0;state="PLAY";
  reBtn.style.display="none";htEl.innerText="0";c.focus();
  if(aid)cancelAnimationFrame(aid);aid=requestAnimationFrame(loop);
}
function spawn(){
  cur=nxt;nxt=rndP();
  nctx.clearRect(0,0,80,60);
  let m=nxt.m,sz=14,sx=(80-m.length*sz)/2,sy=(60-m.length*sz)/2;
  m.forEach((row,r)=>row.forEach((v,col)=>{if(v){nctx.fillStyle=nxt.c;nctx.fillRect(sx+col*sz,sy+r*sz,sz-1,sz-1);}}));
  if(col(brd,cur))end("OVER");
}
function col(b,p){
  for(let r=0;r<p.m.length;r++)for(let cl=0;cl<p.m[r].length;cl++)
    if(p.m[r][cl]){let ny=p.y+r,nx=p.x+cl;if(nx<0||nx>=COLS||ny>=ROWS||(ny>=0&&b[ny][nx]!==0))return true;}
  return false;
}
function merge(b,p){
  let hi=ROWS;
  p.m.forEach((row,r)=>row.forEach((v,cl)=>{if(v&&p.y+r>=0){b[p.y+r][p.x+cl]=p.c;if(p.y+r<hi)hi=p.y+r;}}));
  let mx=0;
  for(let r=0;r<ROWS;r++)for(let cl=0;cl<COLS;cl++)if(b[r][cl]!==0&&b[r][cl]!=="OBS")mx=Math.max(mx,ROWS-r);
  htEl.innerText=Math.min(16,mx);
  if(hi<=GOAL)end("CLEAR");
}
function mv(d){if(state==="PLAY"){cur.x+=d;if(col(brd,cur))cur.x-=d;}}
function rotP(){
  if(state!=="PLAY")return;
  let pm=cur.m;cur.m=cur.m.map((_,i)=>cur.m.map(r=>r[i]).reverse());
  let off=1;
  while(col(brd,cur)){cur.x+=off;off=-(off+(off>0?1:-1));if(off>cur.m.length){cur.m=pm;return;}}
}
function drop(){
  if(state!=="PLAY")return;
  cur.y++;if(col(brd,cur)){cur.y--;merge(brd,cur);if(state==="PLAY")spawn();}dCnt=0;
}
function hDrop(){
  if(state!=="PLAY")return;
  while(!col(brd,cur))cur.y++;
  cur.y--;merge(brd,cur);if(state==="PLAY")spawn();dCnt=0;
}
function end(s){state=s;reBtn.style.display="inline-block";}
function drawB(x,y,clr,obs=false){
  let px=OX+x*BS,py=y*BS;
  if(obs){
    ctx.fillStyle="#D32F2F";ctx.fillRect(px,py,BS-1,BS-1);ctx.strokeStyle="#FFCDD2";ctx.lineWidth=2;
    ctx.beginPath();ctx.moveTo(px+4,py+4);ctx.lineTo(px+BS-5,py+BS-5);ctx.moveTo(px+BS-5,py+4);ctx.lineTo(px+4,py+BS-5);ctx.stroke();
  }else{ctx.fillStyle=clr;ctx.fillRect(px,py,BS-1,BS-1);}
}
function draw(){
  ctx.clearRect(0,0,320,560);ctx.fillStyle="#131520";ctx.fillRect(OX,0,COLS*BS,ROWS*BS);
  ctx.strokeStyle="#1f2336";ctx.lineWidth=1;
  for(let r=0;r<=ROWS;r++){ctx.beginPath();ctx.moveTo(OX,r*BS);ctx.lineTo(OX+COLS*BS,r*BS);ctx.stroke();}
  for(let cl=0;cl<=COLS;cl++){ctx.beginPath();ctx.moveTo(OX+cl*BS,0);ctx.lineTo(OX+cl*BS,ROWS*BS);ctx.stroke();}
  let gy=GOAL*BS;ctx.strokeStyle="#FFD700";ctx.lineWidth=2;ctx.setLineDash([6,4]);
  ctx.beginPath();ctx.moveTo(OX,gy);ctx.lineTo(OX+COLS*BS,gy);ctx.stroke();ctx.setLineDash([]);
  ctx.fillStyle="#FFD700";ctx.font="bold 12px sans-serif";ctx.fillText("🏁 GOAL LINE",OX+5,gy-6);
  for(let r=0;r<ROWS;r++)for(let cl=0;cl<COLS;cl++)if(brd[r][cl])drawB(cl,r,brd[r][cl],brd[r][cl]==="OBS");
  if(state==="PLAY"&&cur)cur.m.forEach((row,r)=>row.forEach((v,cl)=>{if(v)drawB(cur.x+cl,cur.y+r,cur.c);}));
  if(state!=="PLAY"){
    ctx.fillStyle="rgba(0,0,0,0.82)";ctx.fillRect(0,0,320,560);ctx.textAlign="center";
    if(state==="CLEAR"){
      let st=elT<=25?3:elT<=45?2:1,pts=1000+Math.max(0,Math.floor((60-elT)*40));
      ctx.fillStyle="#4CAF50";ctx.font="bold 28px sans-serif";ctx.fillText("🎉 목표 높이 도달!",160,190);
      ctx.font="38px sans-serif";ctx.fillText("⭐".repeat(st)+"☆".repeat(3-st),160,250);
      ctx.fillStyle="#fff";ctx.font="18px sans-serif";ctx.fillText(`클리어 시간: ${elT.toFixed(2)}초`,160,305);
      ctx.fillStyle="#FFD700";ctx.font="bold 22px sans-serif";ctx.fillText(`획득 포인트: ${pts.toLocaleString()} P`,160,345);
    }else{
      ctx.fillStyle="#FF4B4B";ctx.font="bold 30px sans-serif";ctx.fillText("💥 게임 오버!",160,240);
      ctx.fillStyle="#fff";ctx.font="16px sans-serif";ctx.fillText("블록이 천장에 닿았습니다.",160,285);
    }
  }
}
function loop(t=0){
  if(state==="PLAY"){let dt=t-lT;lT=t;elT=(t-stT)/1000;tmEl.innerText=elT.toFixed(1);dCnt+=dt;if(dCnt>600)drop();}
  draw();if(state==="PLAY")aid=requestAnimationFrame(loop);
}
c.addEventListener("click",()=>c.focus());
document.addEventListener("keydown",e=>{
  if(state!=="PLAY")return;
  if(["ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Space"].includes(e.code))e.preventDefault();
  if(e.code==="ArrowLeft")mv(-1);else if(e.code==="ArrowRight")mv(1);else if(e.code==="ArrowDown")drop();
  else if(e.code==="ArrowUp")rotP();else if(e.code==="Space")hDrop();
});
init();
</script></body></html>"""

components.html(game_html, height=740)
