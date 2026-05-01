# Deploying to Railway

The Substack agent is a long-running Telegram bot. Railway is the easiest free-tier
host that keeps it always-on so you can chat with it from anywhere.

## One-time setup (5 minutes)

### 1. Sign up
- Go to https://railway.app
- Click **Login with GitHub** and authorize.
- Railway gives you $5 of free credit per month, enough for this bot.

### 2. Create the project
- Click **New Project** → **Deploy from GitHub repo**.
- Select `uvstharun/substack-agent`.
- Railway auto-detects Python and installs `requirements.txt`.
- It reads the `Procfile` and starts the bot as a `worker` (no public port needed).

### 3. Add environment variables
In the project dashboard click **Variables** and add:

| Name                  | Value                                |
|-----------------------|--------------------------------------|
| `ANTHROPIC_API_KEY`   | your Anthropic key                   |
| `TELEGRAM_BOT_TOKEN`  | your bot token from @BotFather       |
| `TELEGRAM_CHAT_ID`    | your Telegram chat id                |
| `DEFAULT_MODEL`       | `claude-sonnet-4-20250514` (optional)|
| `STORAGE_PATH`        | `/app/storage` (optional)            |

Railway redeploys automatically when you save variables.

### 4. Watch the deploy
- Click the **Deployments** tab.
- Wait for the green checkmark (~2 minutes for first build).
- Open the **Logs** tab. You should see:
  ```
  Telegram bot starting...
  ```

### 5. Test it
- Open Telegram and send `/start` to your bot.
- It should reply within seconds.

## Pushing updates

Just `git push` to GitHub. Railway auto-redeploys on every push to `main`.

```bash
git add .
git commit -m "Update prompts"
git push
```

## Important notes

### Filesystem is ephemeral
Railway wipes the disk on every redeploy. That means `storage/daily/`,
`storage/topics_*.json`, etc. start empty after each deploy.

This is fine for now because the bot's job is to generate content you copy
into Substack. If you later want persistent memory (e.g. so the duplicate
detector remembers older topics across deploys), add a Railway Volume:
- Project → Settings → **Volumes** → mount `/app/storage`.

### Costs
- Idle: a few cents/month.
- Heavy use (~50 Claude calls/day): expect ~$3-8/month in Claude API costs
  on top of the free Railway credit.
- Watch the **Metrics** tab in Railway and your Anthropic console.

### Stopping the bot
- Project → Settings → **Pause Project**.
- Resume any time without reconfiguring.

## Troubleshooting

**Bot doesn't reply:**
- Check Logs for errors. Usually a missing env var.
- Confirm `TELEGRAM_CHAT_ID` matches your actual chat (run `/start` first
  and check the chat id in the bot's incoming update logs).

**"Conflict: terminated by other getUpdates request":**
- The bot is running both locally AND on Railway. Stop the local one.

**Build fails on `pip install`:**
- Check `requirements.txt`. Try removing optional packages.
