# Telegram Admin Bot (Autonomous AI Agent)

This is an advanced All-in-One Telegram Admin Bot, now enhanced with autonomous AI agent capabilities, web search functionality, and expanded administration commands. It is designed for 24/7 operation, ideally hosted on platforms like Render.

## Features

*   **Autonomous AI Agent**: The bot is configured to act as an intelligent agent, capable of making decisions and utilizing tools to fulfill requests.
*   **Web Search Capability**: Integrated with DuckDuckGo Search, allowing the bot to find information on the web when needed to answer questions or gather data.
*   **AI Chat**: Utilizes Google Gemini AI (`gemini-flash-latest`) for intelligent and natural conversations, now with enhanced reasoning and tool-use capabilities.
*   **Group Reply Interaction**: The bot can respond to messages it's replied to in group chats, even without being explicitly mentioned.
*   **Enhanced Admin Commands**:
    *   `/kick`: Kicks a user from the group.
    *   `/ban`: Bans a user from the group.
    *   `/mute`: Mutes a user (prevents them from sending messages).
    *   `/unmute`: Unmutes a user.
    *   `/warn`: Sends a warning message to a user.
    *   `/purge`: Deletes messages from a replied message up to the command message.
*   **24/7 Hosting**: Configured for deployment on Render using a Flask web server and webhooks.

## Deployment on Render

Follow these steps to deploy your Telegram Admin Bot on Render:

### 1. Prepare Your Files

Ensure you have the following files in your project directory:

*   `app.py`: The main bot script with Flask server integration and AI agent logic.
*   `requirements.txt`: Lists all Python dependencies.

### 2. Create a Render Account

If you don't have one, sign up for a free account at [Render](https://render.com/).

### 3. Create a New Web Service

1.  Log in to your Render dashboard.
2.  Click on **New Web Service**.
3.  Connect your GitHub or GitLab repository where your bot's code is hosted. If you don't use Git, you can manually upload your files or use Render's CLI.

### 4. Configure Your Web Service

Fill in the service details as follows:

*   **Name**: Choose a unique name for your service (e.g., `telegram-admin-bot`).
*   **Region**: Select a region close to your users.
*   **Branch**: `main` (or your primary branch).
*   **Root Directory**: `/` (if your files are at the root of your repository).
*   **Runtime**: `Python 3`
*   **Build Command**: `pip install -r requirements.txt`
*   **Start Command**: `gunicorn app:app` (Render uses Gunicorn by default for Python web services. Ensure `gunicorn` is added to your `requirements.txt` if not already there).

### 5. Add Environment Variables

This is crucial for securing your API keys and tokens. Add the following environment variables:

*   `TELEGRAM_TOKEN`: Your Telegram Bot Token (`7778399973:AAEH2BU6hBHUqseWfdw2kNcX_OFZNYoFoes`)
*   `GEMINI_API_KEY`: Your Google Gemini API Key (`AQ.Ab8RN6LrYDk7IdMQkSy3FeSF47AjeDdHyUonKOg5GbdxmHhCAg`)

### 6. Deploy

Click **Create Web Service**. Render will automatically build and deploy your bot.

### 7. Set Up Telegram Webhook

Once your Render service is deployed, you will get a public URL (e.g., `https://your-service-name.onrender.com`). You need to tell Telegram to send updates to this URL.

You can set the webhook using your browser by navigating to the following URL (replace `YOUR_BOT_TOKEN` and `YOUR_RENDER_URL`):

`https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_RENDER_URL>/<YOUR_BOT_TOKEN>`

**Example:**

`https://api.telegram.org/bot7778399973:AAEH2BU6hBHUqseWfdw2kNcX_OFZNYoFoes/setWebhook?url=https://telegram-admin-bot.onrender.com/7778399973:AAEH2BU6hBHUqseWfdw2kNcX_OFZNYoFoes`

If successful, you should see a JSON response like `{"ok":true,"result":true,"description":"Webhook was set"}`.

Your bot should now be running 24/7 on Render and responding to commands and messages!
