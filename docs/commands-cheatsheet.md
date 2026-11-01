# Commands Cheat Sheet

## 🐳 Docker & Compose

```bash

# run docker with network name
docker run -d --name smart_notes_pgadmin --network=note_mind_smart_notes_network -e PGADMIN_DEFAULT_EMAIL=admin@admin.com -e PGADMIN_DEFAULT_PASSWORD=admin  -p 5050:80 dpage/pgadmin4

docker compose up -d              # Start stack
docker compose up -d container_name   # start container in docker compose
docker compose down -v            # becarful you will lost your Images Stop and clean
docker compose down container_name # use the to stop and remove containers
docker compose logs               # Show logs all services
docker compose logs -f api        # Tail logs
docker compose exec api bash      # Enter container
docker rm -f smart_notes_pgadmin  # remove container smart_notes_pgadmin 

#  Build & Rebuild
docker compose build           # Build images from compose file
docker compose build --no-cache  # Clean rebuild
docker compose up -d --build    # Build + start Shortcut
docker compose pull   

#  Postgres CLI (Docker)
docker compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB
\dt  # List tables
\di  # List indexes         # Pull  newer base images

# network 
docker network ls               ## list net work in docker 

# Create Network on docker
docker network create --driver bridge note_mind_smart_notes_network

# If the container exists (stopped or stuck), connect it to the network:
  # note_mind_smart_notes_network is name network 
docker network connect note_mind_smart_notes_network smart_notes_pgadmin

```

## OpenAI: Check Embbeding

```bash
curl -v https://api.openai.com/v1/embeddings   -H "Authorization: Bearer $OPENAI_API_KEY"   -H "Content-Type: application/json"   -d '{"input": "Hello world", "model": "text-embedding-3-small"}'
```
```bash

curl -s https://api.openai.com/v1/embeddings \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello world", "model": "text-embedding-3-small"}'

```
## Testing

```bash
# Run tests with coverage
APP_ENV=testing APP_DEBUG=True pytest --cov=core --cov-report=html tests/

# Filter tests
pytest -k "user and not slow"  # Run specific tests
pytest -m "integration"        # Run marked tests Mark tests with `@pytest.mark.integration`
pytest -n auto                 # Parallel tests
```

## FastAPI: Start API server

```bash
# Start dev server
uvicorn app.main:app --reload --port 8000
```

## Alembic: Command

```bash
# Alembic migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1 # What it does? {Revert last migration}	Notes: Careful: data loss possible
```

## Redis

```bash

redis-cli                         # Connect locally redis
redis-cli KEYS "user:*"           # List keys (dev)
redis-cli SCAN 0 MATCH "cache:*"  # Saer scan


# Read all messages from start
XREAD COUNT 10 STREAMS notes:events 0
# Read using consumer group
XREADGROUP GROUP sync-workers worker-1 COUNT 10 STREAMS notes:events >

# After processing, ACK the message:
XACK notes:events sync-workers <message-id>
# List groups on a stream
XINFO GROUPS notes:events
# List consumers in a group
XINFO CONSUMERS notes:events sync-workers

# Add events to a Stream
XADD notes:events * action create note_id 123 content "Hello world"
# Add another event
XADD notes:events * action update note_id 123 content "Updated content"
# Create consumer group 'sync-workers' starting from the beginning
XGROUP CREATE notes:events sync-workers 0 MKSTREAM
```

- notes:events → stream name
- sync-workers → group name
- 0 → read from beginning ($ would mean only new messages)
- MKSTREAM → create the stream if it doesn’t exist
  
##### .💡 If you don’t XACK messages, they stay in Pending Entries List (PEL).

```bash
# This will show which messages are pending, who owns them, and for how long.
XPENDING notes:events sync-workers
```

##### check if worker listen the docker
```bash
# Use Python inside the worker
(Note_Mind) ebrahim@ebrahim-G7-7500:~/Documents/projects/AI/Note_Mind$ docker compose exec worker bash
# From inside the worker container:
app@32117195840b:/app$ 
# write this code python - <<'PY'
import redis, os

host = os.getenv("REDIS_HOST", "redis")
port = int(os.getenv("REDIS_PORT", "6379"))

print("Trying to connect to", host, port)
try:
    r = redis.Redis(host=host, port=port, decode_responses=True, socket_connect_timeout=1)
    print("PING ->", r.ping())
except Exception as e:
    print("ERROR:", e)
PY

# respons if true then worker listen to redis correctly
Trying to connect to redis 6379
PING -> True


```
## Systemd service

```bash
# Systemd service
sudo systemctl enable note_mind   # enable note_mind or servic to run auto with device
sudo systemctl status note_mind   # status servic if running or not
sudo systemctl stop redis         # stop redis or name service if it work in system
```

## Monitoring

```bash
docker stats                     # Live metrics
htop                            # Host monitoring
journalctl -u note_mind -f      # System logs
```


## Port and Network in system

```bash
sudo lsof -i :8080
sudo netstat -tulnp | grep 8080
docker ps -a | grep 8080
```

---
## what do this functions
### 1. The `hasattr()` Function
##### Syntax: `hasattr(object, attribute_name)`

- Returns: `True` if the object has the attribute, `False` otherwise
```python
# This checks if the 'created' object has an 'id' attribute with a 'value' attribute
result = created.id.value if hasattr(created.id, "value") else created.id
```

### 2. The `str(obj)` Function

- `str(obj.id)` - Converts that ID to a string
```python
id = UserId(value=str(obj.id))
```

# call logging in project

```python
# should be first befor in lib
import logging
logger = logging.getLogger("my_app.repositories")
```
# call message and response schemas

```python

from app.constants.messages import Messages
from app.schemas.response_schemas import StandardResponse

@router.post("/notes/")
def create_note():
    return StandardResponse(
        status="success",
        message=Messages.NOTE_CREATED,
        data={"id": "123", "title": "My Note"}
    )
```