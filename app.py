import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="VOID RAIDERS",
    page_icon="👾",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  body, .stApp { background: #0a0a0f; }
  .block-container { padding-top: 1rem; padding-bottom: 0; max-width: 860px; }
  header, footer { display: none !important; }
  .game-header {
    text-align: center;
    font-family: 'Courier New', monospace;
    color: #00ffff;
    text-transform: uppercase;
    letter-spacing: 0.3em;
    margin-bottom: 0.25rem;
    text-shadow: 0 0 20px #00ffff, 0 0 40px #00ffff44;
  }
  .game-sub {
    text-align: center;
    font-family: 'Courier New', monospace;
    color: #ff00ff;
    font-size: 0.75rem;
    letter-spacing: 0.2em;
    margin-bottom: 0.5rem;
    text-shadow: 0 0 10px #ff00ff;
  }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="game-header">👾 VOID RAIDERS 👾</h1>', unsafe_allow_html=True)
st.markdown('<p class="game-sub">Defend the galaxy — Destroy the void fleet</p>', unsafe_allow_html=True)

GAME_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>VOID RAIDERS</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    background: #0a0a0f;
    display: flex;
    flex-direction: column;
    align-items: center;
    font-family: 'Courier New', monospace;
    overflow: hidden;
    user-select: none;
  }
  #gameCanvas {
    display: block;
    background: #0a0a0f;
    image-rendering: pixelated;
    cursor: none;
  }
  #canvasWrapper {
    position: relative;
    width: 100%;
    max-width: 800px;
  }
  #scanlines {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
      to bottom,
      transparent 0px,
      transparent 3px,
      rgba(0,0,0,0.08) 3px,
      rgba(0,0,0,0.08) 4px
    );
    pointer-events: none;
    z-index: 2;
  }
  #flashOverlay {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: white;
    opacity: 0;
    pointer-events: none;
    z-index: 3;
    transition: opacity 0.05s;
  }
  #controls {
    display: flex;
    gap: 8px;
    margin-top: 8px;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
  }
  .ctrl-group { display: flex; gap: 6px; align-items: center; }
  .ctrl-btn {
    background: #111;
    border: 2px solid #00ffff44;
    color: #00ffff;
    font-family: 'Courier New', monospace;
    font-size: 0.85rem;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    letter-spacing: 0.05em;
    min-width: 52px;
    text-align: center;
    transition: background 0.1s, border-color 0.1s;
    -webkit-tap-highlight-color: transparent;
  }
  .ctrl-btn:active, .ctrl-btn.pressed {
    background: #00ffff22;
    border-color: #00ffff;
  }
  .ctrl-btn.fire-btn {
    border-color: #ff00ff44;
    color: #ff00ff;
    padding: 8px 24px;
  }
  .ctrl-btn.fire-btn:active, .ctrl-btn.fire-btn.pressed {
    background: #ff00ff22;
    border-color: #ff00ff;
  }
  .ctrl-hint {
    color: #ffffff33;
    font-size: 0.65rem;
    letter-spacing: 0.1em;
    text-align: center;
    margin-top: 4px;
    display: none;
  }
  @media (pointer: coarse) { .ctrl-hint { display: block; } }
</style>
</head>
<body>
<div id="canvasWrapper">
  <canvas id="gameCanvas"></canvas>
  <div id="scanlines"></div>
  <div id="flashOverlay"></div>
</div>
<div id="controls">
  <div class="ctrl-group">
    <button class="ctrl-btn" id="btn-left">◄</button>
    <button class="ctrl-btn" id="btn-right">►</button>
  </div>
  <button class="ctrl-btn fire-btn" id="btn-fire">FIRE</button>
</div>
<p class="ctrl-hint">KEYBOARD: ←/→ MOVE  ·  SPACE FIRE  ·  P PAUSE  ·  R RESTART</p>

<script>
// ─── CONFIG ─────────────────────────────────────────────────────────────────
const CFG = {
  W: 800, H: 600,
  player:  { speed: 5, bulletSpeed: 12, fireRate: 280, w: 36, h: 22 },
  enemies: {
    rows: 4, cols: 10,
    startY: 105,
    xPad: 60,
    xGap: 70, yGap: 48,
    baseSpeed: 0.6,
    speedBoost: 0.25,   // added per missing enemy
    dropAmount: 18,
    bulletChance: 0.00035,
    bulletSpeed: 4,
    w: 32, h: 22,
  },
  ufo: { speed: 1.8, spawnChance: 0.00018, w: 52, h: 18 },
  barriers: { count: 4, health: 18, w: 64, h: 36, y: 500 },
  lives: 3,
  scoring: { byRow: [30, 20, 20, 10], ufoPool: [50,100,150,200,300], waveBonus: 500 },
  particles: { count: 10, life: 40, speed: 2.5 },
};

