import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="스피드 타워 쌓기", page_icon="🧱", layout="centered")

st.title("🧱 초고속 타워 쌓기 (Speed Stacker)")
st.markdown("블록을 빠르게 내려서 **빨간색 목표선**에 가장 짧은 시간 안에 도달하세요! *(줄이 완성되어도 사라지지 않습니다)*")

game_html = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
  body {
    background-color: #0e1117;
    color: #ffffff;
    font-family: 'Malgun Gothic', sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    margin: 0;
    padding: 10px;
    user-select: none;
  }
  .header {
    display: flex;
    justify-content: space-between;
    width: 300px;
    margin-bottom: 10px;
    font-size: 18px;
    font-weight: bold;
  }
  .timer { color: #00ffcc; }
  .best { color: #ffd700; }
  canvas {
    border: 3px solid #444;
    background-color: #161b22;
    box-shadow: 0 0 20px rgba(0,0,0,0.5);
  }
  .controls {
    margin-top: 12px;
    font-size: 13px;
    color: #aaa;
    text-align: center;
    line-height: 1.6;
  }
  button {
    margin-top: 10px;
    padding: 8px 20px;
    font-size: 15px;
    font-weight: bold;
    background-color: #ff4b4b;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
  }
  button:hover { background-color: #ff3333; }
</style>
</head>
<body>

<div class="header">
  <div>⏱️ 시간: <span id="timer" class="timer">0.00</span>초</div>
  <div>🏆 최고: <span id="best" class="best">-</span></div>
</div>

<canvas id="game" width="300" height="600"></canvas>

<button onclick="resetGame()">🔄 다시 시작 (R)</button>

<div class="controls">
  <b>[조작법]</b> 게임 화면을 한 번 클릭 후 키보드 사용<br>
  ⬅️ ➡️ 이동 | ⬆️ 회전 | ⬇️ 빠른 낙하 | <b>Space</b> 즉시 내리기
</div>

<script>
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const COLS = 10;
const ROWS = 20;
const BLOCK_SIZE = 30;
const GOAL_ROW = 5; // 위에서 5번째 줄 (바닥에서 15칸 높이)에 도달하면 승리

const COLORS = [
  null,
  '#FF0D72', // T
  '#0DC2FF', // I
  '#0DFF72', // S
  '#F538FF', // Z
  '#FF8E0D', // L
  '#FFE138', // O
  '#3877FF'  // J
];

const SHAPES = [
  [],
  [[0,1,0],[1,1,1],[0,0,0]], // T
  [[0,2,0,0],[0,2,0,0],[0,2,0,0],[0,2,0,0]], // I
  [[0,3,3],[3,3,0],[0,0,0]], // S
  [[4,4,0],[0,4,4],[0,0,0]], // Z
  [[0,0,5],[5,5,5],[0,0,0]], // L
  [[6,6],[6,6]],             // O
  [[7,0,0],[7,7,7],[0,0,0]]  // J
];

let board = [];
let player = { pos: {x: 0, y: 0}, matrix: null };
let dropCounter = 0;
let dropInterval = 600; // 기본 낙하 속도 (ms)
let lastTime = 0;
let startTime = 0;
let elapsedTime = 0;
let isGameOver = false;
let isWin = false;
let bestTime = localStorage.getItem('stacker_best') || null;

if (bestTime) {
  document.getElementById('best').innerText = parseFloat(bestTime).toFixed(2) + '초';
}

function createBoard() {
  return Array.from({length: ROWS}, () => Array(COLS).fill(0));
}

function drawMatrix(matrix, offset) {
  matrix.forEach((row, y) => {
    row.forEach((value, x) => {
      if (value !== 0) {
        ctx.fillStyle = COLORS[value];
        ctx.fillRect((x + offset.x) * BLOCK_SIZE, (y + offset.y) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
        ctx.strokeStyle = '#161b22';
        ctx.lineWidth = 2;
        ctx.strokeRect((x + offset.x) * BLOCK_SIZE, (y + offset.y) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
      }
    });
  });
}

function drawGoalLine() {
  const y = GOAL_ROW * BLOCK_SIZE;
  ctx.save();
  ctx.beginPath();
  ctx.setLineDash([8, 6]);
  ctx.moveTo(0, y);
  ctx.lineTo(canvas.width, y);
  ctx.strokeStyle = '#ff4b4b';
  ctx.lineWidth = 3;
  ctx.stroke();

  ctx.fillStyle = '#ff4b4b';
  ctx.font = 'bold 12px Malgun Gothic';
  ctx.fillText('🚩 GOAL (목표 지점)', 8, y - 6);
  ctx.restore();
}

function draw() {
  ctx.fillStyle = '#161b22';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // 그리드 배경선
  ctx.strokeStyle = '#21262d';
  ctx.lineWidth = 1;
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      ctx.strokeRect(c * BLOCK_SIZE, r * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
    }
  }

  drawMatrix(board, {x: 0, y: 0});
  if (!isWin) {
    drawMatrix(player.matrix, player.pos);
  }
  drawGoalLine();

  if (isWin) {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.75)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#00ffcc';
    ctx.font = 'bold 28px Malgun Gothic';
    ctx.textAlign = 'center';
    ctx.fillText('🎉 목표 도달 성공!', canvas.width / 2, canvas.height / 2 - 20);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 20px Malgun Gothic';
    ctx.fillText(`기록: ${elapsedTime.toFixed(2)}초`, canvas.width / 2, canvas.height / 2 + 20);
    ctx.textAlign = 'left';
  }
}

function collide(board, player) {
  const [m, o] = [player.matrix, player.pos];
  for (let y = 0; y < m.length; ++y) {
    for (let x = 0; x < m[y].length; ++x) {
      if (m[y][x] !== 0 && (board[y + o.y] && board[y + o.y][x + o.x]) !== 0) {
        return true;
      }
    }
  }
  return false;
}

function merge(board, player) {
  player.matrix.forEach((row, y) => {
    row.forEach((value, x) => {
      if (value !== 0) {
        if (y + player.pos.y >= 0) {
          board[y + player.pos.y][x + player.pos.x] = value;
        }
      }
    });
  });
}

function checkWin() {
  // GOAL_ROW 또는 그 위쪽에 블록이 하나라도 고정되면 승리
  for (let r = 0; r <= GOAL_ROW; r++) {
    for (let c = 0; c < COLS; c++) {
      if (board[r][c] !== 0) {
        return true;
      }
    }
  }
  return false;
}

function playerDrop() {
  player.pos.y++;
  if (collide(board, player)) {
    player.pos.y--;
    merge(board, player);
    if (checkWin()) {
      isWin = true;
      if (!bestTime || elapsedTime < parseFloat(bestTime)) {
        bestTime = elapsedTime.toFixed(2);
        localStorage.setItem('stacker_best', bestTime);
        document.getElementById('best').innerText = bestTime + '초';
      }
      return;
    }
    playerReset();
  }
  dropCounter = 0;
}

function playerHardDrop() {
  while (!collide(board, player)) {
    player.pos.y++;
  }
  player.pos.y--;
  merge(board, player);
  if (checkWin()) {
    isWin = true;
    if (!bestTime || elapsedTime < parseFloat(bestTime)) {
      bestTime = elapsedTime.toFixed(2);
      localStorage.setItem('stacker_best', bestTime);
      document.getElementById('best').innerText = bestTime + '초';
    }
    return;
  }
  playerReset();
  dropCounter = 0;
}

function playerMove(dir) {
  player.pos.x += dir;
  if (collide(board, player)) {
    player.pos.x -= dir;
  }
}

function rotate(matrix, dir) {
  for (let y = 0; y < matrix.length; ++y) {
    for (let x = 0; x < y; ++x) {
      [matrix[x][y], matrix[y][x]] = [matrix[y][x], matrix[x][y]];
    }
  }
  if (dir > 0) matrix.forEach(row => row.reverse());
  else matrix.reverse();
}

function playerRotate(dir) {
  const pos = player.pos.x;
  let offset = 1;
  rotate(player.matrix, dir);
  while (collide(board, player)) {
    player.pos.x += offset;
    offset = -(offset + (offset > 0 ? 1 : -1));
    if (offset > player.matrix[0].length) {
      rotate(player.matrix, -dir);
      player.pos.x = pos;
      return;
    }
  }
}

function playerReset() {
  const typeId = Math.floor(Math.random() * 7) + 1;
  player.matrix = SHAPES[typeId].map(row => [...row]);
  player.pos.y = 0;
  player.pos.x = Math.floor(COLS / 2) - Math.floor(player.matrix[0].length / 2);
}

function update(time = 0) {
  if (!isWin) {
    const deltaTime = time - lastTime;
    lastTime = time;
    dropCounter += deltaTime;

    if (dropCounter > dropInterval) {
      playerDrop();
    }

    elapsedTime = (performance.now() - startTime) / 1000;
    document.getElementById('timer').innerText = elapsedTime.toFixed(2);
  }
  draw();
  requestAnimationFrame(update);
}

function resetGame() {
  board = createBoard();
  isWin = false;
  startTime = performance.now();
  elapsedTime = 0;
  dropCounter = 0;
  playerReset();
}

document.addEventListener('keydown', event => {
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(event.code)) {
    event.preventDefault();
  }
  if (event.code === 'KeyR') {
    resetGame();
    return;
  }
  if (isWin) return;

  if (event.code === 'ArrowLeft') playerMove(-1);
  else if (event.code === 'ArrowRight') playerMove(1);
  else if (event.code === 'ArrowDown') playerDrop();
  else if (event.code === 'ArrowUp') playerRotate(1);
  else if (event.code === 'Space') playerHardDrop();
});

resetGame();
update();
</script>
</body>
</html>
"""

components.html(game_html, height=740)

