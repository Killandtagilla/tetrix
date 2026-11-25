import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="스피드 타워 쌓기", page_icon="🧱", layout="centered")

st.title("🧱 초고속 타워 쌓기: 장애물 에디션")
st.markdown("강철 블록, 움직이는 바, 레이저 빔을 피해 **빨간색 목표선**에 가장 빠르게 도달하세요!")

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
    font-size: 16px;
    font-weight: bold;
  }
  .timer { color: #00ffcc; }
  .best { color: #ffd700; }
  canvas {
    border: 3px solid #444;
    background-color: #161b22;
    box-shadow: 0 0 20px rgba(0,0,0,0.5);
  }
  .legend {
    display: flex;
    gap: 12px;
    margin-top: 8px;
    font-size: 12px;
    color: #ccc;
  }
  .controls {
    margin-top: 10px;
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
  <div>⏱️ <span id="timer" class="timer">0.00</span>초</div>
  <div>🏆 최고: <span id="best" class="best">-</span></div>
</div>

<canvas id="game" width="300" height="600"></canvas>

<div class="legend">
  <span>⬛ 강철벽(고정)</span>
  <span>🟥 이동 바(충돌)</span>
  <span>⚡ 레이저(블록 파괴)</span>
</div>

<button onclick="resetGame()">🔄 다시 시작 (R)</button>

<div class="controls">
  <b>[조작법]</b> 게임 화면 클릭 후 키보드 사용<br>
  ⬅️ ➡️ 이동 | ⬆️ 회전 | ⬇️ 빠른 낙하 | <b>Space</b> 즉시 내리기
</div>

<script>
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');

const COLS = 10;
const ROWS = 20;
const BLOCK_SIZE = 30;
const GOAL_ROW = 5;

const COLORS = [
  null,
  '#FF0D72', // 1: T
  '#0DC2FF', // 2: I
  '#0DFF72', // 3: S
  '#F538FF', // 4: Z
  '#FF8E0D', // 5: L
  '#FFE138', // 6: O
  '#3877FF', // 7: J
  '#6e7681'  // 8: 고정 강철 장애물
];

const SHAPES = [
  [],
  [[0, 1, 0], [1, 1, 1], [0, 0, 0]],             // T
  [[0, 2, 0, 0], [0, 2, 0, 0], [0, 2, 0, 0], [0, 2, 0, 0]], // I
  [[0, 3, 3], [3, 3, 0], [0, 0, 0]],             // S
  [[4, 4, 0], [0, 4, 4], [0, 0, 0]],             // Z
  [[0, 0, 5], [5, 5, 5], [0, 0, 0]],             // L
  [[6, 6], [6, 6]],                               // O
  [[7, 0, 0], [7, 7, 7], [0, 0, 0]]              // J
];

let board = [];
let player = { pos: {x: 0, y: 0}, matrix: null };
let dropCounter = 0;
let dropInterval = 600;
let lastTime = 0;
let startTime = 0;
let elapsedTime = 0;
let isWin = false;
let bestTime = localStorage.getItem('stacker_best_v2') || null;

// 1. 움직이는 방해 바
let movingBar = {
  x: 0,
  y: GOAL_ROW + 4, // 9행
  width: 3,
  dir: 1,
  timer: 0,
  interval: 260
};

// 2. 주기적 레이저 빔 (특정 열의 최상단 블록 파괴)
let laser = {
  col: -1,
  state: 'idle', // 'idle' -> 'warning' -> 'fire'
  timer: 0
};

let earnedStars = "";
let earnedPoints = 0;

if (bestTime) {
  document.getElementById('best').innerText = parseFloat(bestTime).toFixed(2) + '초';
}

function createBoard() {
  return Array.from({length: ROWS}, () => Array(COLS).fill(0));
}

// 강철 장애물 생성 (한 행에 최대 1개씩 배치하여 길 막힘 방지)
function spawnStaticObstacles() {
  const candidateRows =;
  candidateRows.forEach(r => {
    const c = Math.floor(Math.random() * COLS);
    board[r][c] = 8;
  });
}

function calculateReward(time) {
  if (time < 12.0) {
    earnedStars = "⭐⭐⭐";
    earnedPoints = 1000 + Math.floor((12.0 - time) * 100);
  } else if (time < 18.0) {
    earnedStars = "⭐⭐☆";
    earnedPoints = 600 + Math.floor((18.0 - time) * 50);
  } else {
    earnedStars = "⭐☆☆";
    earnedPoints = Math.max(100, 300 - Math.floor((time - 18.0) * 10));
  }
}

function drawCell(x, y, color, isHazard = false) {
  ctx.fillStyle = color;
  ctx.fillRect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
  ctx.strokeStyle = '#161b22';
  ctx.lineWidth = 2;
  ctx.strokeRect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);

  if (isHazard) {
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x * BLOCK_SIZE + 6, y * BLOCK_SIZE + 6);
    ctx.lineTo((x + 1) * BLOCK_SIZE - 6, (y + 1) * BLOCK_SIZE - 6);
    ctx.moveTo((x + 1) * BLOCK_SIZE - 6, y * BLOCK_SIZE + 6);
    ctx.lineTo(x * BLOCK_SIZE + 6, (y + 1) * BLOCK_SIZE - 6);
    ctx.stroke();
  }
}

function drawMatrix(matrix, offset) {
  matrix.forEach((row, y) => {
    row.forEach((value, x) => {
      if (value !== 0) {
        drawCell(x + offset.x, y + offset.y, COLORS[value], value === 8);
      }
    });
  });
}

function drawObstacles() {
  // 움직이는 바 그리기
  for (let i = 0; i < movingBar.width; i++) {
    drawCell(movingBar.x + i, movingBar.y, '#ff4b4b', true);
  }

  // 레이저 경고 및 발사 효과 그리기
  if (laser.col !== -1) {
    const lx = laser.col * BLOCK_SIZE;
    if (laser.state === 'warning') {
      ctx.fillStyle = 'rgba(255, 215, 0, 0.18)';
      ctx.fillRect(lx, 0, BLOCK_SIZE, canvas.height);
      ctx.fillStyle = '#ffd700';
      ctx.font = 'bold 14px Malgun Gothic';
      ctx.fillText('⚠️', lx + 6, 22);
    } else if (laser.state === 'fire') {
      ctx.fillStyle = 'rgba(255, 50, 50, 0.65)';
      ctx.fillRect(lx + 6, 0, BLOCK_SIZE - 12, canvas.height);
    }
  }
}

function drawGoalLine() {
  const y = GOAL_ROW * BLOCK_SIZE;
  ctx.save();
  ctx.beginPath();
  ctx.setLineDash([6, 4]);
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
  drawObstacles();

  if (!isWin) {
    drawMatrix(player.matrix, player.pos);
  }
  drawGoalLine();

  if (isWin) {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.82)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = '#ffd700';
    ctx.lineWidth = 2;
    ctx.strokeRect(25, canvas.height / 2 - 115, canvas.width - 50, 230);

    ctx.textAlign = 'center';
    ctx.fillStyle = '#00ffcc';
    ctx.font = 'bold 24px Malgun Gothic';
    ctx.fillText('🎉 목표 도달 성공!', canvas.width / 2, canvas.height / 2 - 70);

    ctx.font = '34px Malgun Gothic';
    ctx.fillText(earnedStars, canvas.width / 2, canvas.height / 2 - 20);

    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 18px Malgun Gothic';
    ctx.fillText(`⏱️ 기록: ${elapsedTime.toFixed(2)}초`, canvas.width / 2, canvas.height / 2 + 25);

    ctx.fillStyle = '#ffd700';
    ctx.font = 'bold 22px Malgun Gothic';
    ctx.fillText(`💰 +${earnedPoints.toLocaleString()} P`, canvas.width / 2, canvas.height / 2 + 65);

    ctx.fillStyle = '#aaaaaa';
    ctx.font = '13px Malgun Gothic';
    ctx.fillText('R 키를 눌러 다시 도전하세요', canvas.width / 2, canvas.height / 2 + 98);
    ctx.textAlign = 'left';
  }
}

