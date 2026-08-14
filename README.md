# 🚨 StatusWatch

**Real-time incident monitoring for Discord.**

StatusWatch is a Discord application that monitors service incidents and delivers status updates directly to your Discord server, helping your community stay informed without constantly checking external status pages.

---

## ✨ Features

* 🚨 **Real-time incident monitoring**
* 🔔 **Configurable incident notifications**
* 🌐 **Multi-server support**
* ⚙️ **Discord slash commands**
* 🐳 **Docker-ready deployment**
* 🔐 **Environment-based secret management**
* 🪶 **Lightweight and Raspberry Pi friendly**

---

## 🖥️ How It Works

StatusWatch monitors supported incident and service-status information and delivers relevant updates to your configured Discord channel.

┌─────────────────────┐
│   Status Monitoring │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│     StatusWatch     │
│     Discord Bot     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Configured Discord  │
│       Channel       │
└──────────┬──────────┘
           │
           ▼
      🚨 Incident
       Notification

---

## 📋 Requirements

StatusWatch requires:

* Python 3.11+ or Docker
* A Discord application
* A Discord bot
* A Discord bot token
* A Discord server where you have permission to install and configure applications

---

# 🚀 Installation

## 🐳 Docker Installation

Docker is the recommended way to run StatusWatch.

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/StatusWatch.git
```

Enter the repository:

```bash
cd StatusWatch
```

Enter the bot directory:

```bash
cd bot
```

Create your environment file:

```bash
cp .env.example .env
```

Edit the environment file:

```bash
nano .env
```

Add your Discord bot token:

```env
DISCORD_TOKEN=your_bot_token_here
```

Save the file and start StatusWatch:

```bash
docker compose up -d --build
```

Check that the container is running:

```bash
docker ps
```

View the latest StatusWatch logs:

```bash
docker logs --tail 100 discord-status-bot
```

---

# ⚙️ Configuration

StatusWatch uses environment variables for sensitive configuration.

### Environment Variables

| Variable        | Description                      |
| --------------- | -------------------------------- |
| `DISCORD_TOKEN` | Discord bot authentication token |

Your `.env` file should contain:

```env
DISCORD_TOKEN=your_bot_token_here
```

### 🔐 Keep Your Token Private

**Never commit your real `.env` file to GitHub.**

The repository includes:

```text
.env.example
```

The example file contains only a placeholder:

```env
DISCORD_TOKEN=your_bot_token_here
```

Your actual `.env` file should remain on the machine running StatusWatch.

---

# 🤖 Discord Setup

To install StatusWatch:

1. Create a Discord application in the Discord Developer Portal.
2. Add a bot to the application.
3. Generate or reset the bot token.
4. Add the token to your `.env` file.
5. Invite StatusWatch to your Discord server.
6. Start the bot.
7. Use the available slash commands to configure StatusWatch.

StatusWatch supports multiple Discord servers, with configuration maintained independently for each server.

---

# 💬 Commands

StatusWatch uses Discord slash commands for configuration and management.

Available commands may change as development continues.

### `/setincidentchannel`

Configures the Discord channel where incident notifications are posted.

Example:

```text
/setincidentchannel
```

After running the command, follow Discord's prompts to select the desired channel.

Additional commands may be added or changed as StatusWatch develops.

---

# 🐳 Docker Management

All Docker commands should be run from the `bot` directory.

Enter the bot directory:

```bash
cd StatusWatch/bot
```

### Start / Build StatusWatch

```bash
docker compose up -d --build
```

### Start Without Rebuilding

```bash
docker compose up -d
```

### Stop StatusWatch

```bash
docker compose down
```

### Restart StatusWatch

```bash
docker compose restart
```

### Check Container Status

```bash
docker ps
```

### View Logs

```bash
docker logs discord-status-bot
```

### View the Last 100 Log Entries

```bash
docker logs --tail 100 discord-status-bot
```

### Follow Logs Live

```bash
docker logs -f discord-status-bot
```

Press:

```text
Ctrl+C
```

to stop following the logs.

### Rebuild After Code Changes

```bash
docker compose up -d --build
```

### Force a Fresh Container Recreation

```bash
docker compose up -d --build --force-recreate
```

---

# 🔄 Updating StatusWatch

To update an existing installation:

Enter the repository:

```bash
cd StatusWatch
```

Pull the latest changes:

```bash
git pull
```

Enter the bot directory:

```bash
cd bot
```

Rebuild and restart StatusWatch:

```bash
docker compose up -d --build
```

Check the container:

```bash
docker ps
```

Check the logs:

```bash
docker logs --tail 100 discord-status-bot
```

---

# 🛠️ Project Structure

```text
StatusWatch/
│
├── bot/
│   ├── bot.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── docs/
│   ├── index.html
│   ├── terms.html
│   ├── privacy.html
│   └── style.css
│
├── .env.example
├── .gitignore
├── README.md
└── LICENSE
```

> The actual `.env` file is intentionally excluded from the repository.

---

# 🔐 Security

Security is an important part of StatusWatch.

### Never expose your Discord token

Your Discord bot token is a sensitive credential and should never be committed to GitHub.

StatusWatch uses environment variables so the token remains outside the public source code.

The repository contains:

```text
.env.example
```

but should never contain:

```text
.env
```

If your Discord bot token is accidentally exposed, immediately regenerate it through the Discord Developer Portal.

### GitHub Security

If you discover a security vulnerability, avoid publicly posting sensitive details before the issue can be addressed.

Use the repository's available security-reporting or contact mechanisms where appropriate.

---

# 📜 Legal

StatusWatch is an independent third-party Discord application.

It is not owned, operated, sponsored, or endorsed by Discord Inc.

Use of StatusWatch is also subject to applicable Discord Terms of Service, Developer Policy, Community Guidelines, and other relevant Discord policies.

### Legal Documents

**[Terms of Service](https://YOUR-USERNAME.github.io/StatusWatch/terms.html)**

**[Privacy Policy](https://YOUR-USERNAME.github.io/StatusWatch/privacy.html)**

---

# 📦 Dependencies

StatusWatch currently uses:

* [discord.py](https://github.com/Rapptz/discord.py)
* [aiohttp](https://github.com/aio-libs/aiohttp)
* [python-dotenv](https://github.com/theskumar/python-dotenv)

Docker uses:

```text
Python 3.11 Slim
```

---

# 🧭 Project Status

StatusWatch is an actively developed project.

Features, commands, configuration options, and implementation details may change as development continues.

The documentation in this repository represents the current project structure and functionality.

---

# 📄 License

StatusWatch is distributed under the license included in this repository.

See the [`LICENSE`](LICENSE) file for the full license text.

---

<div align="center">

## 🚨 Stay informed. Stay connected.

**StatusWatch — real-time incident monitoring for Discord.**

[Terms of Service](https://YOUR-USERNAME.github.io/StatusWatch/terms.html) • [Privacy Policy](https://YOUR-USERNAME.github.io/StatusWatch/privacy.html)

</div>
