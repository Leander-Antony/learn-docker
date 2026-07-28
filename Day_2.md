# Welcome to Day 2: Docker Compose Masterclass

Welcome back! Yesterday, you took your first steps into the world of containers. Today, we are going to level up significantly. As a backend engineer, you rarely run just *one* container. A real-world application usually has an API, a database, a cache (like Redis), and maybe a background worker.

Running all of these manually with `docker run` commands would be a nightmare. This is where **Docker Compose** comes in.

Grab a coffee, and let's dive in. This session will take about 30-45 minutes.

---

## 1. Quick Recap of Day 1

Before we move forward, let's make sure our foundation is solid. Here is what we covered yesterday:

*   **Images**: Think of an image as a read-only blueprint. It contains your code, runtime, libraries, and environment variables.
*   **Containers**: A container is a running instance of an image. If the image is the class, the container is the object.
*   **Dockerfile**: A text file containing the step-by-step instructions to create your Docker image (e.g., `FROM python:3.9`, `COPY . /app`, `RUN pip install -r requirements.txt`).
*   **`docker build -t my-app .`**: The command that reads your Dockerfile and builds the image.
*   **`docker run -p 8080:80 my-app`**: The command that takes your image and starts a container.
*   **Ports**: We use `-p <host_port>:<container_port>` to forward traffic from our laptop into the container.
*   **Volumes**: We use `-v` to persist data so it survives when the container is destroyed, or to mount our local source code into the container for live reloading.

**The Basic Workflow:** Write Code -> Write Dockerfile -> `docker build` -> `docker run`.

---

## 2. Introducing Docker Compose

### Why does Docker Compose exist?

Imagine a project with a React frontend, a Node.js backend, a PostgreSQL database, and a Redis cache.
To start this project using Day 1 knowledge, you would have to open four terminals and run something like:

1.  `docker run -d --name redis redis:alpine`
2.  `docker run -d --name postgres -e POSTGRES_PASSWORD=secret postgres:13`
3.  `docker run -d -p 3000:3000 --link postgres --link redis my-backend`
4.  `docker run -d -p 80:80 --link my-backend my-frontend`

*The problems:*
1.  **Too much typing**: Remembering all those flags (`-p`, `-e`, `--name`, `--link`) is error-prone.
2.  **Order matters**: The backend needs the database to be running first.
3.  **Networking is hard**: Getting containers to talk to each other securely requires setting up Docker networks manually.

### The Solution

**Docker Compose** is a tool for defining and running multi-container Docker applications. With Compose, you use a single YAML file (`docker-compose.yml`) to configure all your application's services, networks, and volumes.

Then, with a **single command** (`docker compose up`), you create and start all the services from your configuration.

### Key Concepts in Compose

*   **Services**: A service is just a container in production. In our example, the frontend, backend, and database are all separate "services".
*   **Networks**: Compose automatically creates a private network for your app. Services on the same network can talk to each other using their service names as hostnames.
*   **Volumes**: Used to share data between containers or persist data on your host machine.
*   **Environment Variables**: Easily pass configuration to your containers.
*   **Dependencies (`depends_on`)**: Tell Compose to start Service B only after Service A is running.

---

## 3. YAML Basics (Just enough to be dangerous)

Docker Compose files are written in YAML (`.yml` or `.yaml`). YAML stands for "YAML Ain't Markup Language". It's designed to be easily readable by humans.

Here are the golden rules of YAML:

1.  **Indentation is EVERYTHING**: YAML uses spaces to denote structure. **NEVER use tabs.** Usually, we use 2 spaces per indentation level. If your indentation is wrong, your file is broken.
2.  **Key-Value Pairs**: Data is represented as a key, followed by a colon and a space, then the value.
    ```yaml
    name: "John Doe"
    age: 30
    ```
3.  **Lists (Arrays)**: Use a hyphen and a space (`- `) for lists.
    ```yaml
    hobbies:
      - coding
      - reading
      - gaming
    ```