// ─── STATE ───────────────────────────────────────────────────────────────────
let STATE = 'START'; // START | PLAYING | PAUSED | GAMEOVER | WINCLEAR | WIN
let score = 0, lives = CFG.lives, wave = 1;
let multiplier = 1.0;
let player, enemies, playerBullets, enemyBullets, barriers, particles;
let ufo = null;
let enemyDir = 1, enemyMoveTimer = 0, enemyMoveInterval = 800;
let enemyAnimFrame = 0, enemyAnimTimer = 0;
let enemyFireTimer = 0;
let lastTime = 0, lastShot = 0;
let shakeTimer = 0;
let flashEl, canvas, ctx;
let keys = {};
let waveTransTimer = 0; // ms to show wave-clear message
const WAVE_TRANS_MS = 2200;

// ─── CANVAS SETUP ────────────────────────────────────────────────────────────
function initCanvas() {
  canvas = document.getElementById('gameCanvas');
  ctx    = canvas.getContext('2d');
  flashEl = document.getElementById('flashOverlay');

  function resize() {
    const wrapper = document.getElementById('canvasWrapper');
    const w = Math.min(wrapper.clientWidth, CFG.W);
    const scale = w / CFG.W;
    canvas.width  = CFG.W;
    canvas.height = CFG.H;
    canvas.style.width  = w + 'px';
    canvas.style.height = (CFG.H * scale) + 'px';
  }
  resize();
  window.addEventListener('resize', resize);
}

// ─── ENTITY FACTORIES ────────────────────────────────────────────────────────
function makePlayer() {
  return {
    x: CFG.W / 2, y: CFG.H - 48,
    w: CFG.player.w, h: CFG.player.h,
    invincible: 0,
  };
}

function makeEnemy(row, col) {
  const type = row === 0 ? 2 : row <= 2 ? 1 : 0;
  return {
    row, col, type,
    x: CFG.enemies.xPad + col * CFG.enemies.xGap,
    y: CFG.enemies.startY + row * CFG.enemies.yGap,
    w: CFG.enemies.w, h: CFG.enemies.h,
    alive: true,
    points: CFG.scoring.byRow[Math.min(row, CFG.scoring.byRow.length - 1)],
  };
}

function makeBullet(x, y, dy, owner) {
  return { x, y, dy, owner, w: 3, h: 10, alive: true };
}

function makeBarrier(x) {
  const bw = CFG.barriers.w, bh = CFG.barriers.h;
  // Build pixel grid (8×5 block pattern)
  const cols = 8, rows = 5;
  const cells = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      // carve top-center notch (simulate classic barrier shape)
      const notch = (r < 2 && c >= 3 && c <= 4);
      cells.push({ alive: !notch, hp: 3 });
    }
  }
  return { x, y: CFG.barriers.y, w: bw, h: bh, cols, rows, cells };
}

function makeParticle(x, y, color) {
  const angle = Math.random() * Math.PI * 2;
  const speed = Math.random() * CFG.particles.speed + 0.5;
  return {
    x, y,
    vx: Math.cos(angle) * speed,
    vy: Math.sin(angle) * speed,
    life: CFG.particles.life,
    maxLife: CFG.particles.life,
    color,
    size: Math.random() * 3 + 2,
  };
}

function spawnParticles(x, y, color, count) {
  for (let i = 0; i < count; i++) particles.push(makeParticle(x, y, color));
}

function makeUFO() {
  const dir = Math.random() < 0.5 ? 1 : -1;
  return {
    x: dir > 0 ? -CFG.ufo.w : CFG.W + CFG.ufo.w,
    y: 38,
    w: CFG.ufo.w, h: CFG.ufo.h,
    vx: CFG.ufo.speed * dir,
    alive: true,
    pulse: 0,
  };
}

// ─── WAVE INIT ───────────────────────────────────────────────────────────────
function initWave(waveNum) {
  multiplier = 1.0 + (waveNum - 1) * 0.15;
  const rowBoost = Math.min(waveNum - 1, 2); // extra rows up to 2 extra
  const rows = Math.min(CFG.enemies.rows + rowBoost, 6);
  const cols = CFG.enemies.cols;

  enemies = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      enemies.push(makeEnemy(r, c));
    }
  }

  enemyDir = 1;
  enemyMoveInterval = Math.max(200, 800 - (waveNum - 1) * 60);
  enemyMoveTimer = 0;
  enemyFireTimer = 0;
  ufo = null;
  playerBullets = [];
  enemyBullets  = [];
  particles     = [];
}

function initGame() {
  score = 0; lives = CFG.lives; wave = 1;
  shakeTimer = 0;
  player = makePlayer();
  barriers = [];
  const gap = (CFG.W - CFG.barriers.count * CFG.barriers.w) / (CFG.barriers.count + 1);
  for (let i = 0; i < CFG.barriers.count; i++) {
    barriers.push(makeBarrier(gap + i * (CFG.barriers.w + gap)));
  }
  initWave(1);
  STATE = 'PLAYING';
  lastTime = performance.now();
}

// ─── INPUT ───────────────────────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  keys[e.code] = true;
  if (e.code === 'Space') e.preventDefault();
  if (e.code === 'ArrowLeft' || e.code === 'ArrowRight') e.preventDefault();

  if (STATE === 'START' && e.code === 'Space') initGame();
  if ((STATE === 'GAMEOVER' || STATE === 'WIN') && e.code === 'KeyR') {
    STATE = 'START';
    shakeTimer = 0;
  }
  if (STATE === 'PLAYING' && e.code === 'KeyP') STATE = 'PAUSED';
  else if (STATE === 'PAUSED' && e.code === 'KeyP') {
    STATE = 'PLAYING';
    lastTime = performance.now();
  }
  if (STATE === 'WINCLEAR' && e.code === 'Space') advanceWave();
});
document.addEventListener('keyup', e => { keys[e.code] = false; });

