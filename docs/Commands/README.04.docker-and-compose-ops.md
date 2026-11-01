
# README — 04. Docker & Docker Compose (Project Ops)

> Scope: Build & run Python/FastAPI apps with Docker, compose multi-service stacks (Postgres, Redis, Chroma, API), manage images/containers, logs, and healthchecks for dev/prod.

---

## 1) Images & Containers (Docker basics)

| Command | What it does | Notes |
|---------|-------------|-------|
| **Image Commands** | | |
| `docker images` | Lists all local images | Shows REPO, TAG, IMAGE ID, SIZE |
| `docker pull <image>` | Downloads image from registry | Defaults to latest tag if unspecified |
| `docker build -t <name> .` | Builds image from Dockerfile | `.` = build context path |
| `docker rmi <image>` | Removes an image | Fails if containers are using it |
| `docker image prune` | Removes dangling images | Add `-a` to remove all unused images |
| `docker tag <image> <new-name>` | Tags an image | Useful for versioning |
| `docker save <image> > file.tar` | Saves image to tar archive | |
| `docker load < file.tar` | Loads image from tar archive | |
| **Container Commands** | | |
| `docker ps` | Lists running containers | Add `-a` to show all containers |
| `docker run <image>` | Creates and starts container | Common flags: `-d` (detached), `-p` (port), `-v` (volume) |
| `docker start <container>` | Starts stopped container | |
| `docker stop <container>` | Gracefully stops container | SIGTERM then SIGKILL after timeout |
| `docker rm <container>` | Removes stopped container | Add `-f` to force remove running |
| `docker container prune` | Removes all stopped containers | Add `-f` to skip confirmation |
| `docker exec -it <container> <cmd>` | Runs command in running container | Common for shells (`/bin/bash`) |
| `docker commit <container> <image>` | Creates image from container | Not recommended for production |

### Key Features:
1. **Images** - Build, manage, and distribute application packages
2. **Containers** - Run, inspect, and manage isolated processes
3. Common flags:
   - `-d` - Detached mode
   - `-it` - Interactive terminal
   - `-p` - Port mapping (host:container)
   - `-v` - Volume mounting (host:container)
   - `-e` - Set environment variables


---

## 2) Logs & Monitoring (single container)

| Command | What it does | Notes |
|---------|-------------|-------|
| `docker logs <container>` | Shows container logs | Defaults to STDOUT & STDERR |
| `docker logs --tail 100 <container>` | Shows last N lines | Useful for recent logs |
| `docker logs -f <container>` | Follow logs in real-time | Like `tail -f` |
| `docker logs --since 1h <container>` | Shows logs since a time period | Supports `1h30m`, `2023-01-01`, etc. |
| `docker logs --until 10m <container>` | Shows logs until a time period | Useful for time-bound debugging |
| `docker stats` | Live container resource usage | CPU, memory, network, disk I/O |
| `docker stats --no-stream` | Single snapshot of stats | Useful for scripts |
| `docker top <container>` | Shows running processes inside container | Similar to Linux `top` |
| `docker events` | Real-time Docker daemon events | Container start/stop, image pulls, etc. |
| `docker inspect <container>` | Detailed container metadata | Includes IP, mounts, configs |
| `docker exec -it <container> sh` | Interactive shell inside container | Replace `sh` with `bash` if available |
| `docker system df` | Shows disk usage | Images, containers, volumes, cache |

### Key Features:  
- **Logs**: View historical or real-time logs (`-f` for follow mode).  
- **Monitoring**: Check CPU, memory, and process stats (`docker stats`).  
- **Debugging**: Inspect metadata (`docker inspect`) or enter containers (`docker exec`).  
- **Disk Usage**: Track storage with `docker system df`.  
---

## 3) Volumes & Networks

| Command | What it does | Notes |
|---------|-------------|-------|
| `docker volume create my_volume` | Creates a named volume | Persistent storage for containers |
| `docker volume ls` | Lists all volumes | Shows name, driver, and scope |
| `docker volume inspect my_volume` | Shows volume details | Includes mountpoint and metadata |
| `docker volume rm my_volume` | Removes a volume | Fails if volume is in use |
| `docker volume prune` | Removes unused volumes | Add `-f` to skip confirmation |
| `docker network create my_network` | Creates a custom network | Defaults to bridge driver |
| `docker network ls` | Lists all networks | Shows name, driver, and scope |
| `docker network inspect my_network` | Shows network details | Includes connected containers |
| `docker network connect my_network container` | Attaches container to network | Container gets new IP on that network |
| `docker network disconnect my_network container` | Detaches container from network | |
| `docker network rm my_network` | Removes a network | Must have no connected containers |
| `docker network prune` | Removes unused networks | Add `-f` to skip confirmation |