4.  **Nested Structures**: You can nest dictionaries inside dictionaries.
    ```yaml
    database:
      type: postgres
      port: 5432
    ```

***

### 🛑 Checkpoint 1

Look at this YAML snippet. Is there an error? If so, what is it?
```yaml
web:
  image: nginx:latest
 ports:
    - "80:80"
```
*(Think about it before moving on!)*
**Answer:** Yes! The word `ports:` is indented with one space, but it should be indented with two spaces to align with `image:`.

***

## 4. Hands-on Project: Microservices with Flask

We are going to build a mini microservice architecture.

**The Architecture:**
*   **user-service**: A simple API that returns a hardcoded list of users.
*   **api-gateway**: The "front door" API. It will receive a request from you, internally call the `user-service`, and return the result.

```text
You (Browser/Curl)  -->  [ api-gateway (Port 5000) ]  -->  [ user-service (Internal Port 5001) ]
```

### Step 1: Create the Folder Structure

I want you to create this directory structure on your machine. I'll provide the code for every file below.

```text
docker-compose-flask-project/
│
├── docker-compose.yml
│
├── user-service/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
│
└── api-gateway/
    ├── app.py
    ├── requirements.txt
    └── Dockerfile
```

### Step 2: The `user-service`

Create these files inside the `user-service/` folder.

**`user-service/app.py`**
```python
from flask import Flask, jsonify

app = Flask(__name__)

# A simple endpoint returning mock data
@app.route('/users', methods=['GET'])
def get_users():
    users = [
        {"id": 1, "name": "Alice", "role": "Admin"},
        {"id": 2, "name": "Bob", "role": "User"}
    ]
    return jsonify(users)

if __name__ == '__main__':
    # Notice host='0.0.0.0'. This is CRITICAL in Docker. 
    # It tells Flask to listen on all network interfaces, not just localhost.
    app.run(host='0.0.0.0', port=5001) 
```

**`user-service/requirements.txt`**
```text
Flask==2.3.2
Werkzeug==2.3.6
```

**`user-service/Dockerfile`**
```dockerfile
# Start with a lightweight Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first (for efficient caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of our application code
COPY . .

# Expose the port the app runs on (documentation purpose mostly)
EXPOSE 5001

# The command to run when the container starts
CMD ["python", "app.py"]
```

### Step 3: The `api-gateway`

Now, let's create the gateway that will talk to the user service. Create these inside `api-gateway/`.

**`api-gateway/app.py`**
```python
from flask import Flask, jsonify
import requests
import os

app = Flask(__name__)

# We use an environment variable to find the user service.
# This makes our code flexible (we can change the URL without changing code).
USER_SERVICE_URL = os.environ.get('USER_SERVICE_URL', 'http://localhost:5001')

@app.route('/api/users', methods=['GET'])
def fetch_users():
    try:
        # Make an HTTP GET request to the user-service
        response = requests.get(f"{USER_SERVICE_URL}/users")
        # Ensure the request was successful
        response.raise_for_status()
        
        # Return the data we got from the user-service
        return jsonify({
            "message": "Data fetched via API Gateway successfully!",
            "data": response.json()
        })
    except requests.exceptions.RequestException as e:
        # Handle connection errors gracefully
        return jsonify({"error": "Could not connect to user-service", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**`api-gateway/requirements.txt`**
```text
Flask==2.3.2
Werkzeug==2.3.6
requests==2.31.0
```

**`api-gateway/Dockerfile`**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

### Step 4: The Glue - `docker-compose.yml`

This is the magic file. Create it in the root folder (`docker-compose-flask-project/`).

**`docker-compose.yml`**
```yaml
version: '3.8' # The version of the compose file format

