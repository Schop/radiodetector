# Render.com Deployment Guide

## Step 1: Push to GitHub

1. Create a new repository on GitHub (e.g., `radiochecker`)
2. Push your code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/radiochecker.git
   git push -u origin main
   ```

## Step 2: Create Render Account

1. Go to https://render.com
2. Sign up with your GitHub account (easiest)
3. Authorize Render to access your repositories

## Step 3: Create Web Service (for web_app.py)

1. Click "New +" → "Web Service"
2. Connect your `radiochecker` repository
3. Configure:
   - **Name**: `radiochecker-web` (or whatever you want)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python web_app.py`
   - **Instance Type**: `Free`
4. Add Environment Variables (optional):
   - You can add any config here if needed
5. Click "Create Web Service"

## Step 4: Create Background Worker (for main.py)

1. Click "New +" → "Background Worker"
2. Connect the same `radiochecker` repository
3. Configure:
   - **Name**: `radiochecker-checker`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Instance Type**: `Free`
4. Click "Create Background Worker"

## Step 5: Wait for Deployment

- Both services will build and deploy (takes 2-5 minutes)
- Once deployed, you'll get a URL like: `https://radiochecker-web.onrender.com`
- The background worker will run continuously

## Step 6: Point Your Domain (Later)

In Render dashboard:
1. Go to your web service
2. Click "Settings" → "Custom Domain"
3. Add your domain (e.g., `philcollins.nl`)
4. Follow Render's DNS instructions to update your STRATO domain

## Notes

- **Free tier limitation**: Services spin down after 15 min of inactivity
- First request after idle will take ~30 seconds to wake up
- Database persists on Render's disk
- Both services share the same filesystem, so they can both access `radio_songs.db`

## Troubleshooting

If services fail to start:
- Check the logs in Render dashboard
- Make sure `requirements.txt` includes all dependencies
- Verify `config.yaml` is in the repository
