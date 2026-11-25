import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="테트리스 클라이머", page_icon="🧱", layout="centered")

st.title("🧱 테트리스 클라이머 (Tetris Climber)")
st.markdown("고정된 **붉은 장애물**을 피해 블록을 쌓아 **목표 라인(노란 점선)**까지 최대한 빠르게 올라가세요!")

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
  #top-bar {
    width: 320px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: #1e2130;
    padding: 10px 15px;
    border-radius: 8px;
    border: 2px solid #333952;
    margin-bottom: 10px;
    box-sizing: border-box;
  }
  .info-box {
    display: flex;
    flex-direction: column;
    gap: 5px;
    font-size: 16px;
    font-weight: bold;
  }
  #next-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    font-size: 12px;
    color: #aaa;
  }
  #nextCanvas {
    background-color: #131520;
    border: 1px solid #444;
    border-radius: 4px;
    margin-top: 3px;
  }
  #gameCanvas {
    border: 3px solid #4CAF50;
    border-radius: 8px;
    background-color: #1e2130;
    box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    outline: none;
    cursor: pointer;
  }
  #controls-guide {
    margin-top: 10px;
    font-size: 13px;
    color: #bbb;
    text-align: center;
  }
  .btn-group {
    display: flex;
    gap: 8px;
    margin-top: 10px;
  }
  button {
    padding: 8px 14px;
    font-size: 14px;
    font-weight: bold;
    background-color: #2b3044;
    color: white;
    border: 1px solid #4a5270;
    border-radius: 5px;
    cursor: pointer;
  }
  button:hover { background-color: #3c435e; }
  #restartBtn {
    background-color: #4CAF50;
    border: none;
    padding: 10px 25px;
    font-size: 16px;
  }
  #restartBtn:hover { background-color: #45a049; }
</style>
</head>
<body>

<div id="top-bar">
  <div class="info-box">
    <span>⏱️ 시간: <span id="timer">0.0</span>초</span>
    <span>📏 높이: <span id="height">0</span> / 16층</span>
  </div>
  <div id="next-box">
    <span>NEXT</span>
    <canvas id="nextCanvas" width="80" height="60"></canvas>
  </div>
</div>

<canvas id="gameCanvas" width="320" height="560" tabindex="0"></canvas>

<div class="btn-group">
  <button onclick="moveLeft()">⬅️</button>
  <button onclick="playerRotate()">🔄 회전</button>
  <button onclick="moveRight()">➡️</button>
  <button onclick="playerDrop()">⬇️</button>
  <button onclick="hardDrop()">⏬ 낙하</button>
</div>

<div id="controls-guide">
  화면 클릭 후 키보드 조작: ⬅️➡️ 이동 | ⬆️ 회전 | ⬇️ 내리기 | <b>Space</b> 즉시 낙하
</div>

<div class="btn-group">
  <button id="restartBtn" onclick="initGame()" style="display:none;">다시 시작</button>
</div>

<script>
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
const nextCanvas = document.getElementById("nextCanvas");
const nextCtx = nextCanvas.getContext("2d");

const timerEl = document.getElementById("timer");
const heightEl = document.getElementById("height");
const restartBtn = document.getElementById("restartBtn");

const COLS = 10;
const ROWS = 20;
const BLOCK_SIZE = 28;
const OFFSET_X = 20;
const GOAL_ROW = 4;

const SHAPE_DEFS = [
  { color: "#00F0F0", rows: ["0000", "1111", "0000", "0000"] },
  { color: "#F0F000", rows: ["11", "11"] },
  { color: "#A000F0", rows: ["010", "111", "000"] },
  { color: "#2979FF", rows: ["100", "111", "000"] },
  { color: "#FF9100", rows: ["001", "111", "000"] },
  { color: "#00E676", rows: ["011", "110", "000"] },
  { color: "#FF1744", rows: ["110", "011", "000"] }
];

const SHAPES = SHAPE_DEFS.map(def => ({
  color: def.color,
  matrix: def.rows.map(r => r.split("").map(Number))
}));

let board = [];
let currentPiece = null;
let nextPiece = null;
let startTime = 0;
let elapsedTime = 0;
let dropCounter = 0;
let lastTime = 0;
let gameState = "PLAYING";
let animId = null;

function createBoard() {
  const b = Array.from({ length: ROWS }, () => Array(COLS).fill(0));
  const obstacles = [
    { r: 16, c: 2 }, { r: 16, c: 3 },
    { r: 13, c: 6 }, { r: 13, c: 7 },
    { r: 10, c: 1 }, { r: 10, c: 2 },
    { r: 7, c: 4 },  { r: 7, c: 5 }, { r: 7, c: 6 }
  ];
  obstacles.forEach(obs => {
    b[obs.r][obs.c] = "OBS";
  });
  return b;
}

function getRandomPiece() {
  const shape = SHAPES[Math.floor(Math.random() * SHAPES.length)];
  return {
    matrix: shape.matrix.map(row => [...row]),
    color: shape.color,
    x: Math.floor(COLS / 2) - Math.ceil(shape.matrix.length / 2),
    y: 0
  };
}