function setupTouchBtn(id, code) {
  const btn = document.getElementById(id);
  if (!btn) return;
  const press   = () => { keys[code] = true;  btn.classList.add('pressed'); };
  const release = () => { keys[code] = false; btn.classList.remove('pressed'); };
  btn.addEventListener('pointerdown',  press);
  btn.addEventListener('pointerup',    release);
  btn.addEventListener('pointerleave', release);
  btn.addEventListener('contextmenu',  e => e.preventDefault());
}
setupTouchBtn('btn-left',  'ArrowLeft');
setupTouchBtn('btn-right', 'ArrowRight');
setupTouchBtn('btn-fire',  'Space');

// ─── AABB COLLISION ──────────────────────────────────────────────────────────
function overlaps(a, b) {
  const aw = a.w / 2, bw = b.w / 2;
  const ah = a.h / 2, bh = b.h / 2;
  return Math.abs(a.x - b.x) < aw + bw && Math.abs(a.y - b.y) < ah + bh;
}

// Barrier cell hit test
function hitBarrier(bullet) {
  // Test bullet tip and tail so fast bullets don't tunnel through thin cells
  const testPoints = [
    { x: bullet.x, y: bullet.y - bullet.h / 2 },
    { x: bullet.x, y: bullet.y },
    { x: bullet.x, y: bullet.y + bullet.h / 2 },
  ];
  for (const bar of barriers) {
    const cw = bar.w / bar.cols, ch = bar.h / bar.rows;
    for (const pt of testPoints) {
      const bx = pt.x - bar.x + bar.w / 2;
      const by = pt.y - bar.y;
      if (bx < 0 || bx >= bar.w || by < 0 || by >= bar.h) continue;
      const col = Math.min(Math.floor(bx / cw), bar.cols - 1);
      const row = Math.min(Math.floor(by / ch), bar.rows - 1);
      const idx = row * bar.cols + col;
      if (bar.cells[idx] && bar.cells[idx].alive) {
        bar.cells[idx].hp--;
        if (bar.cells[idx].hp <= 0) bar.cells[idx].alive = false;
        return true;
      }
    }
  }
  return false;
}

// ─── WAVE ADVANCE ────────────────────────────────────────────────────────────
function advanceWave() {
  wave++;
  if (wave > 10) { STATE = 'WIN'; return; }
  initWave(wave);
  STATE = 'PLAYING';
  lastTime = performance.now();
}

// ─── SCREEN FLASH ────────────────────────────────────────────────────────────
function flash(opacity, duration) {
  flashEl.style.opacity = opacity;
  flashEl.style.transition = 'none';
  requestAnimationFrame(() => {
    flashEl.style.transition = `opacity ${duration}ms`;
    requestAnimationFrame(() => { flashEl.style.opacity = 0; });
  });
}