function collide(board, player) {
  const [m, o] = [player.matrix, player.pos];
  for (let y = 0; y < m.length; ++y) {
    for (let x = 0; x < m[y].length; ++x) {
      if (m[y][x] !== 0) {
        const by = y + o.y;
        const bx = x + o.x;

        // 벽, 바닥, 고정 블록 충돌
        if (bx < 0 || bx >= COLS || by >= ROWS || (board[by] && board[by][bx]) !== 0) {
          return true;
        }
        // 움직이는 방해 바 충돌
        if (by === movingBar.y && bx >= movingBar.x && bx < movingBar.x + movingBar.width) {
          return true;
        }
      }
    }
  }
  return false;
}

function merge(board, player) {
  player.matrix.forEach((row, y) => {
    row.forEach((value, x) => {
      if (value !== 0 && y + player.pos.y >= 0) {
        board[y + player.pos.y][x + player.pos.x] = value;
      }
    });
  });
}

function checkWin() {
  for (let r = 0; r < GOAL_ROW; r++) {
    for (let c = 0; c < COLS; c++) {
      if (board[r][c] !== 0 && board[r][c] !== 8) {
        return true;
      }
    }
  }
  return false;
}

function handleWin() {
  isWin = true;
  calculateReward(elapsedTime);
  if (!bestTime || elapsedTime < parseFloat(bestTime)) {
    bestTime = elapsedTime.toFixed(2);
    localStorage.setItem('stacker_best_v2', bestTime);
    document.getElementById('best').innerText = bestTime + '초';
  }
}

