# Deployment Guide (Linux VPS)

## Backend (Flask + Gunicorn)

- Python 3.13 installed. Install user packages:

```bash
pip install --user Flask==3.0.3 Flask-Cors==4.0.1 Flask-JWT-Extended==4.6.0 Flask-SQLAlchemy==3.1.1 SQLAlchemy==2.0.31 bcrypt==4.1.3 openpyxl==3.1.2 python-dateutil==2.9.0.post0 gunicorn==21.2.0
```

- Service directory: `/srv/bizforecast/backend`
- Run with systemd (as user `ubuntu`):

```ini
[Unit]
Description=BizForecast API (Gunicorn)
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/srv/bizforecast/backend
Environment=PYTHONUNBUFFERED=1
Environment=SECRET_KEY=change-me
Environment=JWT_SECRET_KEY=change-me
ExecStart=/usr/bin/python3 -m gunicorn -w 2 -b 127.0.0.1:5001 wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

- Save as `/etc/systemd/system/bizforecast-api.service`, then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now bizforecast-api
sudo systemctl status bizforecast-api
```

## Frontend (Vite build served by Nginx)

- Build locally or CI and copy `/workspace/frontend/dist` to `/srv/bizforecast/frontend`.
- Nginx site config at `/etc/nginx/sites-available/bizforecast`:

```nginx
server {
    listen 80;
    server_name _;

    root /srv/bizforecast/frontend;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

- Enable and reload:

```bash
sudo ln -sf /etc/nginx/sites-available/bizforecast /etc/nginx/sites-enabled/bizforecast
sudo nginx -t && sudo systemctl reload nginx
```

Notes:
- Backend listens on 127.0.0.1:5001 via Gunicorn; Nginx reverse proxies `/api/`.
- Set `SECRET_KEY` and `JWT_SECRET_KEY` in the service unit or environment.
- SQLite DB will be created in backend directory as `bizforecast.db`.