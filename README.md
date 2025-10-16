# 🐍 Snake Survival Game

An intense survival twist on the classic snake game! Dodge incoming apples instead of eating them, use strategic powerups, and compete for the highest survival time on the **global leaderboard**.

## ✨ Features

- **5 Difficulty Modes**: Easy, Medium, Hard, Impossible, and Hacker
- **Strategic Gameplay**: See exactly where the next apple will spawn
- **8 Unique Powerups**: Including speed boosts, freeze time, shields, and more
- **Ghost Mode**: Practice mode to learn mechanics without dying
- **Local Leaderboards**: Track your best runs for both Ghost and Normal modes
- **🌍 Global Leaderboard**: Compete with players worldwide!
- **Progressive Difficulty**: Game gets harder the longer you survive

## 🎮 How to Play

1. Visit the live game or run locally
2. Use **Arrow Keys** or **WASD** to move
3. Press **Space** to pause
4. Press **G** to toggle Ghost Mode
5. **Objective**: Dodge the charging apples - don't get hit!
6. Apple hits make you grow - reach length 50 and it's game over!

## 💎 Powerups

- ✂️ **Shorten Length** - Remove 5 segments
- 🐢 **Slow Apples** - Reduces apple speed
- ❄️ **Freeze Apples** - Stops all apple movement
- 💎 **2x Points** - Double your survival time score
- 🌈 **Rainbow Mode** - Fabulous visual effect
- ⚡ **Speed Boost** - Move faster to dodge
- 🛡️ **Shield** - Absorbs one apple hit
- 💣 **Nuke** - Destroys all apples on screen (rare!)

## 🎯 Game Modes

- **Normal Mode**: Full challenge - walls and apples kill you
- **Ghost Mode**: Practice mode - pass through walls and yourself (still die at length 50)

## 🚀 Quick Start

### Play Online
Just open the game in your browser - works offline too!

### Run Locally

```bash
# Clone the repository
git clone https://github.com/tysonsiruno/snake-survival-game.git
cd snake-survival-game

# Option 1: Open directly in browser
open index.html

# Option 2: Run with backend (for global leaderboard)
pip install -r requirements.txt
python server/app.py
# Visit http://localhost:5000
```

## 🌐 Backend & Deployment

The game includes an optional Flask backend for the global leaderboard feature.

### Technologies

**Frontend:**
- Pure HTML5/CSS3/JavaScript
- Canvas API for smooth rendering
- LocalStorage for offline leaderboards

**Backend:**
- Flask 3.0+ web framework
- PostgreSQL database
- RESTful API for leaderboard

### API Endpoints

```
GET  /api/leaderboard/global    - Get global leaderboard
POST /api/leaderboard/submit    - Submit a score
GET  /api/leaderboard/stats     - Get global statistics
GET  /health                     - Health check
```

### Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

1. **Fork this repository**
2. **Connect to Railway**:
   - Go to [Railway](https://railway.app)
   - New Project → Deploy from GitHub
   - Select your forked repository
3. **Add Database** (optional):
   - Add PostgreSQL plugin
   - Railway will auto-configure DATABASE_URL
4. **Deploy!**
   - Railway will automatically build and deploy
   - Your game will be live in ~2 minutes

### Environment Variables

```env
# Required for production
SECRET_KEY=your-secret-key

# Optional (Railway provides automatically)
DATABASE_URL=postgresql://...
PORT=5000
```

## 📊 Difficulty Settings

| Difficulty | Apple Spawn Rate | Apple Speed | Growth Amount |
|-----------|------------------|-------------|---------------|
| Easy | 3.5s → 1.5s | 0.12 | 1 → 1 |
| Medium | 3.0s → 1.0s | 0.15 | 1 → 2 |
| Hard | 2.5s → 0.8s | 0.18 | 1 → 3 |
| Impossible | 2.0s → 0.6s | 0.22 | 2 → 4 |
| Hacker | 1.5s → 0.4s | 0.30 | 3 → 5 |

*Growth changes after reaching the "hard mode" threshold time*

## 🏗️ Project Structure

```
snake-survival-game/
├── index.html              # Main game file (playable standalone)
├── README.md
├── server/
│   ├── app.py             # Flask backend
│   └── models.py          # Database models
├── requirements.txt       # Python dependencies
├── Procfile              # Railway/Heroku deployment
├── runtime.txt           # Python version
└── .env.example          # Environment variables template
```

## 🎯 Game Mechanics

### Scoring
- Survival time is your score (in seconds)
- 2x multiplier powerup doubles point gain
- Ghost mode and Normal mode have separate leaderboards

### Apple Behavior
- Apples spawn from screen edges
- They track and chase the snake head
- Apple speed and spawn rate increase over time
- Visual indicators show next spawn location

### Death Conditions
- Hit by an apple (unless you have a shield)
- Hit a wall (Normal mode only)
- Hit yourself (Normal mode only)
- Reach length 50 (always fatal)

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest new powerups or game modes
- Improve the UI/UX
- Optimize performance

## 📄 License

MIT License - Free to use and modify

## 👥 Author

- **Tyson Siruno** - [GitHub](https://github.com/tysonsiruno)

---

**⭐ Star this repo if you enjoy the game!**

**Built with ❤️ using HTML5 Canvas and Flask**
