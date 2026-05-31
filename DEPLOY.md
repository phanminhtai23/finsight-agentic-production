# Deploying FinSight (backend) on a DigitalOcean droplet with a domain

Target: a single Ubuntu 24.04 droplet (**4 GB RAM / 2 vCPU**) running the full stack via Docker
Compose, behind Nginx + HTTPS on your domain. Frontend stays on Vercel.

## 0. Prerequisites

- A droplet created (Ubuntu 24.04). Note its **public IP** from the DigitalOcean dashboard.
- A domain. In your DNS provider, add records pointing to the droplet IP:
  - `A   api   <DROPLET_IP>`  → gives `api.yourdomain.com` (recommended for the backend)
  - (frontend stays on Vercel; point its own domain/subdomain there separately)

## 1. SSH into the server from Windows CMD

Windows 10/11 ships with the OpenSSH client — just open **Command Prompt (cmd)** and run:

```cmd
ssh root@YOUR_DROPLET_IP
```

- First time it asks `Are you sure you want to continue connecting?` → type `yes`.
- **Password droplet:** paste the root password DigitalOcean emailed you (typing is hidden).
- **SSH-key droplet:** point to your private key:
  ```cmd
  ssh -i %USERPROFILE%\.ssh\id_rsa root@YOUR_DROPLET_IP
  ```

You're in when the prompt becomes `root@droplet:~#`. Everything below runs **on the server**.

## 2. Install Docker + a swap file (safety margin on RAM)

```bash
curl -fsSL https://get.docker.com | sh

# 2 GB swap so ingestion/OCR spikes never OOM the box
fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

## 3. Get the code onto the server

**Option A — clone from GitHub (push `finsight-production` first):**
```bash
git clone https://github.com/phanminhtai23/finsight-production.git
cd finsight-production
```

**Option B — copy from your PC (run in CMD on Windows, not on the server):**
```cmd
scp -r "d:\Project\AI-Agents\Project3-AI-Agentic" root@YOUR_DROPLET_IP:/root/finsight
```
then on the server: `cd /root/finsight`

## 4. Create the production `.env`

```bash
cp .env.example .env
nano .env
```
Set at least:
```env
ENVIRONMENT=prod
GOOGLE_API_KEY=<your key>
JWT_SECRET=<strong secret>          # generate: openssl rand -base64 48
DATABASE_URL=postgresql+asyncpg://finsight:finsight@postgres:5432/finsight
CHECKPOINT_DATABASE_URL=postgresql://finsight:finsight@postgres:5432/finsight
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
MCP_SERVER_URL=http://mcp:8001/mcp
FRONTEND_URL=https://your-frontend.vercel.app
CORS_ORIGINS=["https://your-frontend.vercel.app"]
```
> With `ENVIRONMENT=prod` the app refuses to start if `JWT_SECRET` is weak — that's intentional.
> Save in nano: `Ctrl+O`, `Enter`, `Ctrl+X`.

## 5. Build, run, migrate

```bash
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
docker compose -f docker-compose.prod.yml exec api alembic upgrade head

# sanity check (on the server)
curl http://localhost:8000/api/v1/readiness     # {"status":"ready",...}
```

## 6. Nginx reverse proxy + HTTPS (your domain)

```bash
apt update && apt install -y nginx certbot python3-certbot-nginx
ufw allow OpenSSH && ufw allow 'Nginx Full' && ufw --force enable
```

Create the site config:
```bash
nano /etc/nginx/sites-available/finsight
```
Paste (replace `api.yourdomain.com`):
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE (token streaming) + WebSocket (ingestion progress)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }
}
```
Enable + get a free TLS certificate:
```bash
ln -s /etc/nginx/sites-available/finsight /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
certbot --nginx -d api.yourdomain.com      # auto-configures HTTPS + renewal
```

Now `https://api.yourdomain.com/api/v1/health` should return `200`.

## 7. Point the frontend (Vercel) at it

In Vercel → Project → Settings → Environment Variables:
```
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1
VITE_GOOGLE_CLIENT_ID=<same as backend GOOGLE_OAUTH_CLIENT_ID>
```
Redeploy the frontend. Make sure the Vercel URL is in the backend `CORS_ORIGINS` (step 4) and in
your Google OAuth **Authorized JavaScript origins**.

## Operating it

```bash
docker compose -f docker-compose.prod.yml ps              # status
docker compose -f docker-compose.prod.yml logs -f api     # tail api logs
docker compose -f docker-compose.prod.yml pull && \
  docker compose -f docker-compose.prod.yml up -d --build  # update after a git pull
```

- Metrics: `https://api.yourdomain.com/metrics` (consider firewalling this to your IP).
- Health/readiness: `/api/v1/health`, `/api/v1/readiness`.

## Continuous Deployment (auto-deploy on push to main)

`.github/workflows/deploy.yml` SSHes into the droplet after CI passes and rolls the stack
(`git reset --hard origin/main` → `docker compose up -d --build` → `alembic upgrade head`).

**One-time setup:**

1. On the droplet, create a dedicated deploy key and authorize it:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/gh_deploy -N "" -C "github-actions"
   cat ~/.ssh/gh_deploy.pub >> ~/.ssh/authorized_keys
   cat ~/.ssh/gh_deploy        # copy the WHOLE private key (incl. BEGIN/END lines)
   ```
2. In GitHub → repo → **Settings → Secrets and variables → Actions → New repository secret**, add:
   | Secret | Value |
   |--------|-------|
   | `SSH_HOST` | droplet IP (e.g. `104.248.150.222`) |
   | `SSH_USER` | `root` |
   | `SSH_PORT` | `22` |
   | `SSH_PRIVATE_KEY` | the full contents of `~/.ssh/gh_deploy` |
3. Push to `main` → CI runs → on success, **Deploy** runs automatically. You can also trigger it
   manually from the **Actions** tab (`Run workflow`).

> The droplet `.env` is untracked, so `git reset --hard` never touches your secrets.
