# 🚂 Railway Deployment Guide

This guide will help you deploy your Snake Survival game to Railway with global leaderboard functionality.

## 🎯 Quick Start

1. **Connect to Railway**
   - Go to [railway.app](https://railway.app)
   - Sign in with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select `tysonsiruno/snake-survival-game`

2. **Add PostgreSQL Database (Optional but Recommended)**
   - In your Railway project, click "+ New"
   - Select "Database" → "Add PostgreSQL"
   - Railway will automatically provide `DATABASE_URL` environment variable
   - Without PostgreSQL, the app will use SQLite (works but not ideal for production)

3. **Add Redis (Optional but Recommended)**
   - Click "+ New" → "Database" → "Add Redis"
   - Railway will automatically provide `REDIS_URL` environment variable
   - Without Redis, rate limiting will use in-memory storage

4. **Configure Environment Variables**

   Railway will automatically set:
   - `PORT` - The port your app should listen on
   - `DATABASE_URL` - PostgreSQL connection string (if you added PostgreSQL)
   - `REDIS_URL` - Redis connection string (if you added Redis)

   You need to manually set these in Railway dashboard:

   **Required:**
   - `SECRET_KEY` - Copy from your `.env` file
   - `FLASK_ENV` = `production`

   **Optional:**
   - `CORS_ORIGINS` - Set to your Railway domain (e.g., `https://your-app.up.railway.app`)
   - `LOG_LEVEL` = `INFO`

5. **Deploy**
   - Railway will automatically build and deploy
   - Watch the build logs for any errors
   - Once deployed, click "Open App" to test

## 🔧 Configuration Files

Railway uses `nixpacks.toml` for build configuration:

```toml
[phases.setup]
nixPkgs = ["python311", "pip"]

[phases.install]
cmds = [
  "python3.11 -m venv /opt/venv",
  ". /opt/venv/bin/activate",
  "pip install --upgrade pip",
  "pip install -r requirements.txt"
]

[start]
cmd = ". /opt/venv/bin/activate && gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT server.app:app"
```

## 🧪 Testing Your Deployment

### 1. Test Game Homepage
- Visit your Railway URL
- You should see the Snake Survival game with purple gradient background
- Game should auto-start after 1 second

### 2. Test Solo Mode
- Play the game using arrow keys or WASD
- Choose difficulty level (Easy → Hacker)
- Toggle Ghost Mode with 'G' key or toggle switch
- Test powerups (scissors, freeze, shield, etc.)

### 3. Test Local Leaderboards
- Complete a game (hit wall, hit yourself, or reach length 50)
- Your score should appear in the local leaderboard (Ghost Mode or Normal Mode)
- Refresh page - leaderboard should persist (localStorage)

### 4. Test Global Leaderboard API
- Complete a game
- Open browser DevTools Console
- Should see "Score submitted to global leaderboard!" message
- Global leaderboard section should show live scores
- Check that API endpoints are working:
  - `/api/leaderboard/global?mode=all&limit=10` should return JSON
  - `/api/leaderboard/submit` should accept POST requests

### 5. Test Mobile
- Open on mobile device or use browser dev tools mobile emulation
- Check that:
  - Background gradient is visible
  - Controls are responsive
  - Game runs smoothly at 60fps
  - Difficulty and leaderboard panels are accessible

## 🐛 Troubleshooting

### Game Loads But Global Leaderboard Shows "Coming soon..."
**Symptoms:** Local leaderboards work, but global leaderboard says "Coming soon..."

**Solutions:**
1. Check browser console for API errors
2. Verify Railway app is running (check Railway dashboard)
3. Test `/health` endpoint - should return `{"status": "healthy"}`
4. Check that `DATABASE_URL` is set (or SQLite fallback is working)

### Build Failures
**Solution:**
1. Check `nixpacks.toml` is using correct Python version (3.11)
2. Verify `requirements.txt` exists at project root
3. Check Railway build logs for specific error messages
4. Make sure `server/` directory exists with `app.py`, `auth.py`, `models.py`

### 500 Internal Server Error
**Solutions:**
1. Check Railway logs for Python errors
2. Verify environment variables are set correctly
3. Make sure `SECRET_KEY` is set
4. Check database connection (if using PostgreSQL)

### Global Leaderboard Not Updating
**Solutions:**
1. Open browser DevTools Console
2. Check for errors when submitting scores
3. Verify `/api/leaderboard/submit` endpoint is accessible
4. Check Railway logs for database errors
5. Make sure rate limiting isn't blocking requests

## 📊 Monitoring

### Railway Dashboard
- Monitor CPU and Memory usage
- Check deployment logs
- View metrics and analytics

### Application Logs
View real-time logs in Railway dashboard:
- API requests (leaderboard submit/fetch)
- Database queries
- Rate limiting events
- Errors and warnings

## 🔐 Security Checklist

Before going to production:

- [ ] Set strong random value for `SECRET_KEY`
- [ ] Set `FLASK_ENV=production`
- [ ] Configure `CORS_ORIGINS` to your actual domain (not `*`)
- [ ] Add PostgreSQL database (don't use SQLite in production)
- [ ] Add Redis for proper rate limiting
- [ ] Enable Railway's custom domain with SSL
- [ ] Review rate limits (currently 200/day, 50/hour)

## 🚀 Performance Tips

1. **Enable PostgreSQL** - Much faster than SQLite for concurrent users
2. **Enable Redis** - Better rate limiting and caching
3. **Single Worker** - Required for eventlet compatibility
4. **Monitor Logs** - Watch for slow queries or bottlenecks

## 📝 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | Auto | 5000 | Server port (Railway sets this) |
| `DATABASE_URL` | Auto | SQLite | PostgreSQL URL (Railway sets this) |
| `REDIS_URL` | Auto | memory | Redis URL (Railway sets this) |
| `SECRET_KEY` | ✅ Yes | - | Flask session secret |
| `FLASK_ENV` | ✅ Yes | development | Set to `production` |
| `CORS_ORIGINS` | Recommended | * | Allowed CORS origins |
| `LOG_LEVEL` | Optional | INFO | Logging level |

## 🎮 Game Features

Once deployed, your game will have:
- **5 Difficulty Levels**: Easy → Medium → Hard → Impossible → Hacker
- **Ghost Mode**: Walk through walls and yourself
- **8 Powerups**: Scissors, Freeze, Shield, Nuke, Speed, Slow, Multiplier, Rainbow
- **Visual Spawn Indicators**: See where apples will spawn next
- **Local Leaderboards**: Top 5 Ghost Mode and Normal Mode runs (localStorage)
- **Global Leaderboards**: Compete with players worldwide
- **Mobile Support**: Touch controls and responsive design

## 🎉 Success!

Your Snake Survival game should now be live on Railway with global leaderboards!

Share the URL with friends and compete for the highest survival time! 🐍

---

**Last Updated:** 2025-10-20
**Railway Build:** Optimized for Railway deployment with PostgreSQL and Redis support