function playerDrop() {
  player.pos.y++;
  if (collide(board, player)) {
    player.pos.y--;
    merge(board, player);
    if (checkWin()) {
      handleWin();
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
    handleWin();
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
// 입구가 막혀 움직일 수 없는 경우 맨 아래 2줄을 비워 진행 가능하게 유지
if (collide(board, player)) {
board.splice(ROWS - 2, 2);
board.unshift(Array(COLS).fill(0), Array(COLS).fill(0));
}
}
function updateObstacles(deltaTime) {
// 1. 움직이는 방해 바 업데이트
movingBar.timer += deltaTime;
if (movingBar.timer >= movingBar.interval) {
movingBar.timer = 0;
const nextX = movingBar.x + movingBar.dir;
// 벽에 닿거나 이동 경로에 블록이 있으면 방향 반전
let blocked = nextX < 0 || nextX + movingBar.width > COLS;
if (!blocked) {
for (let i = 0; i < movingBar.width; i++) {
if (board[movingBar.y][nextX + i] !== 0) {
blocked = true;
break;
}
}
}
if (blocked) {
movingBar.dir *= -1;
} else {
movingBar.x = nextX;
}
}
// 2. 레이저 빔 업데이트 (3.5초 대기 -> 1.2초 경고 -> 0.25초 발사)
laser.timer += deltaTime;
if (laser.state === 'idle' && laser.timer > 3500) {
laser.col = Math.floor(Math.random() * COLS);
laser.state = 'warning';
laser.timer = 0;
} else if (laser.state === 'warning' && laser.timer > 1200) {
laser.state = 'fire';
laser.timer = 0;
// 해당 열의 가장 위에 있는 플레이어 블록 1칸 제거 (강철벽은 유지)
for (let r = 0; r < ROWS; r++) {
if (board[r][laser.col] !== 0 && board[r][laser.col] !== 8) {
board[r][laser.col] = 0;
break;
}
}
} else if (laser.state === 'fire' && laser.timer > 250) {
laser.state = 'idle';
laser.col = -1;
laser.timer = 0;
}
}
function update(time = 0) {
if (!isWin) {
const deltaTime = time - lastTime;
lastTime = time;
dropCounter += deltaTime;
if (dropCounter > dropInterval) {
playerDrop();
}
updateObstacles(deltaTime);
elapsedTime = (performance.now() - startTime) / 1000;
document.getElementById('timer').innerText = elapsedTime.toFixed(2);
}
draw();
requestAnimationFrame(update);
}
function resetGame() {
board = createBoard();
spawnStaticObstacles();
movingBar.x = 0;
movingBar.dir = 1;
movingBar.timer = 0;
laser = { col: -1, state: 'idle', timer: 0 };
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



"""
components.html(game_html, height=760)
