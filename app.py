import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="스피드 타워 쌓기", page_icon="🧱", layout="centered")

st.title("🧱 초고속 타워 쌓기 (Speed Stacker)")
st.markdown("움직이는 장애물과 강철 블록을 피해 **빨간색 목표선**에 가장 짧은 시간 안에 도달하세요!")

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
  <div>⏱️ <span id="timer" class="timer">0.00</span>초</div>
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
const GOAL_ROW = 5; // 바닥에서 15칸 높이

const COLORS = [
  null,
  '#FF0D72', // T
  '#0DC2FF', // I
  '#0DFF72', // S
  '#F538FF', // Z
  '#FF8E0D', // L
  '#FFE138', // O
  '#3877FF', // J
  '#6e7681'  // 8: 고정 강철 장애물
];

const SHAPES = [
  [],
  [[0, 1, 0], [1, 1, 1], [0, 0, 0]], // T
  [[0, 2, 0, 0], [0, 2, 0, 0], [0, 2, 0, 0], [0, 2, 0, 0]], // I
  [[0, 3, 3], [3, 3, 0], [0, 0, 0]], // S
  [[4, 4, 0], [0, 4, 4], [0, 0, 0]], // Z
  [[0, 0, 5], [5, 5, 5], [0, 0, 0]], // L
  [[6, 6], [6, 6]], // O
  [[7, 0, 0], [7, 7, 7], [0, 0, 0]] // J
];

let board = [];
let player = { pos: {x: 0, y: 0}, matrix: null };
let dropCounter = 0;
let dropInterval = 600;
let lastTime = 0;
let startTime = 0;
let elapsedTime = 0;
let isWin = false;
let bestTime = localStorage.getItem('stacker_best_obs') || null;

// 움직이는 장애물 바 설정
let movingObstacle = {
  x: 0,
  y: GOAL_ROW + 4, // 9번째 줄에서 좌우 이동
  width: 3,        // 3칸 너비
  dir: 1,
  moveCounter: 0,
  moveInterval: 280 // 0.28초마다 1칸 이동
};

let earnedStars = "";
let earnedPoints = 0;

if (bestTime) {
  document.getElementById('best').innerText = parseFloat(bestTime).toFixed(2) + '초';
}

function createBoard() {
  return Array.from({length: ROWS}, () => Array(COLS).fill(0));
}

// 고정 강철 장애물 생성 (목표선과 움직이는 바를 피해 배치)
function spawnStaticObstacles() {
  let count = 0;
  while (count < 6) {
    const r = Math.floor(Math.random() * 10) + (GOAL_ROW + 2); // 7 ~ 16행 사이
    const c = Math.floor(Math.random() * COLS);
    // 움직이는 바의 행은 비워두고 배치
    if (r !== movingObstacle.y && board[r][c] === 0) {
      board[r][c] = 8;
      count++;
    }
  }
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

function drawBlock(x, y, color, isObstacle = false) {
  ctx.fillStyle = color;
  ctx.fillRect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
  ctx.strokeStyle = '#161b22';
  ctx.lineWidth = 2;
  ctx.strokeRect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);

  // 장애물 전용 X자/빗금 디테일 추가
  if (isObstacle) {
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.45)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x * BLOCK_SIZE + 5, y * BLOCK_SIZE + 5);
    ctx.lineTo((x + 1) * BLOCK_SIZE - 5, (y + 1) * BLOCK_SIZE - 5);
    ctx.moveTo((x + 1) * BLOCK_SIZE - 5, y * BLOCK_SIZE + 5);
    ctx.lineTo(x * BLOCK_SIZE + 5, (y + 1) * BLOCK_SIZE - 5);
    ctx.stroke();
  }
}

function drawMatrix(matrix, offset) {
  matrix.forEach((row, y) => {
    row.forEach((value, x) => {
      if (value !== 0) {
        drawBlock(x + offset.x, y + offset.y, COLORS[value], value === 8);
      }
    });
  });
}

function drawMovingObstacle() {
  for (let i = 0; i < movingObstacle.width; i++) {
    drawBlock(movingObstacle.x + i, movingObstacle.y, '#ff4b4b', true);
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
  drawMovingObstacle();

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
        const boardY = y + o.y;
        const boardX = x + o.x;

        // 보드 경계 및 고정 블록(강철 장애물 포함) 충돌 검사
        if ((board[boardY] && board[boardY][boardX]) !== 0) {
          return true;
        }
        // 움직이는 장애물 바 충돌 검사
        if (
          boardY === movingObstacle.y &&
          boardX >= movingObstacle.x &&
          boardX < movingObstacle.x + movingObstacle.width
        ) {
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
      if (value !== 0) {
        if (y + player.pos.y >= 0) {
          board[y + player.pos.y][x + player.pos.x] = value;
        }
      }
    });
  });
}

// 빨간 목표선을 돌파(r < GOAL_ROW)해야 승리
function checkWin() {
  for (let r = 0; r < GOAL_ROW; r++) {
    for (let c = 0; c < COLS; c++) {
      // 고정 장애물(8)이 아닌 플레이어가 쌓은 블록만 인정
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
    localStorage.setItem('stacker_best_obs', bestTime);
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

  // 스폰 직후 블록이 막혀 더 이상 쌓을 수 없으면 보드 하단 일부 정리(소프트락 방지)
  if (collide(board, player)) {
    board.splice(ROWS - 3, 3);
    board.unshift(...Array.from({length: 3}, () => Array(COLS).fill(0)));
  }
}

function updateMovingObstacle(deltaTime) {
  movingObstacle.moveCounter += deltaTime;
