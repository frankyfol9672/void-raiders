# 👾 VOID RAIDERS

A retro arcade space shooter built with Streamlit — playable in the browser, deployable to Streamlit Community Cloud in minutes.

Inspired by classic arcade shooters. Original code, original assets.

---

## Features

- **Canvas-based gameplay** — smooth 60 fps game loop inside a Streamlit iframe
- **3 enemy types** — each with 2-frame animation and unique pixel art style
- **4 destructible barriers** — pixel-cell health system (green → yellow → red → gone)
- **Random UFO bonus enemy** — flies across the top for bonus points
- **10 waves of escalating difficulty** — enemy speed, bullet rate, and rows increase each wave
- **Score multiplier** — increases with each wave cleared
- **Wave clear bonuses** — 500 × wave number added to score on clear
- **3 lives system** — player blinks on hit with temporary invincibility
- **Screen shake + flash effects** — on player hit and enemy kill
- **Particle explosions** — colored particle bursts on every enemy death
- **Pause / Resume** — press P at any time
- **Full restart flow** — Game Over → press R → back to Start Screen
- **Touch-friendly buttons** — on-screen ◄ ► FIRE controls for mobile
- **Retro aesthetic** — neon colors, scanline overlay, CRT glow, star field

---

## Screenshots

> *(Add screenshot here once deployed)*

---

## Local Setup

### Requirements

- Python 3.9+
- pip

### Install & Run

```bash
git clone https://github.com/YOUR_USERNAME/void-raiders.git
cd void-raiders
pip install -r requirements.txt
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (must be public, or you must have a Streamlit Cloud account with private repo access).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **"New app"**.
4. Select your repository, branch (`main`), and set the main file path to `app.py`.
5. Click **"Deploy"** — done. No extra configuration needed.

---

## Repository Structure

```
void-raiders/
├── app.py            # Streamlit shell + embedded HTML/CSS/JS game
├── requirements.txt  # Only streamlit required
└── README.md         # This file
```

The entire game lives inside `app.py` as a self-contained HTML string passed to `st.components.v1.html()`. No external assets, no build tools, no backend.

---

## Controls

| Key | Action |
|-----|--------|
| `←` / `A` | Move left |
| `→` / `D` | Move right |
| `Space` | Fire |
| `P` | Pause / Resume |
| `R` | Restart (Game Over screen) |
| On-screen buttons | Mobile / touch play |

---

## Customization Guide

All tunable values live in the `CFG` object near the top of the JavaScript block inside `app.py`:

```js
const CFG = {
  W: 800, H: 600,                    // Canvas dimensions
  player: {
    speed: 5,                        // Player move speed (px/frame)
    bulletSpeed: 12,                 // Player bullet speed
    fireRate: 280,                   // Minimum ms between shots
  },
  enemies: {
    rows: 4, cols: 10,               // Starting grid size
    baseSpeed: 0.6,                  // Base horizontal step size
    speedBoost: 0.25,                // Speed multiplier per dead enemy
    dropAmount: 18,                  // Pixels enemies drop on wall hit
    bulletChance: 0.00035,           // Per-frame enemy fire probability
    bulletSpeed: 4,                  // Enemy bullet speed
  },
  ufo: {
    speed: 1.8,                      // UFO horizontal speed
    spawnChance: 0.00018,            // Per-ms UFO spawn probability
  },
  barriers: {
    count: 4,                        // Number of barriers
    health: 18,                      // Starting HP per barrier column
  },
  lives: 3,                          // Starting lives
  scoring: {
    byRow: [30, 20, 20, 10],         // Points per enemy by row index
    ufoPool: [50,100,150,200,300],   // UFO point values (random pick)
    waveBonus: 500,                  // Multiplied by wave number on clear
  },
};
```

To make the game harder: increase `bulletChance`, `bulletSpeed`, reduce `fireRate`.
To make it easier: increase `lives`, reduce `bulletChance`, increase `fireRate`.

---

## License

MIT — free to use, modify, and deploy.
