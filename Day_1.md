# Day 1: Introduction to Docker & Compose 🐳🐙

Welcome to Day 1! Today, we are going to learn what Docker is, how it works, how to use it to run a simple Python Flask application, and finally how to run multiple containers at once using Docker Compose.

---

## 1. What is Docker?

Imagine you write a really cool program on your laptop. You send the code to a friend, but when they try to run it, it crashes. Why? Because they might have a different operating system, a different version of Python, or they might be missing some hidden dependencies.

This is the classic **"It works on my machine"** problem.

**Docker** solves this by packaging your application along with *everything* it needs to run (libraries, dependencies, even a mini operating system) into a single, standardized unit called a **Container**.

Think of it like a physical shipping container. It doesn't matter what's inside (cars, electronics, or clothes); ships, cranes, and trucks all know exactly how to handle the container. Docker does the same thing for software.

---

## 2. Important Concepts: Dockerfile, Image, and Container

To understand Docker, you just need to know these three terms:

1. **Dockerfile**: The recipe. It's a simple text file with a list of instructions on how to build your application.
2. **Docker Image**: The blueprint. When you "build" a Dockerfile, it creates an Image. It's a read-only template that contains your code and everything needed to run it.
3. **Docker Container**: The running instance. When you "run" an Image, it becomes a Container. You can have many containers running from a single image.

*(Metaphor: The Dockerfile is the recipe, the Image is the cake mold, and the Container is the actual cake you can eat!)*

---

## 3. What is Docker Hub?

If Docker Images are the blueprints, **Docker Hub** is the library where you store them. 

Think of Docker Hub like **GitHub, but for Docker Images**. You can:
- **Pull (download)** official images made by others (like a pre-configured Python or Ubuntu image).
- **Push (upload)** your own images to share with the world or your team.

---

## 4. Hands-on Example: The Flask App

Let's look at the `flask` folder in our project. We have a simple web server built with Python. 

### The Application Files
- **`app.py`**: Our web server code. It starts a server on port 3000 and says `"Flask running inside Docker!"`.
- **`requirements.txt`**: Tells Python that our app needs the `flask` library to work.

### The Dockerfile Explained
Let's open the `Dockerfile` inside the `flask` folder and see how we instruct Docker to run our app:

```dockerfile
# 1. Base Image: We start with a lightweight version of Python 3.11 pre-installed.
FROM python:3.11-slim

# 2. Work Directory: We create a folder called /app inside the container and move there.
WORKDIR /app

# 3. Copy Requirements: We copy our requirements.txt from our computer to the container.
COPY requirements.txt .

# 4. Install Dependencies: We tell the container to install flask using pip.
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy Code: We copy our actual app.py code into the container.
COPY app.py .

# 6. Default Command: When the container starts, run this exact command: "python app.py"
CMD ["python", "app.py"]

# 7. Expose Port: Just a note that our app uses port 3000.
EXPOSE 3000
```

---

## 5. How to Build and Run It

To bring this all to life, open your terminal, navigate into the `flask` folder (`cd flask`), and run these two commands:

### Step 1: Build the Image
```bash
docker build -t my-first-flask-app .
```
- `docker build`: Tells Docker to read the Dockerfile.
- `-t my-first-flask-app`: Tags (names) our image so we can find it easily.
- `.`: Tells Docker the Dockerfile is in the current directory.

### Step 2: Run the Container
```bash
docker run -p 3000:3000 my-first-flask-app
```
- `docker run`: Starts a container from our image.
- `-p 3000:3000`: Maps port 3000 on your computer to port 3000 inside the container. 
- `my-first-flask-app`: The name of the image we just built.

### Step 3: Test It!
Open your web browser and go to: **http://localhost:3000**
You should see your Flask app running beautifully!

---

## 6. Common Mistakes: "Site Can't Be Reached" ⚠️

A very common mistake for beginners is running the container like this:
```bash
docker run my-first-flask-app
```

If you do this, your terminal might show that the server is running on `http://127.0.0.1:3000`, but when you open that in your browser, you get a **"Site Can't Be Reached"** error.

**Why did this happen?**
Because Docker containers run inside their own isolated network bubble. The Flask app is successfully running on port 3000 *inside* that bubble, but your computer (the outside world) has no way to reach it. 

**The Fix:**
You must use the **`-p` (publish port)** flag to poke a hole in that bubble, linking your computer's port to the container's port:
```bash
docker run -p 3000:3000 my-first-flask-app
```
Now, port 3000 on your machine connects directly to port 3000 in the container!