// ─── UPDATE ──────────────────────────────────────────────────────────────────
function update(dt) {
  if (STATE !== 'PLAYING') return;

  // Player movement
  const spd = CFG.player.speed;
  const hw = player.w / 2;
  if ((keys['ArrowLeft'] || keys['KeyA']) && player.x - hw > 0)
    player.x -= spd;
  if ((keys['ArrowRight'] || keys['KeyD']) && player.x + hw < CFG.W)
    player.x += spd;

  // Player shoot
  const now = performance.now();
  if ((keys['Space']) && now - lastShot > CFG.player.fireRate) {
    playerBullets.push(makeBullet(player.x, player.y - player.h / 2, -CFG.player.bulletSpeed, 'player'));
    lastShot = now;
  }

  // Player invincibility countdown
  if (player.invincible > 0) player.invincible -= dt;

  // Move player bullets
  for (const b of playerBullets) {
    b.y += b.dy;
    if (b.y < -10) b.alive = false;
  }

  // Move enemy bullets
  for (const b of enemyBullets) {
    b.y += b.dy;
    if (b.y > CFG.H + 10) b.alive = false;
  }

  // Enemy movement (step-based)
  enemyMoveTimer += dt;
  const aliveEnemies = enemies.filter(e => e.alive);
  const speedMult = 1 + (enemies.length - aliveEnemies.length) * CFG.enemies.speedBoost / enemies.length;
  const interval  = Math.max(80, enemyMoveInterval / speedMult);

  if (enemyMoveTimer >= interval) {
    enemyMoveTimer = 0;
    // Check if any enemy would hit a wall after stepping
    let hitWall = false;
    const step = CFG.enemies.baseSpeed * 18;
    for (const e of aliveEnemies) {
      const nx = e.x + step * enemyDir;
      if (nx - e.w / 2 < 4 || nx + e.w / 2 > CFG.W - 4) { hitWall = true; break; }
    }
    if (hitWall) {
      enemyDir *= -1;
      for (const e of aliveEnemies) e.y += CFG.enemies.dropAmount;
    } else {
      for (const e of aliveEnemies) e.x += step * enemyDir;
    }
  }

  // Enemy fire — independent timer, not tied to movement cadence
  enemyFireTimer += dt;
  const fireInterval = Math.max(400, 1400 - wave * 80);
  if (enemyFireTimer >= fireInterval && aliveEnemies.length > 0) {
    enemyFireTimer = 0;
    // Fire from 1-3 random enemies per interval depending on wave
    const salvo = Math.min(3, 1 + Math.floor(wave / 3));
    const shuffled = aliveEnemies.slice().sort(() => Math.random() - 0.5);
    for (let s = 0; s < salvo && s < shuffled.length; s++) {
      const shooter = shuffled[s];
      enemyBullets.push(makeBullet(shooter.x, shooter.y + shooter.h / 2, CFG.enemies.bulletSpeed + wave * 0.35, 'enemy'));
    }
  }

  // Enemy animation
  enemyAnimTimer += dt;
  if (enemyAnimTimer > 500) { enemyAnimTimer = 0; enemyAnimFrame ^= 1; }

  // UFO spawn
  if (!ufo && Math.random() < CFG.ufo.spawnChance * dt) ufo = makeUFO();

  // UFO movement
  if (ufo) {
    ufo.x += ufo.vx;
    ufo.pulse = (ufo.pulse + dt * 0.006) % (Math.PI * 2);
    if (ufo.x < -ufo.w * 2 || ufo.x > CFG.W + ufo.w * 2) ufo = null;
  }

  // Particles
  for (const p of particles) {
    p.x += p.vx; p.y += p.vy; p.life -= 1;
    p.vy += 0.05; // gravity
  }

  // ── Collision: player bullets vs enemies ──
  for (const b of playerBullets) {
    if (!b.alive) continue;
    // vs UFO
    if (ufo) {
      const uRect = { x: ufo.x, y: ufo.y, w: ufo.w, h: ufo.h };
      const bRect = { x: b.x,   y: b.y,   w: b.w,   h: b.h   };
      if (overlaps(bRect, uRect)) {
        b.alive = false;
        const pts = CFG.scoring.ufoPool[Math.floor(Math.random() * CFG.scoring.ufoPool.length)];
        score += Math.round(pts * multiplier);
        spawnParticles(ufo.x, ufo.y, '#ff3030', 12);
        flash(0.25, 120);
        ufo = null;
        continue;
      }
    }
    // vs enemies
    for (const e of aliveEnemies) {
      if (!b.alive) break;
      const eRect = { x: e.x, y: e.y, w: e.w * 1.1, h: e.h };
      const bRect = { x: b.x, y: b.y, w: b.w, h: b.h };
      if (overlaps(bRect, eRect)) {
        b.alive = false;
        e.alive = false;
        const colors = ['#ff00ff', '#00ff88', '#ffff00'];
        spawnParticles(e.x, e.y, colors[e.type], CFG.particles.count);
        score += Math.round(e.points * multiplier);
        flash(0.15, 80);
        break;
      }
    }
    // vs barriers
    if (b.alive && hitBarrier(b)) b.alive = false;
  }

  // ── Collision: enemy bullets vs player ──
  for (const b of enemyBullets) {
    if (!b.alive) continue;
    if (player.invincible > 0) continue;
    const pRect = { x: player.x, y: player.y, w: player.w * 0.85, h: player.h };
    const bRect = { x: b.x, y: b.y, w: b.w, h: b.h };
    if (overlaps(bRect, pRect)) {
      b.alive = false;
      lives--;
      player.invincible = 2200;
      spawnParticles(player.x, player.y, '#00ffff', 15);
      flash(0.5, 200);
      shakeTimer = 400;
      if (lives <= 0) { STATE = 'GAMEOVER'; return; }
    }
    // vs barriers
    if (b.alive && hitBarrier(b)) b.alive = false;
  }

  // ── Enemies reaching barriers or bottom ──
  for (const e of aliveEnemies) {
    if (e.y + e.h / 2 >= CFG.barriers.y) {
      // Damage barrier cells below enemy
      for (const bar of barriers) {
        if (Math.abs(e.x - (bar.x + bar.w / 2)) < bar.w * 0.8) {
          for (const cell of bar.cells) { if (cell.alive && Math.random() < 0.3) cell.alive = false; }
        }
      }
    }
    if (e.y + e.h / 2 >= CFG.H - 20) {
      STATE = 'GAMEOVER';
      return;
    }
  }

  // ── Wave clear check ──
  if (aliveEnemies.length === 0 && STATE === 'PLAYING') {
    score += CFG.scoring.waveBonus * wave;
    STATE = 'WINCLEAR';
    waveTransTimer = 0;
  }

  // Wave transition auto-advance (after delay)
  if (STATE === 'WINCLEAR') {
    waveTransTimer += dt;
    if (waveTransTimer >= WAVE_TRANS_MS) advanceWave();
  }

  // Cleanup dead entities
  playerBullets = playerBullets.filter(b => b.alive);
  enemyBullets  = enemyBullets.filter(b => b.alive);
  particles     = particles.filter(p => p.life > 0);

  // Screen shake
  if (shakeTimer > 0) shakeTimer -= dt;
}

