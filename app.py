import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="스카이 빌더 - 장애물 블록 쌓기", page_icon="🧱", layout="centered")

st.title("🧱 스카이 빌더 (Sky Builder)")
st.markdown("**스페이스바(Space)** 또는 **화면 클릭**으로 블록을 멈춰서 장애물을 피해 20층까지 빠르게 올라가세요!")

# HTML5 Canvas + JavaScript 게임 엔진
game_html = """
<!DOCTYPE html>
<html>
<head>
<style>
  body {
    margin: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    background-color: #0e1117;
    color: white;
    font-family: 'Malgun Gothic', sans-serif;
    user-select: none;
  }
  canvas {
    border: 3px solid #4CAF50;
    border-radius: 8px;
    background-color: #1e2130;
    box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    cursor: pointer;
  }
  #ui-panel {
    width: 400px;
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
    font-size: 18px;
    font-weight: bold;
  }
  button {
    margin-top: 15px;
    padding: 10px 25px;
    font-size: 16px;
    font-weight: bold;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
  }
  button:hover { background-color: #45a049; }
</style>
</head>
<body>

<div id="ui-panel">
  <span>층수: <span id="floor">0</span> / 20</span>
  <span>시간: <span id="timer">0.0</span>초</span>
</div>

<canvas id="gameCanvas" width="400" height="550"></canvas>
<button id="restartBtn" onclick="initGame()" style="display:none;">다시 시작</button>

<script>
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
const floorEl = document.getElementById("floor");
const timerEl = document.getElementById("timer");
const restartBtn = document.getElementById("restartBtn");

const TARGET_FLOORS = 20;
const BLOCK_HEIGHT = 22;
let blocks = [];
let currentBlock = {};
let obstacles = [];
let cameraY = 0;
let startTime = 0;
let elapsedTime = 0;
let gameState = "PLAYING"; // PLAYING, GAMEOVER, CLEAR
let animationId;

function initGame() {
  blocks = [{ x: 100, y: 500, width: 200, color: "#4CAF50" }];
  obstacles = [];
  cameraY = 0;
  gameState = "PLAYING";
  restartBtn.style.display = "none";
  startTime = performance.now();
  
  // 4층 간격으로 움직이는 장애물 생성
  for (let i = 4; i < TARGET_FLOORS; i += 4) {
    obstacles.push({
      floor: i,
      y: 500 - (i * BLOCK_HEIGHT) - 10,
      x: Math.random() * 250,
      width: 110,
      height: 8,
      speed: 2.5 + (i * 0.15),
      dir: Math.random() > 0.5 ? 1 : -1
    });
  }
  
  spawnBlock();
  if (animationId) cancelAnimationFrame(animationId);
  gameLoop();
}

function spawnBlock() {
  const prevBlock = blocks[blocks.length - 1];
  const floor = blocks.length;
  const speed = 3 + (floor * 0.25); // 올라갈수록 빨라짐
  
  currentBlock = {
    x: 0,
    y: prevBlock.y - BLOCK_HEIGHT,
    width: prevBlock.width,
    speed: speed,
    dir: 1,
    color: `hsl(${(floor * 18) % 360}, 75%, 55%)`
  };
  
  // 카메라 시점 위로 이동
  if (floor > 10) {
    cameraY = (floor - 10) * BLOCK_HEIGHT;
  }
}

function placeBlock() {
  if (gameState !== "PLAYING") return;

  const prevBlock = blocks[blocks.length - 1];
  const delta = currentBlock.x - prevBlock.x;
  const overlap = prevBlock.width - Math.abs(delta);

  // 1. 블록을 완전히 놓쳤을 경우
  if (overlap <= 0) {
    endGame("GAMEOVER");
    return;
  }

  // 2. 장애물 충돌 체크
  const currentFloor = blocks.length;
  for (let obs of obstacles) {
    if (obs.floor === currentFloor) {
      if (currentBlock.x < obs.x + obs.width && currentBlock.x + currentBlock.width > obs.x) {
        endGame("GAMEOVER");
        return;
      }
    }
  }

  // 잘린 만큼 블록 크기 조정 후 고정
  currentBlock.width = overlap;
  currentBlock.x = delta > 0 ? currentBlock.x : prevBlock.x;
  blocks.push({ ...currentBlock });
  
  floorEl.innerText = blocks.length - 1;

  // 목표 층수 도달 체크
  if (blocks.length - 1 >= TARGET_FLOORS) {
    endGame("CLEAR");
  } else {
    spawnBlock();
  }
}

function endGame(state) {
  gameState = state;
  restartBtn.style.display = "block";
}

function calculateScore() {
  let stars = 1;
  if (elapsedTime <= 18.0) stars = 3;
  else if (elapsedTime <= 28.0) stars = 2;

  // 기본 1000점 + 시간 보너스 + 남은 블록 너비 보너스
  const timeBonus = Math.max(0, Math.floor((40 - elapsedTime) * 50));
  const widthBonus = Math.floor(blocks[blocks.length - 1].width * 5);
  const totalPoints = 1000 + timeBonus + widthBonus;

  return { stars, totalPoints };
}

function update() {
  if (gameState !== "PLAYING") return;

  elapsedTime = (performance.now() - startTime) / 1000;
  timerEl.innerText = elapsedTime.toFixed(1);

  // 현재 블록 좌우 이동
  currentBlock.x += currentBlock.speed * currentBlock.dir;
  if (currentBlock.x + currentBlock.width > canvas.width) {
    currentBlock.x = canvas.width - currentBlock.width;
    currentBlock.dir = -1;
  } else if (currentBlock.x < 0) {
    currentBlock.x = 0;
    currentBlock.dir = 1;
  }

  // 장애물 좌우 이동
  for (let obs of obstacles) {
    obs.x += obs.speed * obs.dir;
    if (obs.x + obs.width > canvas.width || obs.x < 0) {
      obs.dir *= -1;
    }
  }
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.translate(0, cameraY);

  // 목표 결승선 그리기
  const finishY = 500 - (TARGET_FLOORS * BLOCK_HEIGHT);
  ctx.strokeStyle = "#FFD700";
  ctx.setLineDash([5, 5]);
  ctx.beginPath();
  ctx.moveTo(0, finishY);
  ctx.lineTo(canvas.width, finishY);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = "#FFD700";
  ctx.fillText("🏁 GOAL (20층)", 10, finishY - 5);

  // 쌓인 블록 그리기
  for (let b of blocks) {
    ctx.fillStyle = b.color;
    ctx.fillRect(b.x, b.y, b.width, BLOCK_HEIGHT - 2);
  }

  // 움직이는 현재 블록 그리기
  if (gameState === "PLAYING") {
    ctx.fillStyle = currentBlock.color;
    ctx.fillRect(currentBlock.x, currentBlock.y, currentBlock.width, BLOCK_HEIGHT - 2);
  }

  // 장애물(붉은 레이저) 그리기
  for (let obs of obstacles) {
    ctx.fillStyle = "#FF4B4B";
    ctx.fillRect(obs.x, obs.y, obs.width, obs.height);
  }

  ctx.restore();

  // 게임 종료 오버레이 화면
  if (gameState !== "PLAYING") {
    ctx.fillStyle = "rgba(0, 0, 0, 0.78)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.textAlign = "center";
    if (gameState === "CLEAR") {
      const { stars, totalPoints } = calculateScore();
      const starText = "⭐".repeat(stars) + "☆".repeat(3 - stars);

      ctx.fillStyle = "#4CAF50";
      ctx.font = "bold 32px sans-serif";
      ctx.fillText("🎉 목표 도달 성공!", canvas.width / 2, 180);

      ctx.font = "40px sans-serif";
      ctx.fillText(starText, canvas.width / 2, 245);

      ctx.fillStyle = "#FFFFFF";
      ctx.font = "20px sans-serif";
      ctx.fillText(`클리어 시간: ${elapsedTime.toFixed(2)}초`, canvas.width / 2, 300);
      ctx.fillStyle = "#FFD700";
      ctx.font = "bold 24px sans-serif";
      ctx.fillText(`획득 포인트: ${totalPoints.toLocaleString()} P`, canvas.width / 2, 345);
    } else {
      ctx.fillStyle = "#FF4B4B";
      ctx.font = "bold 34px sans-serif";
      ctx.fillText("💥 게임 오버!", canvas.width / 2, 230);

      ctx.fillStyle = "#FFFFFF";
      ctx.font = "18px sans-serif";
      ctx.fillText("장애물에 부딪혔거나 블록을 놓쳤습니다.", canvas.width / 2, 275);
      ctx.fillText(`도달 층수: ${blocks.length - 1}층`, canvas.width / 2, 310);
    }
  }
}

function gameLoop() {
  update();
  draw();
  animationId = requestAnimationFrame(gameLoop);
}

// 조작 이벤트 (클릭 및 스페이스바)
canvas.addEventListener("mousedown", placeBlock);
window.addEventListener("keydown", (e) => {
  if (e.code === "Space") {
    e.preventDefault();
    placeBlock();
  }
});

initGame();
</script>
</body>
</html>
"""

# 스트림릿 화면에 게임 렌더링
components.html(game_html, height=660)
