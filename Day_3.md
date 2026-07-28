# Day 3: Production-Ready Docker & Multi-Container Systems

Welcome back! I'm your senior backend engineering mentor, and today we are getting serious. 

You've learned how to containerize an app and link two simple Flask APIs. But in the real world, applications need databases, caches, persistent storage, and health checks. Today, we are building a complete backend system exactly how you would structure it for production. 

Grab some coffee. We have a lot of ground to cover in the next 45-60 minutes.

---

## PART 1: Production Docker Concepts

### The Container Lifecycle
Containers are designed to be **ephemeral** (temporary). 
If a container crashes or you run `docker compose down`, everything inside that container is destroyed. 

```text
Create container  -->  Application runs  -->  Container deleted (Data is lost!)
```

### Why Databases Should NOT Store Data Inside Containers
If you run a PostgreSQL container and save user data inside its internal file system, the moment that container is stopped or updated, **all your users are gone**. In production, losing database data is a resume-generating event (you get fired).

### The Solution: Volumes
Volumes are a way to store data *outside* the container's lifecycle, on your actual host machine's hard drive.

```text
Container deleted  -->  Database data remains (stored safely in a volume)
```

There are two main types of volumes:
1. **Named Volumes**: Docker manages where the data is stored on your host machine. Best for databases like Postgres or Redis. (e.g., `pgdata:/var/lib/postgresql/data`).
2. **Bind Mounts**: You specify an exact folder on your laptop to link to the container. Best for local development so your code changes update live without rebuilding. (e.g., `./app:/app`).

### 🛑 Checkpoint 1
You are setting up a MongoDB container for production. Would you use a bind mount mapping to your `C:\Users\data` folder, or a Docker Named Volume?
*(Answer: Named Volume. It's safer, managed by Docker, and avoids permission issues on different operating systems.)*

---

## PART 2: The Project - Task Management API

Today, we are building a **Task Management API**.

**The Architecture:**
```text
                 Client
                   |
                   |
              Flask API
                   |
        ---------------------
        |                   |
   PostgreSQL             Redis
   Database               Cache
```

**Features:**
* `POST /tasks` - Create a new task.
* `GET /tasks` - Get all tasks (Cached in Redis to make it lightning fast).
* `DELETE /tasks/<id>` - Delete a specific task.

**Database Table (`tasks`):**
* `id` (Integer, Primary Key)
* `title` (String)
* `description` (String)
* `status` (String - "pending" or "completed")
* `created_at` (Timestamp)

---

## PART 3: Create Folder Structure

Create this exact folder structure on your machine. I will explain the purpose of each file as we write the code.

```text
task-management-api/
│
├── docker-compose.yml     # The master blueprint orchestrating our 3 services.
├── .env                   # Secret environment variables (passwords, etc).
├── README.md              # Documentation for your project.
│
├── flask-api/             # The backend logic folder.
│   ├── app.py             # Main Flask routing and caching logic.
│   ├── models.py          # SQLAlchemy database schema definition.
│   ├── database.py        # Database connection setup.
│   ├── requirements.txt   # Python dependencies.
│   ├── Dockerfile         # Instructions to containerize the Flask app.
│   └── .dockerignore      # Files Docker should ignore to keep images small.
│
└── postgres/              # Database initialization.
    └── init.sql           # SQL script that runs automatically when DB starts.
```

---

## PART 4: Flask Application

Let's write the code for our API. Create these inside the `flask-api/` directory.

**`flask-api/requirements.txt`**
```text
Flask==2.3.2
SQLAlchemy==2.0.18
psycopg2-binary==2.9.6
redis==4.6.0
python-dotenv==1.0.0
```
*(We need `psycopg2` to talk to Postgres, `redis` to talk to Redis, and `SQLAlchemy` as our ORM).*

**`flask-api/database.py`**
```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# We construct the connection string using environment variables.
DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DB_NAME = os.getenv("POSTGRES_DB", "taskdb")
DB_HOST = os.getenv("DB_HOST", "postgres") # Notice the default is the container name!

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

**`flask-api/models.py`**
```python
from sqlalchemy import Column, Integer, String, DateTime
import datetime
from database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String(255))
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }
```

**`flask-api/app.py`**
```python
import os
import json
from flask import Flask, request, jsonify
import redis
from database import engine, Base, SessionLocal
from models import Task