### Key Features:
1. **Volumes** → Persistent storage (even when containers die)
2. **Networks** → Isolated communication channels
3. All commands support `--help` for more options
---

## 4) Docker Compose Basics

| Command                                     | What it does                | Notes                     |
| ------------------------------------------- | --------------------------- | ------------------------- |
| `docker compose up`                         | Start services (foreground) | For dev                   |
| `docker compose up -d`                      | Detached mode               | Common in prod            |
| `docker compose down`                       | Stop & remove               | Add `-v` to wipe volumes  |
| `docker compose stop` / `start` / `restart` | Manage services             |                           |
| `docker compose ps`                         | List services               | Names + state             |
| `docker compose logs`                       | Show logs all services      | Add `-f api` for specific |
| `docker compose exec api bash`              | Exec into service           | Replace `api`             |

---

## 5) Build & Rebuild

| Command                           | What it does                   | Notes        |
| --------------------------------- | ------------------------------ | ------------ |
| `docker compose build`            | Build images from compose file |              |
| `docker compose build --no-cache` | Clean rebuild                  |              |
| `docker compose up -d --build`    | Build + start                  | Shortcut     |
| `docker compose pull`             | Pull newer base images         | Stay patched |

---

## 6) Example: Full Stack Compose (API + DB + Cache + Vector DB)

 `docker-compose.yml` file with a dedicated network configuration, which improves service isolation and communication:

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      APP_ENV: dev
      DATABASE_URL: postgres://postgres:${POSTGRES_PASSWORD}@postgres:5432/smart_notes
      REDIS_URL: redis://:password@redis:6379/0
      CHROMA_URL: http://chroma:8001
    depends_on:
      - postgres
      - redis
      - chroma
    networks:
      - app_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 3s
      retries: 5

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: smart_notes
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
    networks:
      - app_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:6.4.0
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redis_data:/data
    networks:
      - app_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  chroma:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma
    networks:
      - app_network

volumes:
  pg_data:
  redis_data:
  chroma_data:

networks:
  app_network:
    driver: bridge
```

Key improvements made:
1. Added `networks` section at root level
2. Connected all services to `app_network`
3. Explicitly set network driver to `bridge` (default, but good practice to specify)
4. Each service now has `networks` configuration

Benefits:
- Better service isolation from other Docker projects
- Services can communicate using their service names as hostnames
- More secure than default networking
- Easier to add additional networks later (like separating frontend/backend)

#### ```note```
The network uses bridge mode which is ideal for single-host deployments. For swarm/cluster deployments, you might want to use `overlay` driver instead.

---

## 7) Health & Debugging

| Command                                                   | What it does        | Notes                |
| --------------------------------------------------------- | ------------------- | -------------------- |
| `docker compose ps --services --filter "status=running"`  | Show only running   | Quick health glance  |
| `docker compose logs -f --tail=50`                        | Tail last 50 lines  | Live troubleshooting |
| `docker inspect <container> --format='{{.State.Health}}'` | Inspect healthcheck | JSON output          |
| `curl http://localhost:8000/health`                       | API health endpoint | Define in FastAPI    |

---

## 8) Deploy Strategy (Prod-ready)

| Approach              | Command / Notes                                                                            |
| --------------------- | ------------------------------------------------------------------------------------------ |
| **Blue-Green**        | Run `docker compose -p note_mind_blue up -d`, switch load balancer, then stop green.       |
| **Rolling Update**    | `docker compose up -d --scale api=3 --no-deps --build api` (restarts services one by one). |
| **Zero-downtime tip** | Use reverse proxy (NGINX/Traefik) in front of API containers.                              |

---

## 9) Security & Hardening

| Area    | Action                                                                       |
| ------- | ---------------------------------------------------------------------------- |
| Secrets | Use `.env` files with Docker secrets / vault, never hardcode                 |
| User    | Use non-root user in Dockerfile (`USER app`)                                 |
| Network | Isolate services with compose networks                                       |
| Updates | Rebuild periodically (`docker compose pull && docker compose up -d --build`) |
| Scan    | Run `docker scan <image>` or use Trivy/Grype in CI                           |

---

## 10) Troubleshooting “Gotchas”

#### a comprehensive **Troubleshooting "Gotchas"** table for Docker Compose deployments, covering common issues with your setup:

| Symptom | Quick Check | Fix |
|---------|------------|------|
| **API service won't start** | `docker-compose logs api` | Check dependency services (Postgres/Redis/Chroma) are healthy |
| **Postgres connection refused** | `docker-compose exec postgres pg_isready` | Verify `POSTGRES_PASSWORD` is set in `.env` file |
| **Redis not responding** | `docker-compose exec redis redis-cli ping` | Ensure Redis volume isn't corrupted (`docker volume inspect`) |
| **Chroma connection timeout** | `curl -I http://localhost:8001/api/v1/heartbeat` | Increase Chroma's startup wait time in `depends_on` |
| **Port already in use** | `netstat -tulnp \| grep :8000` | Change host port or stop conflicting service |
| **Volume permission errors** | `docker-compose exec postgres ls -la /var/lib/postgresql/data` | Add `user: 1000:1000` to postgres service |
| **Environment variables not set** | `docker-compose config` | Verify `.env` file exists and variables match compose file |
| **Health checks failing** | `docker inspect --format='{{json .State.Health}}' service-name` | Adjust healthcheck intervals/timeouts |
| **Slow container startup** | `docker-compose events` | Add `restart: unless-stopped` to critical services |
| **DNS resolution failures** | `docker-compose exec api ping postgres` | Explicitly set `network_alias` for services |
| **Build cache issues** | `docker-compose build --no-cache` | Prune unused images/volumes |
| **Intermittent failures** | `docker stats` | Check memory limits (add `mem_limit: 512m` if needed) |

**Pro Tips:**
1. Always check logs in order:
   ```bash
   docker-compose logs --tail=100 api
   docker-compose logs --timestamps
   ```
2. For stuck containers:
   ```bash
   docker-compose down -v --remove-orphans
   docker system prune -a
   docker-compose up
   ```
3. To debug networking:
   ```bash
   docker-compose exec api curl -v http://postgres:5432
   docker network inspect your-project_app_network
   ```
---
## 11) an **expanded Troubleshooting “Gotchas”**
#### with specific Postgres/Redis/Chroma gotchas and advanced debugging techniques for your stack:

| Symptom | Quick Check | Fix | Advanced Debugging |
|---------|------------|------|-------------------|
| **Postgres: Authentication failed** | `docker-compose exec postgres psql -U postgres -c '\l'` | Verify `.env` matches `POSTGRES_PASSWORD` in DB URL | `docker exec -it postgres cat /var/lib/postgresql/data/pg_hba.conf` |
| **Postgres: Disk full** | `docker-compose exec postgres df -h` | Increase volume size or run `VACUUM FULL` | `docker run -it --rm -v your_pg_data:/volume busybox sh -c "du -sh /volume"` |
| **Redis: AOF corruption** | `docker-compose exec redis redis-check-aof --fix /data/appendonly.aof` | Restart with `--appendonly no` temporarily | `docker diff redis` to see changed files |
| **Redis: OOM errors** | `docker stats redis` | Add `memory: 1gb` limit in compose | `redis-cli info memory` inside container |
| **Chroma: Collection errors** | `curl -X GET http://chroma:8001/api/v1/collections` | Recreate persistent volume | Check Chroma logs with `journalctl -u chroma` if using systemd |
| **Chroma: Slow embeddings** | `docker-compose exec api time curl -s http://chroma:8001` | Scale Chroma with `chroma: scale: 2` | `docker-compose exec chroma chroma-monitor` |
| **API: Dependency timeout** | `docker-compose exec api nc -zv postgres 5432` | Add `healthcheck` to all services | `docker-compose up -d --wait postgres redis chroma` |
| **API: DB pool exhaustion** | `docker-compose exec api curl http://localhost:8000/debug` | Increase pool size in DB URL (`?pool_size=20`) | `docker-compose exec postgres psql -c 'SELECT * FROM pg_stat_activity'` |
| **Intermittent 502s** | `docker-compose logs --tail=50 api \| grep -A 5 'BrokePipe'` | Add `restart: unless-stopped` | `strace -p <container_pid>` on host |
| **Volume permission errors** | `docker-compose exec postgres touch /var/lib/postgresql/data/test` | Add `user: "1000:1000"` to service | `docker run --rm -v pg_data:/mnt alpine ls -la /mnt` |

**Specialized Commands for Your Stack:**
```bash
# Postgres query log (temporarily enable)
docker-compose exec postgres sh -c 'echo "log_statement = 'all'" >> /var/lib/postgresql/data/postgresql.conf && pg_ctl reload'

# Redis slow query log
docker-compose exec redis redis-cli CONFIG SET slowlog-log-slower-than 1000
docker-compose exec redis redis-cli SLOWLOG GET 10

# Chroma debug mode
docker-compose stop chroma
docker-compose run chroma chroma-server --workers 1 --log-level debug
```

**Gotcha Prevention Checklist:**
1. **For production**: 
   ```yaml
   postgres:
     deploy:
       resources:
         limits:
           memory: 2gb
     healthcheck:
       test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB && psql -U $$POSTGRES_USER -d $$POSTGRES_DB -c 'SELECT 1'"]
   ```
2. **For Chroma persistence**:
   ```yaml
   chroma:
     environment:
       PERSIST_DIRECTORY: /chroma/persist
     volumes:
       - chroma_data:/chroma/persist
   ```