---

## 7. Essential Docker Commands Cheat Sheet 📝

Here are the most common commands you will use every day when working with Docker:

### Managing Containers
- **`docker ps`**: Lists all *currently running* containers.
- **`docker ps -a`**: Lists *all* containers (both running and stopped).
- **`docker stop <container_id_or_name>`**: Gracefully stops a running container.
- **`docker start <container_id_or_name>`**: Starts a stopped container.
- **`docker rm <container_id_or_name>`**: Deletes a stopped container. (Add `-f` to force delete a running one).

### Managing Images
- **`docker images`**: Lists all the Docker images you have downloaded or built on your machine.
- **`docker rmi <image_id_or_name>`**: Deletes an image from your machine.

### Debugging and Interacting
- **`docker logs <container_id_or_name>`**: Shows the output/logs of a container (very useful if your app crashes).
- **`docker logs -f <container_id_or_name>`**: Follows the logs in real-time.
- **`docker exec -it <container_id_or_name> sh`**: Opens a terminal *inside* the running container so you can poke around and explore the files.

### Cleaning Up
- **`docker system prune`**: The magic cleanup command! This removes all stopped containers, unused networks, and dangling images to free up space on your hard drive.

---
---

# Part 2: Docker Compose (The Conductor) 🐙

Now that you know how to build a single container, it's time to learn how to run a complete application with multiple moving parts.

## 8. What is Docker Compose?

If a `Dockerfile` is a recipe for **one** container, **Docker Compose** is the master blueprint for your **entire application architecture**. 

Most real-world apps aren't just one program. You usually have:
1. A backend server (like our Flask app).
2. A database (like PostgreSQL or Redis).
3. A frontend (like React).

Without Compose, you would have to manually build, run, and link all of these containers together using complex, long terminal commands. Docker Compose lets you define all these pieces in one single file and start them all up with one simple command.

*(Metaphor: If a Docker Container is a single musician, Docker Compose is the conductor that makes sure the whole orchestra plays together in perfect harmony.)*

## 9. How to Add Multiple Dockerfiles: The `docker-compose.yml`

To use Compose, we create a file named `docker-compose.yml`. This file uses a simple format called YAML to describe all the different "services" (containers) we want to run.

Here is an example `docker-compose.yml` that runs your Flask app alongside a Redis database:

```yaml
# The version of the compose file format
version: '3.8'

services:
  # Service 1: Our Web Application
  web:
    build: 
      context: ./flask     # Tells Compose where to find your Dockerfile
    ports:
      - "3000:3000"        # Maps port 3000 on your Mac to the container
    depends_on:
      - database           # Tells Docker to start the database BEFORE the web app

  # Service 2: The Database
  database:
    # Instead of building a Dockerfile, we just pull a ready-made image from Docker Hub!
    image: "redis:alpine"  
    ports:
      - "6379:6379"
```

**Notice two different ways to create a service here:**
1. The **`web`** service points to your `./flask` folder. Compose will look inside that folder, find the `Dockerfile`, and build it automatically. If you had another folder with a React frontend, you'd add a third service and point it to that folder's Dockerfile.
2. The **`database`** service doesn't need a Dockerfile! It just downloads the official `redis:alpine` image directly from Docker Hub.

## 10. Mac-Specific Commands 🍏

Since you are on a Mac, you will be using **Docker Desktop for Mac**. 

*Note for Mac users: Ensure you are using `docker compose` (with a space) and not the older `docker-compose` (with a hyphen).*

Open your Mac Terminal, navigate to the folder containing the `docker-compose.yml` file, and use these commands:

### Start the Orchestra 🎵
```bash
docker compose up
```
This single command reads the YAML file, builds your Flask Dockerfile, downloads the Redis image, connects them on a shared network, and starts them up.
- **Pro-tip**: Run `docker compose up -d` (the `-d` stands for "detached"). This runs everything in the background so you can keep typing in your terminal.

### Rebuild After Changing Code 🏗️
```bash
docker compose up --build
```
If you edit `app.py` or change your `Dockerfile`, you must add `--build`. This forces Docker to rebuild the Flask image with the fresh code before starting.

### Check What's Running 👀
```bash
docker compose ps
```
Shows a list of all the containers currently running for this specific project and what ports they are using.

### Stop Everything 🛑
```bash
docker compose down
```
When you are done working, this command gracefully stops all the containers and cleans up the background network. No more messy hanging processes!