app = Flask(__name__)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Connect to Redis. Host is the service name from docker-compose!
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, db=0, decode_responses=True)

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.json
    db = SessionLocal()
    new_task = Task(title=data['title'], description=data.get('description', ''))
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    db.close()
    
    # Invalidate cache because data changed!
    redis_client.delete("all_tasks")
    
    return jsonify(new_task.to_dict()), 201

@app.route('/tasks', methods=['GET'])
def get_tasks():
    # 1. Check Redis Cache
    cached_tasks = redis_client.get("all_tasks")
    if cached_tasks:
        print("Fetching from Redis cache!")
        return jsonify(json.loads(cached_tasks))
    
    # 2. If not in cache, query PostgreSQL
    print("Fetching from PostgreSQL database!")
    db = SessionLocal()
    tasks = db.query(Task).all()
    db.close()
    
    tasks_list = [task.to_dict() for task in tasks]
    
    # 3. Save to Redis for the next request (expire in 60 seconds)
    redis_client.setex("all_tasks", 60, json.dumps(tasks_list))
    
    return jsonify(tasks_list)

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        db.delete(task)
        db.commit()
        redis_client.delete("all_tasks") # Invalidate cache
        db.close()
        return jsonify({"message": "Task deleted"}), 200
    db.close()
    return jsonify({"error": "Task not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### 🛑 Checkpoint 2
Look at `app.py`. Why do we delete `"all_tasks"` from `redis_client` when a task is created or deleted?
*(Answer: Cache invalidation. If the database changes, the cache is outdated. Deleting it forces the next `GET` request to fetch fresh data from the DB.)*

---

## PART 5: PostgreSQL Integration

In the root folder (`task-management-api/`), create a `.env` file. 

**`.env`**
```text
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=taskdb
```

**Why we use `.env`**: You should NEVER commit passwords or API keys to Github inside your code. We use `.env` files locally (and ignore them in `.gitignore`), and in production, we inject these as secure environment variables via our hosting provider.

**The Database URL:**
Look at `database.py`: `postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}`.
Notice `DB_HOST` defaults to `postgres`. 
In Docker networking, we DO NOT use `localhost` to connect containers. We use the service name. Docker automatically resolves `postgres` to the correct internal IP address of the database container.

Let's initialize the database. Create this inside `postgres/`:

**`postgres/init.sql`**
```sql
-- This file runs automatically when the PostgreSQL container is first created.
-- We can pre-populate some data here if we want!
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## PART 6: Redis Integration

Redis is an in-memory data store. Reading from memory (RAM) is vastly faster than reading from a hard drive (where PostgreSQL lives).

**Why caching exists**: If thousands of users ask for the *same* list of tasks, querying the database every time causes heavy load. Instead, we query the DB once, save the JSON response in Redis, and serve it directly from memory for the next 60 seconds.

**Flow in our `GET /tasks`**:
1. Request arrives.
2. Check Redis for key `"all_tasks"`.
3. If it exists -> Return it immediately (Sub-millisecond response).
4. If it doesn't exist -> Query PostgreSQL -> Store result in Redis -> Return response.

---

## PART 7: Dockerfiles

Create these in the `flask-api/` directory.

**`flask-api/Dockerfile`**
```dockerfile
# 1. Base image: We use slim to keep the image size small
FROM python:3.9-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. System dependencies required for psycopg2 (PostgreSQL driver)
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# 4. Copy only requirements first to leverage Docker layer caching
COPY requirements.txt .

# 5. Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the application code
COPY . .

# 7. Document the port
EXPOSE 5000

# 8. Command to run the app
CMD ["python", "app.py"]
```

**`flask-api/.dockerignore`**
```text
__pycache__
*.pyc
.env
venv/
.git/
```
**Why use `.dockerignore`**: It prevents unnecessary files (like your local `venv` or sensitive `.env` files) from being copied into the Docker image, reducing size and increasing security.

---

## PART 8: Docker Compose

This is the glue. Create this in the root `task-management-api/` folder.

**`docker-compose.yml`**
```yaml
version: '3.8'

services:
  flask-api:
    build: ./flask-api
    ports:
      - "5000:5000"
    env_file:
      - .env # Load variables from our .env file
    environment:
      - DB_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      postgres:
        condition: service_healthy # Wait for DB to be READY, not just started
      redis:
        condition: service_started
    networks:
      - backend-network

  postgres:
    image: postgres:15-alpine
    env_file:
      - .env
    volumes:
      # Named volume: Persist database data even if container is destroyed
      - pgdata:/var/lib/postgresql/data
      # Bind mount: Mount init.sql to run on first start
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - backend-network
    # HEALTHCHECK: Tell Docker how to verify if Postgres is actually ready to accept connections
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:alpine
    networks:
      - backend-network
    ports:
      - "6379:6379"

# Define the named volume
volumes:
  pgdata:

# Define a custom network
networks:
  backend-network:
    driver: bridge
```

### Explanation of key concepts:
* **`env_file`**: Injects everything in `.env` into the container safely.
* **`condition: service_healthy`**: In Day 2, `depends_on` just waited for the container to turn on. But a DB takes a few seconds to boot up. A health check ensures Flask waits until Postgres is *fully ready* to accept queries before starting.
* **`volumes: pgdata:/...`**: This maps the internal Postgres data directory to our Docker-managed volume called `pgdata`.

---

## PART 9: Running The Application

Open your terminal in the `task-management-api/` directory.

**1. Build the images:**
```bash
docker compose build
```

**2. Start everything in the background (`-d` for detached):**
```bash
docker compose up -d
```
*Internally: Docker creates the `backend-network`, creates the `pgdata` volume, starts Postgres and Redis. It waits for Postgres to pass its health check, then starts the Flask API.*

**3. Check the status:**
```bash
docker compose ps
```
You should see all three containers running and healthy.

**4. View logs for a specific service:**
```bash
docker compose logs -f flask-api
```

**5. Test the API:**
*   **POST:** `curl -X POST http://localhost:5000/tasks -H "Content-Type: application/json" -d '{"title": "Learn Docker", "description": "Master volumes and networks"}'`
*   **GET:** `curl http://localhost:5000/tasks` (Run this twice! The second time, check the Flask logs—you'll see it fetched from Redis).

**6. Stop everything:**
```bash
docker compose down
```
*(Because we used a volume, if you run `up` again, your tasks will still be there!)*

---

## PART 10: Debugging Practice

As a senior engineer, I spend 50% of my time debugging. Here are common errors and how to fix them:

**1. Database connection refused**
*   **Symptom:** Flask crashes with `sqlalchemy.exc.OperationalError: connection refused`.
*   **Solution:** You didn't wait for Postgres to be ready. Ensure you have the `healthcheck` block in Postgres and `condition: service_healthy` in Flask's `depends_on`.

**2. Redis connection error**
*   **Symptom:** `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379`.
*   **Solution:** You tried to connect to `localhost`. Change your code to connect to the service name `redis` instead.

**3. Container keeps restarting**
*   **Symptom:** `docker compose ps` shows the container restarting constantly.
*   **Solution:** The application crashed immediately upon startup. Run `docker compose logs <service_name>` to read the Python traceback. It's usually a syntax error or a missing package in `requirements.txt`.

**4. Data disappears after restart**
*   **Symptom:** You `docker compose down`, then `up`, and the database is empty.
*   **Solution:** You forgot to add a volume to the `postgres` service in `docker-compose.yml`.

**5. Environment variable not loading**
*   **Symptom:** DB authentication fails.
*   **Solution:** Make sure your `.env` file is in the exact same directory as your `docker-compose.yml`, and that you included `env_file: - .env` in the compose file.

---

## PART 11: Production Improvements

If we were deploying this to AWS today, we would improve two things:

**1. Health Checks**
We added one for Postgres. In production, we'd add one for Flask too (`GET /health`), so load balancers know if our API is alive. If the health check fails, the orchestrator (like Kubernetes) will automatically restart the container.

**2. Multi-stage Docker Builds**
Currently, our Flask image includes `gcc` and build tools required to install `psycopg2`. In production, we build the dependencies in "Stage 1", and copy only the final installed binaries to "Stage 2". This reduces image sizes from 500MB+ down to ~100MB, making deployments much faster and more secure.

**Dev vs Prod Docker Setup:**
*   **Dev:** Uses bind mounts (so you can edit code live), exposes DB ports to localhost (so you can use DataGrip/DBeaver), uses `.env` files.
*   **Prod:** Uses volumes, blocks DB ports from the outside world, injects secrets via the cloud provider's Secret Manager.

---

## PART 12: Mini Challenge

Ready to test your skills?

**Beginner:**
1.  **Add update endpoint:** Create a `PUT /tasks/<id>` endpoint to change a task's status to "completed". Don't forget to invalidate the Redis cache!
2.  **Add user table:** Create a `users` table in `models.py` and link tasks to a user via a Foreign Key.

**Intermediate:**
1.  **Add authentication:** Use JWT tokens. Only let logged-in users create tasks.
2.  **Add a worker microservice:** Add a new Python service called `email-worker`. When a task is created, Flask drops a message in Redis (using Redis Pub/Sub or Celery), and the worker reads it and prints "Sending email...".
3.  **Add Nginx reverse proxy:** Put an Nginx container in front of Flask to handle incoming HTTP traffic.

**Advanced:**
1.  **Deploy to VPS:** Rent a $5 DigitalOcean/AWS EC2 server, SSH into it, clone your repo, and run `docker compose up -d` in the cloud!

---

## Final Output

### 1. Complete Concepts Learned
*   **Data Persistence:** Using Named Volumes to protect DB data.
*   **Docker Networking:** Using service names as hostnames for inter-container communication.
*   **Healthchecks:** Ensuring dependencies (DB) are ready before the app starts.
*   **Multi-tier Architecture:** Connecting an API, a relational database, and an in-memory cache.
*   **Secrets Management:** Using `.env` files for configuration.

### 2. Docker Interview Questions
*   *"How do you ensure a database is ready before your API starts in Docker Compose?"* -> Use `depends_on` with `condition: service_healthy` and define a `healthcheck` block in the DB service.
*   *"What is the difference between a bind mount and a named volume?"* -> Bind mounts link a specific host folder to the container (good for dev live-reloading). Named volumes are managed entirely by Docker and abstract away the host path (good for DB data).
*   *"Why do we use `.dockerignore`?"* -> To keep build contexts small, speed up image builds, and prevent sensitive files like `.env` or `.git` from ending up in the image.

### 3. Practice Before Day 4
*   Build the exact project described above.
*   Intentionally break things: change the DB password in `.env` and watch the logs crash. Fix it.
*   Complete at least one Beginner and one Intermediate challenge.

### 4. How this connects to the real world
*   **Backend Engineering:** You just built a standard microservice architecture. 80% of backend engineering is wiring up APIs, databases, and caches in this exact way.
*   **Data Science Deployment:** Want to deploy a model? Wrap it in a Flask/FastAPI container, add a Redis queue for incoming predictions, and use Docker Compose to run it.
*   **Machine Learning APIs:** Large ML models take time to load. You can load the model in a background worker container, expose a fast API container, and use Redis to pass data between them, all orchestrated by Compose.

Congratulations on completing Day 3! You are now writing Docker configs like a pro.