function initGame() {
  board = createBoard();
  nextPiece = getRandomPiece();
  spawnPiece();
  startTime = performance.now();
  lastTime = startTime;
  dropCounter = 0;
  gameState = "PLAYING";
  restartBtn.style.display = "none";
  heightEl.innerText = "0";
  canvas.focus();

  if (animId) cancelAnimationFrame(animId);
  animId = requestAnimationFrame(update);
}

function spawnPiece() {
  currentPiece = nextPiece;
  nextPiece = getRandomPiece();
  drawNextPiece();

  if (collide(board, currentPiece)) {
    endGame("GAMEOVER");
  }
}

function drawNextPiece() {
  nextCtx.clearRect(0, 0, nextCanvas.width, nextCanvas.height);
  const m = nextPiece.matrix;
  const size = 14;
  const startX = (nextCanvas.width - m.length * size) / 2;
  const startY = (nextCanvas.height - m.length * size) / 2;

  for (let r = 0; r < m.length; r++) {
    for (let c = 0; c < m[r].length; c++) {
      if (m[r][c]) {
        nextCtx.fillStyle = nextPiece.color;
        nextCtx.fillRect(startX + c * size, startY + r * size, size - 1, size - 1);
      }
    }
  }
}

function collide(b, piece) {
  const m = piece.matrix;
  for (let r = 0; r < m.length; r++) {
    for (let c = 0; c < m[r].length; c++) {
      if (m[r][c]) {
        const newY = piece.y + r;
        const newX = piece.x + c;
        if (newX < 0 || newX >= COLS || newY >= ROWS || (newY >= 0 && b[newY][newX] !== 0)) {
          return true;
        }
      }
    }
  }
  return false;
}

function merge(b, piece) {
  const m = piece.matrix;
  let highestRow = ROWS;

  for (let r = 0; r < m.length; r++) {
    for (let c = 0; c < m[r].length; c++) {
      if (m[r][c]) {
        const boardY = piece.y + r;
        const boardX = piece.x + c;
        if (boardY >= 0) {
          b[boardY][boardX] = piece.color;
          if (boardY < highestRow) highestRow = boardY;
        }
      }
    }
  }

  let currentMaxHeight = 0;
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      if (b[r][c] !== 0 && b[r][c] !== "OBS") {
        currentMaxHeight = Math.max(currentMaxHeight, ROWS - r);
      }
    }
  }
  heightEl.innerText = Math.min(16, currentMaxHeight);

  if (highestRow <= GOAL_ROW) {
    endGame("CLEAR");
  }
}

function rotate(matrix) {
  return matrix.map((_, index) => matrix.map(row => row[index]).reverse());
}

function moveLeft() {
  if (gameState !== "PLAYING") return;
  currentPiece.x--;
  if (collide(board, currentPiece)) currentPiece.x++;
}

function moveRight() {
  if (gameState !== "PLAYING") return;
  currentPiece.x++;
  if (collide(board, currentPiece)) currentPiece.x--;
}

function playerRotate() {
  if (gameState !== "PLAYING") return;
  const prevMatrix = currentPiece.matrix;
  currentPiece.matrix = rotate(currentPiece.matrix);
  let offset = 1;
  while (collide(board, currentPiece)) {
    currentPiece.x += offset;
    offset = -(offset + (offset > 0 ? 1 : -1));
    if (offset > currentPiece.matrix.length) {
      currentPiece.matrix = prevMatrix;
      return;
    }
  }
}

function playerDrop() {
  if (gameState !== "PLAYING") return;
  currentPiece.y++;
  if (collide(board, currentPiece)) {
    currentPiece.y--;
    merge(board, currentPiece);
    if (gameState === "PLAYING") {
      spawnPiece();
    }
  }
  dropCounter = 0;
}

function hardDrop() {
  if (gameState !== "PLAYING") return;
  while (!collide(board, currentPiece)) {
    currentPiece.y++;
  }
  currentPiece.y--;
  merge(board, currentPiece);
  if (gameState === "PLAYING") {
    spawnPiece();
  }
  dropCounter = 0;
}

function endGame(state) {
  gameState = state;
  restartBtn.style.display = "inline-block";
}

function calculateScore() {
  let stars = 1;
  if (elapsedTime <= 25.0) stars = 3;
  else if (elapsedTime <= 45.0) stars = 2;

  const timeBonus = Math.max(0, Math.floor((60 - elapsedTime) * 40));
  const totalPoints = 1000 + timeBonus;
  return { stars, totalPoints };
}