// ─── DRAW HELPERS ────────────────────────────────────────────────────────────
function drawText(text, x, y, opts = {}) {
  ctx.save();
  ctx.font = (opts.style || '') + ' ' + (opts.size || 16) + 'px "Courier New", monospace';
  ctx.fillStyle = opts.color || '#ffffff';
  ctx.textAlign = opts.align || 'center';
  ctx.textBaseline = 'middle';
  if (opts.shadow) {
    ctx.shadowColor = opts.shadow;
    ctx.shadowBlur  = opts.shadowBlur || 12;
  }
  if (opts.letterSpacing) {
    // manual letter spacing
    const chars = text.split('');
    const totalW = chars.reduce((a, c) => a + ctx.measureText(c).width, 0)
                 + (chars.length - 1) * opts.letterSpacing;
    let cx = x - totalW / 2;
    ctx.textAlign = 'left';
    for (const ch of chars) {
      ctx.fillText(ch, cx, y);
      cx += ctx.measureText(ch).width + opts.letterSpacing;
    }
  } else {
    ctx.fillText(text, x, y);
  }
  ctx.restore();
}

function drawPlayer(x, y, alpha) {
  ctx.save();
  ctx.globalAlpha = alpha;
  // Main hull
  ctx.fillStyle = '#00ffff';
  ctx.shadowColor = '#00ffff';
  ctx.shadowBlur = 10;
  ctx.beginPath();
  ctx.moveTo(x, y - 11);
  ctx.lineTo(x + 18, y + 11);
  ctx.lineTo(x + 8,  y + 6);
  ctx.lineTo(x - 8,  y + 6);
  ctx.lineTo(x - 18, y + 11);
  ctx.closePath();
  ctx.fill();
  // Cockpit
  ctx.fillStyle = '#ffffff';
  ctx.shadowBlur = 6;
  ctx.beginPath();
  ctx.moveTo(x, y - 6);
  ctx.lineTo(x + 5, y + 2);
  ctx.lineTo(x - 5, y + 2);
  ctx.closePath();
  ctx.fill();
  // Engine glow
  ctx.fillStyle = '#00ffff88';
  ctx.shadowColor = '#00ffff';
  ctx.shadowBlur = 12;
  ctx.fillRect(x - 6, y + 7, 4, 5);
  ctx.fillRect(x + 2, y + 7, 4, 5);
  ctx.restore();
}

const ENEMY_SHAPES = [
  // Type 0 — Bottom rows — crabby
  (x, y, f) => {
    ctx.fillStyle = '#ffff00';
    ctx.shadowColor = '#ffff00';
    ctx.shadowBlur = 8;
    // body
    ctx.fillRect(x - 12, y - 7, 24, 14);
    // legs
    const legX = f ? [-16, -10, 10, 16] : [-14, -8, 8, 14];
    for (const lx of legX) ctx.fillRect(x + lx - 2, y + 4, 4, 6);
    // eyes
    ctx.fillStyle = '#0a0a0f';
    ctx.fillRect(x - 7, y - 4, 5, 5);
    ctx.fillRect(x + 2,  y - 4, 5, 5);
    // antennae
    ctx.fillStyle = '#ffff00';
    ctx.fillRect(x - 10, y - 12, 3, 6);
    ctx.fillRect(x + 7,  y - 12, 3, 6);
  },
  // Type 1 — Mid rows — squid
  (x, y, f) => {
    ctx.fillStyle = '#00ff88';
    ctx.shadowColor = '#00ff88';
    ctx.shadowBlur = 8;
    // dome
    ctx.beginPath();
    ctx.ellipse(x, y - 4, 12, 9, 0, Math.PI, 0);
    ctx.fill();
    // body
    ctx.fillRect(x - 12, y - 4, 24, 10);
    // tentacles
    const tPos = f ? [-10,-4,4,10] : [-12,-5,5,11];
    for (const tp of tPos) {
      ctx.fillRect(x + tp, y + 6, 3, 7);
    }
    // eyes
    ctx.fillStyle = '#0a0a0f';
    ctx.fillRect(x - 6, y - 3, 4, 4);
    ctx.fillRect(x + 2,  y - 3, 4, 4);
  },
  // Type 2 — Top rows — octopus
  (x, y, f) => {
    ctx.fillStyle = '#ff00ff';
    ctx.shadowColor = '#ff00ff';
    ctx.shadowBlur = 10;
    // dome + spikes
    ctx.beginPath();
    ctx.arc(x, y, 11, Math.PI, 0);
    ctx.fill();
    // spikes
    ctx.beginPath();
    if (f) {
      ctx.moveTo(x - 11, y); ctx.lineTo(x - 16, y - 5); ctx.lineTo(x - 8, y - 2);
      ctx.moveTo(x + 11, y); ctx.lineTo(x + 16, y - 5); ctx.lineTo(x + 8, y - 2);
    } else {
      ctx.moveTo(x - 9, y - 6); ctx.lineTo(x - 14, y - 2); ctx.lineTo(x - 7, y - 1);
      ctx.moveTo(x + 9, y - 6); ctx.lineTo(x + 14, y - 2); ctx.lineTo(x + 7, y - 1);
    }
    ctx.fill();
    ctx.fillRect(x - 12, y - 2, 24, 12);
    // tentacles
    ctx.fillStyle = '#ff00ff';
    const tPos = f ? [-10,-3,3,10] : [-11,-4,4,11];
    for (const tp of tPos) ctx.fillRect(x + tp, y + 10, 4, 6);
    // eyes
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(x - 6, y + 1, 4, 4);
    ctx.fillRect(x + 2,  y + 1, 4, 4);
    ctx.fillStyle = '#0a0a0f';
    ctx.fillRect(x - 5, y + 2, 2, 2);
    ctx.fillRect(x + 3,  y + 2, 2, 2);
  },
];

