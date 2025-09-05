# Calendar & Airtable MCP Server - Railway Deployment

## Step 1: Prepare Your Files

Create a new folder with these files:
- `calendar_airtable_server.py` (the main MCP server)
- `web_server.py` (FastAPI wrapper for Railway)
- `requirements.txt` (Python dependencies)
- `railway.toml` (Railway configuration)

## Step 2: Get API Credentials

### Google Calendar API:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Calendar API
4. Create credentials (OAuth 2.0 for web application)
5. Get your access token

### Airtable API:
1. Go to [Airtable](https://airtable.com/create/tokens)
2. Create a new personal access token
3. Give it permissions to read/write your bases
4. Copy your Base ID from your Airtable URL

## Step 3: Deploy to Railway

1. **Sign up for Railway**: Go to [railway.app](https://railway.app) and sign up
2. **Create new project**: Click "New Project" → "Deploy from GitHub repo"
3. **Connect GitHub**: Connect your GitHub account and create a repo with your files
4. **Deploy**: Select your repository and Railway will automatically deploy

## Step 4: Set Environment Variables

In your Railway dashboard:
1. Go to your project
2. Click "Variables" tab
3. Add these environment variables:
   - `GOOGLE_CALENDAR_TOKEN`: Your Google Calendar access token
   - `AIRTABLE_API_KEY`: Your Airtable API key
   - `AIRTABLE_BASE_ID`: Your Airtable base ID
   - `PORT`: 8000 (Railway will automatically set this)

## Step 5: Get Your Railway URL

After deployment, Railway will give you a URL like:
`https://your-app-name.up.railway.app`

## Step 6: Configure Claude Desktop

In Claude Desktop MCP configuration:
- **Server type**: Streamable HTTP
- **URL**: `https://your-app-name.up.railway.app/mcp`
- **Secret Token**: (optional, add if you want extra security)

## Step 7: Test Your ElevenLabs Integration

Your ElevenLabs voice agent can now make HTTP requests to endpoints like:
- `POST https://your-app-name.up.railway.app/calendar/events` (create events)
- `GET https://your-app-name.up.railway.app/calendar/events` (get events)
- `POST https://your-app-name.up.railway.app/calendar/check-availability` (check availability)
- `POST https://your-app-name.up.railway.app/tasks` (create tasks)
- `POST https://your-app-name.up.railway.app/contacts/search` (search contacts)
- `POST https://your-app-name.up.railway.app/reminders` (create reminders)

## Example API Usage in ElevenLabs

```javascript
// Check availability
const response = await fetch('https://your-app-name.up.railway.app/calendar/check-availability', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    date: '2024-12-15',
    start_time: '14:00',
    duration_minutes: 60
  })
});

// Create appointment
const createResponse = await fetch('https://your-app-name.up.railway.app/calendar/events', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    summary: 'Meeting with client',
    start: { dateTime: '2024-12-15T14:00:00Z' },
    end: { dateTime: '2024-12-15T15:00:00Z' }
  })
});
```

## Troubleshooting

1. **Check Railway logs**: In your Railway dashboard, go to "Deployments" to see logs
2. **Verify environment variables**: Make sure all API keys are set correctly
3. **Test endpoints**: Use the `/health` endpoint to verify your server is running
4. **Check API permissions**: Ensure your Google Calendar and Airtable tokens have proper permissions