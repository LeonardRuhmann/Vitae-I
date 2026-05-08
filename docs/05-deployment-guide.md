# 🚀 Free Tier Deployment Guide

This guide walks you through deploying the **Vitae-I** application in production for absolutely **zero cost**. We will use three different platforms, each excelling in their respective layers.

> **Note:** Make sure you merge your code into the `main` branch on GitHub before starting, as these platforms will automatically pull the code from there!

---

## 🟢 1. Database: Aiven Cloud (PostgreSQL)

Aiven provides a fully managed, robust PostgreSQL instance on their free tier.

### Steps:
1. Go to [Aiven.io](https://aiven.io/) and create a free account.
2. In the Console, click **Create Service** and select **PostgreSQL**.
3. Choose the **Free Plan** (available in specific regions like US or EU).
4. Give your service a name (e.g., `vitae-db`) and click **Create**.
5. Once the service is running, find the **Connection URI** (or `DATABASE_URL`) on the Overview page.
   * It will look something like: `postgres://avnadmin:password@host.aivencloud.com:port/defaultdb?sslmode=require`
6. **CRITICAL:** Change the prefix from `postgres://` to `postgresql+asyncpg://` to match our async driver!
   * *Example:* `postgresql+asyncpg://avnadmin:password@host.aivencloud.com:port/defaultdb?sslmode=require`

Save this URL for the next step.

---

## 🟣 2. Backend: Render (FastAPI)

Render provides a fantastic Free Web Service tier that automatically builds your Docker image from GitHub. We've already added a `render.yaml` file to make this seamless.

### Steps:
1. Go to [Render.com](https://render.com/) and link your GitHub account.
2. Click **New** > **Blueprint**.
3. Connect your `Vitae-I` GitHub repository.
4. Render will automatically detect the `render.yaml` file and prepare the `vitae-api` Web Service.
5. In the final step before applying, Render will ask you to fill in the missing Environment Variables:
   * **`DATABASE_URL`**: Paste the connection string you got from Aiven (the one with `postgresql+asyncpg://`).
   * **`ALLOWED_ORIGINS`**: Leave this empty for a moment (we will update it after we deploy Netlify).
6. Click **Apply**.
7. Render will now clone the repo, build the Dockerfile, download the spaCy model, and start the API.
8. Once deployed, copy your backend URL (e.g., `https://vitae-api.onrender.com`).

---

## 🔵 3. Frontend: Netlify (React/Vite)

Netlify is the industry standard for hosting static SPA (Single Page Application) frontends. We already added the `_redirects` file so React Router works perfectly without returning 404 errors!

### Steps:
1. Go to [Netlify.com](https://www.netlify.com/) and log in with GitHub.
2. Click **Add new site** > **Import an existing project** > **GitHub** > Select `Vitae-I`.
3. In the Site Settings, configure the Build settings:
   * **Base directory:** `frontend`
   * **Build command:** `npm run build`
   * **Publish directory:** `frontend/dist`
4. Click **Add environment variables**:
   * Key: `VITE_API_URL`
   * Value: The Render URL you copied in the previous step (e.g., `https://vitae-api.onrender.com`) — *Make sure there is no trailing slash!*
5. Click **Deploy site**.
6. Once published, copy your live Netlify URL (e.g., `https://vitae-app.netlify.app`).

---

## 🔗 4. The Final Connection (CORS)

Right now, if you try to use the Netlify site, the browser will block the connection because of CORS (Cross-Origin Resource Sharing). We need to tell the Backend to trust the Frontend.

### Steps:
1. Go back to your [Render Dashboard](https://dashboard.render.com/).
2. Open the `vitae-api` Web Service.
3. Go to the **Environment** tab.
4. Add or edit the `ALLOWED_ORIGINS` variable:
   * Value: Paste your Netlify URL (e.g., `https://vitae-app.netlify.app`). *No trailing slash!*
5. Save changes. Render will restart the backend automatically.

---

## 🎉 Done!
Your application is now fully deployed.
* The frontend is cached globally on Netlify's CDN.
* The backend is running inside a Docker container on Render.
* The data is safely persisted in Aiven Cloud.