services: # This block defines all the containers we want to run

  # Service 1: The User API
  user-service: 
    build: 
      context: ./user-service # Where to find the Dockerfile for this service
    ports:
      # Expose port 5001 to the host so we can test it directly if we want
      - "5001:5001" 
    
  # Service 2: The Gateway API
  api-gateway:
    build:
      context: ./api-gateway
    ports:
      # Map host port 5000 to container port 5000. 
      # This is how YOU access the app from your browser.
      - "5000:5000"
    environment:
      # Set the environment variable used by our Python code.
      # CRITICAL: Notice the URL is 'http://user-service:5001'
      - USER_SERVICE_URL=http://user-service:5001
    depends_on:
      # Tell Compose to start user-service before api-gateway
      - user-service
```

***

### 🛑 Checkpoint 2

Look at the `environment` section for `api-gateway` in the YAML file above. 
Why is the URL `http://user-service:5001` instead of `http://localhost:5001`? 
*(Read the next section for the answer!)*

***

## 5. Container Networking Deep Dive (The "Localhost" Trap)

This is the **#1 mistake** beginners make.

When you run a Flask app locally on your laptop, it runs on `localhost`. If App A tries to reach App B on `localhost:5001`, it works perfectly because they share the same network (your laptop).

**In Docker, every container is its own isolated little computer.**

If `api-gateway` tries to connect to `localhost:5001`, it is looking inside *its own container* for something running on port 5001. But `user-service` isn't in that container; it's in a different one!

**How Docker Compose solves this (Docker DNS):**

When you run `docker compose up`, Docker automatically creates a custom internal network for your project. 
It then provides a built-in DNS (Domain Name System) server. 

The DNS server maps the **service names** defined in your `docker-compose.yml` to the internal IP addresses of those containers.

Because we named our service `user-service` in the YAML file:
```yaml
services:
  user-service: # <--- THIS NAME
```
Docker makes the hostname `user-service` automatically resolve to that specific container. 
That's why `api-gateway` can simply make a request to `http://user-service:5001`!

## 6. Running the Project

Open your terminal, navigate to the `docker-compose-flask-project` folder, and let's run some commands.

### 1. Build the images
```bash
docker compose build
```
*What happens internally:* Docker reads the `docker-compose.yml`, finds the `build: ./folder` paths, goes into each folder, and runs `docker build` using the Dockerfile there. It tags the images automatically (e.g., `docker-compose-flask-project_api-gateway`).

### 2. Start the application
```bash
docker compose up
```
*(Tip: Add `-d` at the end to run in detached mode, freeing up your terminal).*

*What happens internally:* 
1. Compose creates a network (e.g., `docker-compose-flask-project_default`).
2. It starts `user-service` first (because of `depends_on`).
3. It starts `api-gateway`.
4. It attaches both to the network and streams their logs to your terminal.

**Test it!**
Open your browser or use curl:
*   `http://localhost:5001/users` -> You hit the user-service directly.
*   `http://localhost:5000/api/users` -> You hit the gateway, which internally talks to the user-service!

### 3. See what's running
Open a *new* terminal window in the same directory.
```bash
docker compose ps
```
*What happens internally:* Lists all containers managed by this specific `docker-compose.yml` file and shows their status and port mappings.

### 4. View logs (if you ran in `-d` mode)
```bash
docker compose logs -f
```
*What happens internally:* Aggregates the logs from *all* services into one stream. The `-f` means "follow" (live tail). You can also view logs for just one service: `docker compose logs api-gateway`.

### 5. Stop and tear down
```bash
docker compose down
```
*What happens internally:* It stops all the containers, removes them, and deletes the custom network it created. Your system is clean again.

---

## 7. Debugging Practice: Common Errors

As a mentor, I want you to be prepared when things break.

### Error 1: Port already in use
**Symptom:** `Error starting userland proxy: listen tcp4 0.0.0.0:5000: bind: address already in use`
**Why:** You already have something running on your Mac/PC on port 5000 (maybe another Docker container, or a local Flask app).
**Fix:** Change the host port mapping in `docker-compose.yml` to something else, like `"8080:5000"`. (Example: `- "8080:5000"`)