function drawEnemy(e) {
  ctx.save();
  ENEMY_SHAPES[e.type](e.x, e.y, enemyAnimFrame === 1);
  ctx.restore();
}

function drawUFO(u) {
  ctx.save();
  const glow = 0.7 + 0.3 * Math.sin(u.pulse);
  ctx.shadowColor = '#ff3030';
  ctx.shadowBlur  = 14 * glow;
  // Hull
  ctx.fillStyle = '#cc1111';
  ctx.beginPath();
  ctx.ellipse(u.x, u.y, 26, 8, 0, 0, Math.PI * 2);
  ctx.fill();
  // Dome
  ctx.fillStyle = '#ff6666';
  ctx.beginPath();
  ctx.ellipse(u.x, u.y - 5, 13, 7, 0, Math.PI, 0);
  ctx.fill();
  // Lights
  const lColors = ['#ffff00', '#00ff88', '#ff00ff', '#00ffff'];
  for (let i = 0; i < 4; i++) {
    const lx = u.x - 18 + i * 12;
    ctx.fillStyle = lColors[(i + Math.floor(u.pulse * 2)) % 4];
    ctx.beginPath();
    ctx.arc(lx, u.y + 2, 3, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

function drawBarrier(bar) {
  const cw = bar.w / bar.cols, ch = bar.h / bar.rows;
  for (let r = 0; r < bar.rows; r++) {
    for (let c = 0; c < bar.cols; c++) {
      const cell = bar.cells[r * bar.cols + c];
      if (!cell.alive) continue;
      const ratio = cell.hp / 3;
      let color;
      if (ratio > 0.66) color = '#00ff88';
      else if (ratio > 0.33) color = '#ffff00';
      else color = '#ff4400';
      ctx.fillStyle = color;
      ctx.shadowColor = color;
      ctx.shadowBlur = 4;
      ctx.fillRect(
        Math.round(bar.x + c * cw) + 1,
        Math.round(bar.y + r * ch) + 1,
        Math.floor(cw) - 2,
        Math.floor(ch) - 2,
      );
    }
  }
}

function drawBullet(b) {
  ctx.save();
  if (b.owner === 'player') {
    ctx.fillStyle = '#00ffff';
    ctx.shadowColor = '#00ffff';
    ctx.shadowBlur = 8;
  } else {
    ctx.fillStyle = '#ff4444';
    ctx.shadowColor = '#ff0000';
    ctx.shadowBlur = 6;
  }
  ctx.fillRect(b.x - b.w / 2, b.y - b.h / 2, b.w, b.h);
  ctx.restore();
}

function drawParticle(p) {
  ctx.save();
  ctx.globalAlpha = p.life / p.maxLife;
  ctx.fillStyle = p.color;
  ctx.shadowColor = p.color;
  ctx.shadowBlur = 4;
  ctx.fillRect(Math.round(p.x - p.size / 2), Math.round(p.y - p.size / 2), Math.round(p.size), Math.round(p.size));
  ctx.restore();
}

function drawHUD() {
  // Score
  drawText('SCORE', 80, 16, { size: 11, color: '#ffffff55', align: 'center' });
  drawText(String(score).padStart(6, '0'), 80, 32, { size: 18, color: '#ffffff', shadow: '#ffffff', shadowBlur: 8, align: 'center' });

  // Lives
  drawText('LIVES', CFG.W / 2, 16, { size: 11, color: '#ffffff55', align: 'center' });
  for (let i = 0; i < lives; i++) {
    ctx.save();
    ctx.globalAlpha = 0.9;
    drawPlayer(CFG.W / 2 - (lives - 1) * 14 + i * 28, 34, 1);
    ctx.restore();
  }

  // Wave
  drawText('WAVE', CFG.W - 80, 16, { size: 11, color: '#ffffff55', align: 'center' });
  drawText(String(wave).padStart(2, '0'), CFG.W - 80, 32, { size: 18, color: '#ffff00', shadow: '#ffff00', shadowBlur: 8, align: 'center' });

  // Multiplier if > 1
  if (multiplier > 1.05) {
    drawText(`×${multiplier.toFixed(1)}`, CFG.W - 80, 50, { size: 12, color: '#ff00ff', shadow: '#ff00ff' });
  }

  // Divider line
  ctx.strokeStyle = '#ffffff22';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(0, 56); ctx.lineTo(CFG.W, 56);
  ctx.stroke();

  // Controls strip — always visible below divider
  const hints = ['←/A MOVE', '→/D MOVE', 'SPC FIRE', 'P PAUSE', 'R RESTART'];
  const hintColors = ['#ffffff44', '#ffffff44', '#ffffff44', '#ffff0077', '#ffffff44'];
  const slotW = CFG.W / hints.length;
  for (let i = 0; i < hints.length; i++) {
    drawText(hints[i], slotW * i + slotW / 2, 68, { size: 10, color: hintColors[i], align: 'center' });
  }

  // Second divider under hints
  ctx.strokeStyle = '#ffffff11';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(0, 78); ctx.lineTo(CFG.W, 78);
  ctx.stroke();
}

function drawStartScreen() {
  // Dim overlay
  ctx.fillStyle = 'rgba(0,0,0,0.6)';
  ctx.fillRect(0, 0, CFG.W, CFG.H);

  drawText('VOID RAIDERS', CFG.W / 2, 140, {
    size: 52, color: '#00ffff', shadow: '#00ffff', shadowBlur: 30, letterSpacing: 8
  });
  drawText('— DEFEND THE GALAXY —', CFG.W / 2, 200, {
    size: 16, color: '#ff00ff', shadow: '#ff00ff', shadowBlur: 12, letterSpacing: 4
  });

  // Enemy legend
  const legend = [
    { type: 2, pts: 30, label: '= 30 PTS' },
    { type: 1, pts: 20, label: '= 20 PTS' },
    { type: 0, pts: 10, label: '= 10 PTS' },
  ];
  let ly = 260;
  for (const item of legend) {
    ctx.save();
    enemyAnimFrame = 0;
    ENEMY_SHAPES[item.type](CFG.W / 2 - 80, ly, false);
    ctx.restore();
    drawText(item.label, CFG.W / 2 + 30, ly, { size: 14, color: '#ffffff88', align: 'left' });
    ly += 44;
  }

  // UFO row
  const fakeUfo = { x: CFG.W / 2 - 80, y: ly, w: CFG.ufo.w, h: CFG.ufo.h, pulse: 0 };
  drawUFO(fakeUfo);
  drawText('= ??? PTS', CFG.W / 2 + 30, ly, { size: 14, color: '#ff3030', align: 'left', shadow: '#ff3030' });

  drawText('CONTROLS', CFG.W / 2, 415, { size: 12, color: '#ffffff44', letterSpacing: 3 });
  const ctrlLines = ['← / A  ·  MOVE LEFT', '→ / D  ·  MOVE RIGHT', 'SPACE  ·  FIRE', 'P  ·  PAUSE', 'R  ·  RESTART'];
  for (let i = 0; i < ctrlLines.length; i++) {
    drawText(ctrlLines[i], CFG.W / 2, 438 + i * 20, { size: 13, color: '#ffffff66' });
  }

  // Blink PRESS SPACE
  const blink = Math.floor(performance.now() / 500) % 2 === 0;
  if (blink) {
    drawText('PRESS SPACE TO START', CFG.W / 2, 562, {
      size: 18, color: '#ffff00', shadow: '#ffff00', shadowBlur: 16, letterSpacing: 3
    });
  }
}

function drawGameOverScreen() {
  ctx.fillStyle = 'rgba(0,0,0,0.72)';
  ctx.fillRect(0, 0, CFG.W, CFG.H);

  drawText('GAME OVER', CFG.W / 2, CFG.H / 2 - 90, {
    size: 60, color: '#ff0000', shadow: '#ff0000', shadowBlur: 30, letterSpacing: 6
  });
  drawText('FINAL SCORE', CFG.W / 2, CFG.H / 2 - 10, { size: 14, color: '#ffffff77', letterSpacing: 3 });
  drawText(String(score).padStart(6, '0'), CFG.W / 2, CFG.H / 2 + 30, {
    size: 44, color: '#ffffff', shadow: '#ffffff', shadowBlur: 16
  });
  drawText('WAVE REACHED: ' + wave, CFG.W / 2, CFG.H / 2 + 80, { size: 16, color: '#ffff0088' });

  const blink = Math.floor(performance.now() / 600) % 2 === 0;
  if (blink) {
    drawText('PRESS R TO PLAY AGAIN', CFG.W / 2, CFG.H / 2 + 130, {
      size: 18, color: '#00ffff', shadow: '#00ffff', shadowBlur: 14, letterSpacing: 3
    });
  }
}

function drawWinScreen() {
  ctx.fillStyle = 'rgba(0,0,0,0.72)';
  ctx.fillRect(0, 0, CFG.W, CFG.H);
  drawText('VICTORY!', CFG.W / 2, CFG.H / 2 - 70, {
    size: 64, color: '#ffff00', shadow: '#ffff00', shadowBlur: 40, letterSpacing: 8
  });
  drawText('ALL WAVES CLEARED!', CFG.W / 2, CFG.H / 2, { size: 20, color: '#00ff88', shadow: '#00ff88', letterSpacing: 3 });
  drawText('FINAL SCORE: ' + String(score).padStart(6, '0'), CFG.W / 2, CFG.H / 2 + 50, {
    size: 26, color: '#ffffff', shadow: '#ffffff', shadowBlur: 12
  });
  const blink = Math.floor(performance.now() / 600) % 2 === 0;
  if (blink) {
    drawText('PRESS R TO PLAY AGAIN', CFG.W / 2, CFG.H / 2 + 120, {
      size: 18, color: '#00ffff', shadow: '#00ffff', shadowBlur: 14, letterSpacing: 3
    });
  }
}

function drawWaveClear() {
  ctx.fillStyle = 'rgba(0,0,0,0.5)';
  ctx.fillRect(0, 0, CFG.W, CFG.H);
  drawText('WAVE ' + wave + ' CLEARED!', CFG.W / 2, CFG.H / 2 - 30, {
    size: 42, color: '#00ff88', shadow: '#00ff88', shadowBlur: 28, letterSpacing: 5
  });
  drawText('BONUS: +' + (CFG.scoring.waveBonus * wave), CFG.W / 2, CFG.H / 2 + 30, {
    size: 24, color: '#ffff00', shadow: '#ffff00', shadowBlur: 16
  });
  const blink = Math.floor(performance.now() / 500) % 2 === 0;
  if (blink) {
    drawText('PRESS SPACE TO CONTINUE', CFG.W / 2, CFG.H / 2 + 90, {
      size: 16, color: '#ffffff88', letterSpacing: 2
    });
  }
}

function drawPause() {
  ctx.fillStyle = 'rgba(0,0,0,0.55)';
  ctx.fillRect(0, 0, CFG.W, CFG.H);
  drawText('PAUSED', CFG.W / 2, CFG.H / 2, {
    size: 56, color: '#00ffff', shadow: '#00ffff', shadowBlur: 30, letterSpacing: 8
  });
  drawText('PRESS P TO RESUME', CFG.W / 2, CFG.H / 2 + 70, {
    size: 18, color: '#ffffff66', letterSpacing: 3
  });
}

// ─── RENDER ──────────────────────────────────────────────────────────────────
function render() {
  ctx.save();

  // Screen shake — only during active play
  if (shakeTimer > 0 && (STATE === 'PLAYING' || STATE === 'GAMEOVER')) {
    const mag = Math.min(shakeTimer / 100, 4);
    ctx.translate(
      (Math.random() - 0.5) * mag * 2,
      (Math.random() - 0.5) * mag * 2,
    );
  }

  // Background
  ctx.fillStyle = '#0a0a0f';
  ctx.fillRect(0, 0, CFG.W, CFG.H);

  // Stars (deterministic via index)
  ctx.fillStyle = '#ffffff';
  for (let i = 0; i < 60; i++) {
    const sx = ((i * 137 + 11) % CFG.W);
    const sy = ((i * 97  + 7)  % CFG.H);
    const br = (i % 3 === 0) ? 0.7 : 0.25;
    ctx.globalAlpha = br + 0.15 * Math.sin(performance.now() * 0.001 + i);
    ctx.fillRect(sx, sy, 1, 1);
  }
  ctx.globalAlpha = 1;

  if (STATE === 'START') {
    drawStartScreen();
    ctx.restore();
    return;
  }

  // HUD
  drawHUD();

  // Game entities
  for (const bar of barriers) drawBarrier(bar);
  for (const e of enemies.filter(e => e.alive)) drawEnemy(e);
  if (ufo) drawUFO(ufo);
  for (const b of playerBullets) drawBullet(b);
  for (const b of enemyBullets)  drawBullet(b);
  for (const p of particles)     drawParticle(p);

  // Player (blink when invincible)
  const showPlayer = player.invincible <= 0 || Math.floor(player.invincible / 150) % 2 === 0;
  if (showPlayer) drawPlayer(player.x, player.y, 1);

  // Bottom line
  ctx.strokeStyle = '#00ffff44';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0, CFG.H - 4); ctx.lineTo(CFG.W, CFG.H - 4);
  ctx.stroke();

  // Overlay states
  if (STATE === 'GAMEOVER')  drawGameOverScreen();
  if (STATE === 'WIN')       drawWinScreen();
  if (STATE === 'WINCLEAR')  drawWaveClear();
  if (STATE === 'PAUSED')    drawPause();

  ctx.restore();
}

// ─── MAIN LOOP ────────────────────────────────────────────────────────────────
function loop(ts) {
  const dt = Math.min(ts - lastTime, 50); // cap at 50ms to avoid spiral
  lastTime = ts;

  // Handle R key globally
  if ((STATE === 'GAMEOVER' || STATE === 'WIN') && keys['KeyR']) {
    STATE = 'START';
    shakeTimer = 0;
    keys['KeyR'] = false;
  }

  update(dt);
  render();
  requestAnimationFrame(loop);
}

// ─── BOOT ─────────────────────────────────────────────────────────────────────
initCanvas();
// Init dummy state so first render has something to draw
player = makePlayer();
enemies = []; playerBullets = []; enemyBullets = []; barriers = []; particles = [];
lastTime = performance.now();
requestAnimationFrame(loop);
</script>
</body>
</html>
"""

components.html(GAME_HTML, height=720, scrolling=False)
