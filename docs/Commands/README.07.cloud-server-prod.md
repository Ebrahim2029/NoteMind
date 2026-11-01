Awesome 🌍 Here’s the **seventh (final) README**.

# README — 07. Cloud Server (Production Deploy, Monitor, Logs, Backups)

> Scope: Deploying the Note\_Mind stack (FastAPI + Postgres + Redis + Chroma) on a **cloud server (VPS or VM)**. Includes deployment patterns, monitoring, scaling, logs, and backup strategies.

---

## 1) Server Setup (Linux VM)

| Command                                           | What it does              | Notes                               |
| ------------------------------------------------- | ------------------------- | ----------------------------------- |
| `sudo apt update && sudo apt upgrade -y`          | Update system             | Ubuntu/Debian                       |
| `sudo apt install docker.io docker-compose -y`    | Install Docker + Compose  | Or install from Docker CE repo      |
| `sudo usermod -aG docker $USER`                   | Allow non-root Docker use | Relogin required                    |
| `ufw allow 22` / `ufw allow 80` / `ufw allow 443` | Open SSH/HTTP/HTTPS       | Harden firewall                     |
| `ufw enable`                                      | Enable firewall           | Confirm SSH allowed before enabling |

---

## 2) Deploy with Docker Compose

| Command                                       | What it does           | Notes                        |
| --------------------------------------------- | ---------------------- | ---------------------------- |
| `scp -r ./project user@server:/opt/note_mind` | Copy project to server | Adjust path                  |
| `ssh user@server`                             | SSH into server        |                              |
| `cd /opt/note_mind && docker compose up -d`   | Start full stack       | API, Postgres, Redis, Chroma |
| `docker compose ps`                           | Verify containers      | Should show running services |
| `curl http://<server-ip>:8000/health`         | Check API health       | Use reverse proxy for public |

---

## 3) Reverse Proxy + SSL (NGINX / Traefik)

### NGINX reverse proxy example:

```nginx
server {
    listen 80;
    server_name notes.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable HTTPS with **Let’s Encrypt (Certbot):**

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d notes.example.com
```

---

## 4) Process Management (systemd)

To ensure Docker Compose stack auto-starts:

```bash
sudo tee /etc/systemd/system/note_mind.service <<EOF
[Unit]
Description=NoteMind App Stack
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/note_mind
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
EOF
```

Then:

```bash
sudo systemctl enable note_mind
sudo systemctl start note_mind
sudo systemctl status note_mind
```

---

## 5) Logs & Monitoring

| Command                           | What it does           | Notes                  |
| --------------------------------- | ---------------------- | ---------------------- |
| `docker compose logs -f api`      | Tail API logs          |                        |
| `docker compose logs -f postgres` | Tail DB logs           |                        |
| `docker compose logs -f redis`    | Tail Redis logs        |                        |
| `docker stats`                    | Live CPU/Memory        | Across containers      |
| `htop` / `iotop`                  | Host monitoring        | CPU/IO load            |
| `df -h`                           | Disk usage             | Watch DB/Redis volumes |
| `journalctl -u note_mind -f`      | Systemd logs for stack |                        |

**Advanced (recommended):**

* Use **Prometheus + Grafana** stack.
* Exporter examples:

  * `wrouesnel/postgres_exporter`
  * `oliver006/redis_exporter`
  * `prom/node-exporter` for server stats.

---

## 6) Database Backups (Postgres)

### Daily dump (cron):

```bash
pg_dump -U postgres -d smart_notes -F c > /backups/smart_notes_$(date +%F).dump
```

### Restore:

```bash
pg_restore -U postgres -d smart_notes -c /backups/smart_notes_2025-08-17.dump
```

**Docker example:**

```bash
docker exec -t note_mind_postgres pg_dump -U postgres smart_notes > ./backup.sql
docker exec -i note_mind_postgres psql -U postgres smart_notes < ./backup.sql
```

---

## 7) Redis Backups

* If persistence is enabled (`appendonly yes`):

  * AOF file: `/data/appendonly.aof`
  * RDB snapshot: `/data/dump.rdb`

### Copy backup:

```bash
docker cp note_mind_redis:/data/appendonly.aof ./redis-backup.aof
```

### Restore:

* Stop Redis.
* Replace file.
* Start again.

---

## 8) Chroma Backups

* Chroma stores data in DuckDB inside `/chroma`.
* Backup by copying volume:

```bash
docker cp note_mind_chroma:/chroma ./chroma-backup/
```

* Restore by replacing volume content.

---

## 9) Scaling & Updates

| Task                   | Command                                                    | Notes                              |
| ---------------------- | ---------------------------------------------------------- | ---------------------------------- |
| Scale API horizontally | `docker compose up -d --scale api=3`                       | Needs reverse proxy load balancing |
| Update image           | `docker compose pull && docker compose up -d`              | Zero-downtime if proxy used        |
| Blue-Green deploy      | Run second stack `-p note_mind_blue`, swap proxy, stop old | Safer updates                      |
| Rolling update         | Restart services one by one                                | For clusters / Swarm / K8s         |

---

## 10) Security & Hardening

| Area     | Action                                                 |
| -------- | ------------------------------------------------------ |
| SSH      | Use key auth, disable root login                       |
| Firewall | Allow only 22, 80, 443 (or VPN for DB/Redis)           |
| Secrets  | Store DB/Redis passwords in `.env` (not Git)           |
| TLS      | Always use HTTPS for public endpoints                  |
| DB       | Allow only internal network access                     |
| Redis    | Bind to localhost / private network, set `requirepass` |
| Backups  | Encrypt before offsite storage                         |

---

## 11) Common “Gotchas”

| Symptom                                 | Quick check                       | Fix                                                |
| --------------------------------------- | --------------------------------- | -------------------------------------------------- |
| API responds locally but not externally | Firewall / NGINX                  | Open 80/443, set correct server\_name              |
| Containers restart loop                 | `docker compose logs <svc>`       | Fix env vars / healthchecks                        |
| Disk fills quickly                      | `du -sh /var/lib/docker/volumes`  | Add monitoring, rotate backups                     |
| Postgres OOM kills                      | `docker stats` shows memory spike | Tune `shared_buffers`, `work_mem`, increase VM RAM |
| Redis data gone                         | Persistence not enabled           | Add `appendonly yes` + mounted volume              |

---