function drawBlock(x, y, color, isObs = false) {
  const px = OFFSET_X + x * BLOCK_SIZE;
  const py = y * BLOCK_SIZE;
  
  if (isObs) {
    ctx.fillStyle = "#D32F2F";
    ctx.fillRect(px, py, BLOCK_SIZE - 1, BLOCK_SIZE - 1);
    ctx.strokeStyle = "#FFCDD2";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(px + 4, py + 4);
    ctx.lineTo(px + BLOCK_SIZE - 5, py + BLOCK_SIZE - 5);
    ctx.moveTo(px + BLOCK_SIZE - 5, py + 4);
    ctx.lineTo(px + 4, py + BLOCK_SIZE - 5);
    ctx.stroke();
  } else {
    ctx.fillStyle = color;
    ctx.fillRect(px, py, BLOCK_SIZE - 1, BLOCK_SIZE - 1);
  }
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = "#131520";
  ctx.fillRect(OFFSET_X, 0, COLS * BLOCK_SIZE, ROWS * BLOCK_SIZE);

  ctx.strokeStyle = "#1f2336";
  ctx.lineWidth = 1;
  for (let r = 0; r <= ROWS; r++) {
    ctx.beginPath();
    ctx.moveTo(OFFSET_X, r * BLOCK_SIZE);
    ctx.lineTo(OFFSET_X + COLS * BLOCK_SIZE, r * BLOCK_SIZE);
    ctx.stroke();
  }
  for (let c = 0; c <= COLS; c++) {
    ctx.beginPath();
    ctx.moveTo(OFFSET_X + c * BLOCK_SIZE, 0);
    ctx.lineTo(OFFSET_X + c * BLOCK_SIZE, ROWS * BLOCK_SIZE);
    ctx.stroke();
  }

  const goalY = GOAL_ROW * BLOCK_SIZE;
  ctx.strokeStyle = "#FFD700";
  ctx.lineWidth = 2;
  ctx.setLineDash([6, 4]);
  ctx.beginPath();
  ctx.moveTo(OFFSET_X, goalY);
  ctx.lineTo(OFFSET_X + COLS * BLOCK_SIZE, goalY);
  ctx.stroke();
  ctx.setLineDash([]);
ctx.fillStyle = "#FFD700";
ctx.font = "bold 12px sans-serif";
ctx.fillText("🏁 GOAL LINE (여기까지 쌓으세요!)", OFFSET_X + 5, goalY - 6);
for (let r = 0; r < ROWS; r++) {
for (let c = 0; c < COLS; c++) {
if (board[r][c] === "OBS") {
drawBlock(c, r, null, true);
} else if (board[r][c] !== 0) {
drawBlock(c, r, board[r][c], false);
}
}
}
if (gameState === "PLAYING" && currentPiece) {
const m = currentPiece.matrix;
for (let r = 0; r < m.length; r++) {
for (let c = 0; c < m[r].length; c++) {
if (m[r][c]) {
drawBlock(currentPiece.x + c, currentPiece.y + r, currentPiece.color);
}
}
}
}
if (gameState !== "PLAYING") {
ctx.fillStyle = "rgba(0, 0, 0, 0.82)";
ctx.fillRect(0, 0, canvas.width, canvas.height);
ctx.textAlign = "center";
if (gameState === "CLEAR") {
const { stars, totalPoints } = calculateScore();
const starText = "⭐".repeat(stars) + "☆".repeat(3 - stars);
ctx.fillStyle = "#4CAF50";
ctx.font = "bold 28px sans-serif";
ctx.fillText("🎉 목표 높이 도달!", canvas.width / 2, 190);
ctx.font = "38px sans-serif";
ctx.fillText(starText, canvas.width / 2, 250);
ctx.fillStyle = "#FFFFFF";
ctx.font = "18px sans-serif";
ctx.fillText(클리어 시간: ${elapsedTime.toFixed(2)}초, canvas.width / 2, 305);
ctx.fillStyle = "#FFD700";
ctx.font = "bold 22px sans-serif";
ctx.fillText(획득 포인트: ${totalPoints.toLocaleString()} P, canvas.width / 2, 345);
} else {
ctx.fillStyle = "#FF4B4B";
ctx.font = "bold 30px sans-serif";
ctx.fillText("💥 게임 오버!", canvas.width / 2, 240);
ctx.fillStyle = "#FFFFFF";
ctx.font = "16px sans-serif";
ctx.fillText("블록이 천장에 닿았습니다.", canvas.width / 2, 285);
}
}
}
function update(time = 0) {
if (gameState === "PLAYING") {
const deltaTime = time - lastTime;
lastTime = time;
elapsedTime = (time - startTime) / 1000;
timerEl.innerText = elapsedTime.toFixed(1);
dropCounter += deltaTime;
if (dropCounter > 600) {
playerDrop();
}
}
draw();
if (gameState === "PLAYING") {
animId = requestAnimationFrame(update);
}
}
canvas.addEventListener("click", () => canvas.focus());
window.addEventListener("load", () => {
window.focus();
canvas.focus();
});
document.addEventListener("keydown", event => {
if (gameState !== "PLAYING") return;
if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Space"].includes(event.code)) {
event.preventDefault();
}
if (event.code === "ArrowLeft") moveLeft();
else if (event.code === "ArrowRight") moveRight();
else if (event.code === "ArrowDown") playerDrop();
else if (event.code === "ArrowUp") playerRotate();
else if (event.code === "Space") hardDrop();
});
initGame();



"""
components.html(game_html, height=740)