### Error 2: ModuleNotFoundError
**Symptom:** Container crashes immediately. Logs show `ModuleNotFoundError: No module named 'requests'`
**Why:** You forgot to add `requests` to your `requirements.txt`, or you added it but forgot to rebuild the image.
**Fix:** Add it to `requirements.txt`, then run `docker compose build --no-cache` to force a clean build, then `docker compose up`.

### Error 3: Container exits immediately (Status 0)
**Symptom:** `docker compose ps` shows the container is "Exited (0)". 
**Why:** The command inside `CMD []` finished executing. Containers only stay alive as long as their main process is running. If your python script throws an error and dies, or just finishes its task, the container stops.
**Fix:** Check `docker compose logs <service_name>` to see the exact python traceback.

### Error 4: Cannot connect between services
**Symptom:** API Gateway returns 500 error, logs show `requests.exceptions.ConnectionError: Failed to establish a new connection: [Errno 111] Connection refused`
**Why:** 
1. `user-service` is not running. 
2. `user-service` is listening on `127.0.0.1` instead of `0.0.0.0`. 
3. The `USER_SERVICE_URL` environment variable has a typo in the hostname or port.
**Fix:** Ensure `host='0.0.0.0'` in `app.py`. Ensure the service name matches perfectly in the YAML file.

---

## 8. Your Homework / Practice Tasks

To truly master this, you need keyboard time. Create the folder structure and try these tasks before our next lesson:

**Beginner Tasks:**
1.  **Add an endpoint:** Add a `GET /health` endpoint to `user-service` that returns `{"status": "healthy"}`.
2.  **Change Ports:** Change the `api-gateway` to expose port `8080` to your host machine instead of `5000`.
3.  **Volumes:** Modify the `docker-compose.yml` to map your local `./api-gateway` folder to `/app` inside the container, so you can edit the Python code and see changes without rebuilding! (Hint: Look up `volumes:` syntax).

**Intermediate Tasks (For the brave):**
1.  **Add a third service:** Create an `inventory-service` (port 5002). Update the gateway to fetch data from both users and inventory.
2.  **Add Redis:** Add a `redis:alpine` container to your `docker-compose.yml`. Update `api-gateway` to cache the response from `user-service` in Redis for 10 seconds.

---

## 9. Summary & Interview Prep

### What we learned today:
*   **Docker Compose** is for orchestrating multi-container applications using declarative YAML.
*   **Networking:** Compose creates a custom network. Containers communicate using **Service Names** as DNS hostnames (no `localhost`!).
*   **Workflow:** `build`, `up`, `ps`, `logs`, `down`.
*   **Configuration:** We used Environment Variables in Compose to inject dynamic URLs into our code.

### 📝 Pop Quiz / Interview Questions

1.  **"What is the difference between `docker run` and `docker compose`?"**
    *   *Answer:* `docker run` is a CLI command to start a single container. `docker compose` is a tool (using a YAML file) to configure, start, and manage multiple interconnected containers and their networks/volumes as a single unit.
2.  **"If I have a web container and a database container in Compose, how does the web container connect to the database?"**
    *   *Answer:* It uses the service name defined in the `docker-compose.yml` (e.g., `db`) as the hostname in its connection string. Compose's internal DNS handles the routing.
3.  **"Why did you use `host='0.0.0.0'` in your Flask app inside Docker?"**
    *   *Answer:* By default, Flask binds to `127.0.0.1` (localhost). Inside a container, `localhost` means the container itself. To accept connections from outside the container (like from the host machine or other containers), the app must bind to `0.0.0.0` (all network interfaces).

### 🚀 Teaser for Day 3:
Awesome job today! Tomorrow (Day 3), we are going to look at **Data Persistence**. We will add a PostgreSQL database container, learn how to keep our data safe when containers are destroyed, and explore Docker Volumes in depth. 

Let me know when you are done with the practice tasks and ready for Day 3!
