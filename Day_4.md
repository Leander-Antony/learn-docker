# Day 4: Nginx + Production Networking with Docker

Welcome back! I am your senior backend infrastructure mentor. Over the last three days, you've learned how to containerize apps, link them together, and add databases and caches.

Today, we are bridging the gap between a "works on my machine" setup and a **true production architecture**. We are going to learn how real traffic hits your servers, how to route it securely using Nginx, and how advanced Docker networking works.

This is a 60-minute deep dive. We will go slow, focus on the "why", and build a production-grade reverse proxy setup. Let's get started.

---

## PART 1: Understanding Production Traffic

When you are developing locally, you usually run your Flask app on port `5000` and go to `localhost:5000` in your browser. 

**Development Architecture:**
```text
Browser  --->  Flask Container (:5000)
```

In production, **we never expose our application containers (like Flask, Node, or Django) directly to the internet.** 

Why?
1. **Security**: Application servers aren't designed to handle malicious traffic, slow-client attacks, or massive DDoS attempts.
2. **Multiple Apps**: What if you want to run a React frontend and a Flask backend on the *same* server? You only have one port 80 (HTTP) and one port 443 (HTTPS). They can't both use it.

**Production Architecture:**
Instead, we place a shield in front of our applications.

```text
User Browser
     |
  Internet
     |
   Server
     |
 Reverse Proxy (Nginx)  <-- The Shield (Listens on Port 80/443)
     |
Application Container(s) <-- Hidden safely behind the proxy
```

### 🛑 Checkpoint 1
Why can't we just expose our Flask app directly on port 80 to the internet?
*(Answer: Security vulnerabilities, inability to easily host multiple services on the same domain/port, and poor performance handling thousands of raw, unoptimized connections.)*

---

## PART 2: Learn Nginx Fundamentals

### What is Nginx?
Nginx (pronounced "Engine-X") is an open-source powerhouse. It was originally built to solve the "C10K problem" (handling 10,000 concurrent connections). 

### What problems does it solve?
In modern infrastructure, Nginx wears many hats:
1. **Web Server**: It is incredibly fast at serving static files (HTML, CSS, JS, images).
2. **Reverse Proxy**: It receives requests and forwards them to the appropriate backend containers.
3. **Load Balancer**: It can distribute incoming traffic across multiple identical Flask containers to handle heavy load.
4. **SSL Termination**: It handles the math for HTTPS encryption, taking that burden off your Python code.

### Forward Proxy vs Reverse Proxy
*   **Forward Proxy**: Sits in front of the **client**. (e.g., A corporate VPN proxy that hides your laptop's IP from the internet).
*   **Reverse Proxy**: Sits in front of the **server**. (e.g., Nginx hiding your Flask backend from the internet). The client thinks they are talking to Nginx, they don't even know Flask exists!

---

## PART 3: Create Production Architecture

We are going to build a system with a Frontend, a Backend, and Nginx sitting in front routing traffic.

Create this folder structure:

```text
nginx-docker-production/
│
├── docker-compose.yml
│
├── nginx/
│   ├── nginx.conf
│   └── Dockerfile
│
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
│
└── frontend/
    ├── index.html
    └── Dockerfile
```

**The Architecture:**
```text
              User (Browser)
                   |
             Nginx (Port 80)
               /        \
   (If path is /)      (If path is /api)
             /            \
    Frontend Container    Backend Flask Container
```

---

## PART 4: Create Flask Backend

Let's create the backend hidden API. Inside the `backend/` folder:

**`backend/app.py`**
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/message', methods=['GET'])
def get_message():
    # A simple API response
    return jsonify({"message": "Hello from backend in production!"})

if __name__ == '__main__':
    # We still bind to 0.0.0.0 so Nginx can reach us inside the Docker network.
    app.run(host='0.0.0.0', port=5000)
```

**`backend/requirements.txt`**
```text
Flask==2.3.2
```

**`backend/Dockerfile`**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# We expose 5000, but only internally to the Docker network.
EXPOSE 5000
CMD ["python", "app.py"]
```

**Why we don't expose ports publicly:** 
If we put `ports: - "5000:5000"` in our `docker-compose.yml` for this backend, anyone on the internet could bypass Nginx and hit our backend directly. By leaving that out, the backend remains completely inaccessible from the outside world. It only talks to Nginx.

---

## PART 5: Create Frontend Container

Let's create a simple static frontend that calls our API. Inside `frontend/`:

**`frontend/index.html`**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Production App</title>
</head>
<body>
    <h1>Our Production App</h1>
    <p>Message from backend: <strong id="msg">Loading...</strong></p>

    <script>
        // Notice we call /api/message, NOT http://localhost:5000/api/message!
        fetch('/api/message')
            .then(response => response.json())
            .then(data => {
                document.getElementById('msg').innerText = data.message;
            })
            .catch(error => console.error('Error:', error));
    </script>
</body>
</html>
```

**`frontend/Dockerfile`**
```dockerfile
# We can use Nginx itself just to serve this static file internally
FROM nginx:alpine
# Copy our static HTML file into the default Nginx web directory
COPY index.html /usr/share/nginx/html/index.html
```

### Why didn't the frontend call `localhost:5000`?
When the `fetch()` javascript runs, it runs in the **User's Browser**, miles away from your server. If the code said `fetch('http://localhost:5000')`, the user's laptop would try to call its own port 5000, which has nothing there!
Instead, we use a relative path (`/api/message`). The browser sends the request to the same domain serving the HTML (our Nginx proxy), and Nginx will handle routing it to the backend.

---

## PART 6: Docker Networking Deep Dive

Let's talk about the magic allowing Nginx to find these containers.

```text
Container A  <--->  [ Docker Bridge Network ]  <--->  Container B
```

*   **Bridge Networks**: When you run Compose, it creates an isolated virtual LAN (Local Area Network) called a Bridge Network. 
*   **Container DNS**: Docker has a built-in DNS server. If Container A pings `backend`, Docker resolves that name to Container B's internal IP address (e.g., `172.18.0.3`).
*   **The Localhost Trap**: Inside a container, `localhost` means *that specific container*. If Nginx forwards traffic to `localhost:5000`, Nginx is looking for a Flask app running *inside the Nginx container itself*. 
**Rule of thumb:** In Docker, containers talk to each other using their Service Names, never `localhost`.

---

## PART 7: Nginx Configuration

This is the brain of our operation. Inside `nginx/`:

**`nginx/nginx.conf`**
```nginx
# Define the events block (required by Nginx)
events {
    worker_connections 1024;
}

# The http block contains our web server configuration
http {
    # Define a server that listens for incoming traffic
    server {
        # Listen on port 80 (standard HTTP port)
        listen 80;

        # Route 1: The Frontend (Root path)
        # Any request starting with '/' goes here.
        location / {
            # proxy_pass forwards the request to our frontend container.
            # 'frontend' is the service name in docker-compose.yml
            proxy_pass http://frontend:80;
        }

        # Route 2: The Backend API
        # Any request starting with '/api/' goes here.
        location /api/ {
            # Forward to the Flask backend container on its internal port 5000
            proxy_pass http://backend:5000;
            
            # These headers pass important information about the original client to Flask
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
```

### Explaining the lines:
*   `server {}`: Defines a virtual server. You can have multiple servers for different domains (e.g., one for `api.example.com`, one for `www.example.com`).
*   `location / {}`: A routing block. It matches URLs against a path.
*   `proxy_pass`: The most important command. It tells Nginx: "Stop here, take this request, and pass it verbatim to this other server/container."
*   `headers`: Nginx acts as a middleman. If Flask checks the client's IP, it will see Nginx's IP. The `X-Real-IP` headers pass the actual user's IP down to Flask so your logs are accurate.

**`nginx/Dockerfile`**
```dockerfile
FROM nginx:alpine
# Replace the default Nginx config with our custom one
COPY nginx.conf /etc/nginx/nginx.conf
```

---

## PART 8: Docker Compose Setup

Let's wire it all together in the root folder.

**`docker-compose.yml`**
```yaml
version: '3.8'

services:
  # 1. The Shield (Publicly accessible)
  reverse-proxy:
    build: ./nginx
    ports:
      # THIS IS THE ONLY PORT EXPOSED TO YOUR MAC/PC/INTERNET
      - "80:80"
    depends_on:
      - frontend
      - backend
    networks:
      - app-network

  # 2. The Frontend (Internal only)
  frontend:
    build: ./frontend
    networks:
      - app-network
    # Notice: NO ports block! It is completely hidden from the outside.

  # 3. The Backend (Internal only)
  backend:
    build: ./backend
    networks:
      - app-network
    # Notice: NO ports block!

networks:
  app-network:
    driver: bridge
```

### 🛑 Checkpoint 2
If you run this setup and try to access `http://localhost:5000` directly in your browser, what will happen?
*(Answer: It will fail / Connection Refused. Port 5000 is not exposed to the host machine. You can only access the backend by going through Nginx at `http://localhost/api/`)*

---

## PART 9: Add Production Features

While our setup is good, a senior engineer configures Nginx to do much more:

1. **Static File Serving**: Nginx is 100x faster than Flask at serving images/CSS. You can configure Nginx to serve a `/static/` folder directly from the hard drive, bypassing Python entirely.
2. **Compression (Gzip/Brotli)**: Nginx can zip JSON responses and HTML before sending them over the wire, reducing bandwidth by 80%.
3. **Caching**: Nginx can cache the output of slow Flask API calls for a few minutes.
4. **Security Headers**: Adding `Strict-Transport-Security` or `X-Frame-Options` to prevent Clickjacking.
5. **Rate Limiting**: Prevent abuse by telling Nginx "Only allow 10 requests per second per IP address". 

---

## PART 10: HTTPS and SSL Basics

Right now we are using **HTTP** (Port 80). Data is sent in plain text. If a user logs in, a hacker on the same coffee shop WiFi can see their password.

In production, you MUST use **HTTPS** (Port 443). 

**How it works:**
```text
Client  ---(Encrypted TLS connection)--->  Nginx  ---(Unencrypted, safe internal network)---> Flask
```

1.  **SSL Certificates**: Nginx holds a cryptographic certificate proving it owns the domain (`example.com`).
2.  **TLS Handshake**: When a browser connects, Nginx and the browser secretly agree on an encryption key.
3.  **Let's Encrypt**: A free service that gives you SSL certificates. In production, we often run a sidecar container like `Certbot` that automatically talks to Let's Encrypt and rotates our Nginx certificates every 90 days.

*Note: We won't implement HTTPS locally right now, as you need a real domain name for Let's Encrypt to verify.*

---

## PART 11: Load Balancing

What if one Flask container isn't enough to handle your traffic?
Nginx makes scaling incredibly easy.

**Architecture:**
```text
              Nginx
                |
        -----------------
        |       |       |
     Flask 1  Flask 2 Flask 3
```

With Docker Compose, you can run `docker compose up --scale backend=3`.
Compose creates three backend containers. Because Docker's internal DNS is smart, when Nginx resolves the name `backend`, Docker automatically uses **Round Robin** to distribute the requests evenly among the three containers!

*(Round Robin: Request 1 goes to Container A, Request 2 goes to Container B, Request 3 goes to C, Request 4 goes back to A).*

---

## PART 12: Debugging Practice

When using Nginx, errors look different.

**Problem 1: Nginx gives a "502 Bad Gateway" page.**
*   *Cause:* Nginx received the request, but when it turned around to hand it to Flask, Flask wasn't there.
*   *Solution:* 
    1. Your backend container stopped or crashed (`docker compose ps`).
    2. You used the wrong service name in `proxy_pass` (e.g., `http://back_end` instead of `http://backend`).
    3. Flask is listening on `127.0.0.1` instead of `0.0.0.0`.

**Problem 2: Frontend loads, but API data is missing/failing.**
*   *Cause:* The frontend's Javascript is trying to hit an API endpoint that Nginx isn't routing correctly.
*   *Solution:* Open Chrome Developer Tools -> Network tab. See exactly what URL the frontend requested. Does it match your Nginx `location` block?

**Problem 3: Nginx container crashes immediately on startup.**
*   *Cause:* You made a typo in `nginx.conf` (e.g., missing a semicolon `;`).
*   *Solution:* Run `docker compose logs reverse-proxy`. Or, to test a config file manually, you can run `nginx -t` inside the container.

---

## PART 13: Hands-On Challenge

Your turn.
Build the `nginx-docker-production` folder structure detailed above.
1. Create all the files and paste in the code.
2. Run `docker compose build` and `docker compose up -d`.
3. Open your browser to `http://localhost`. You should see the frontend loading the data through Nginx!
4. **Challenge**: Try adding a `/api/health` endpoint in Flask, and make sure you can reach it via `http://localhost/api/health`.

---

## Final Output

### 1. Complete Day 4 Summary
Today you moved from a developer mindset to an infrastructure mindset. You learned that production applications must be shielded by a Reverse Proxy (Nginx) for security, routing, and performance. You built a secure internal network where your application code is invisible to the outside world, and only Nginx manages the gateway.

### 2. Important Nginx Commands
*(Note: These run inside the Nginx container, or are useful to know)*
*   `nginx -t`: Tests the syntax of your `nginx.conf` file for errors.
*   `nginx -s reload`: Reloads the configuration without dropping active connections (zero-downtime config updates).
*   `proxy_pass <url>`: The holy grail of reverse proxying.

### 3. Docker Networking Interview Questions
*   *"If a frontend container needs to call a backend container API, should the javascript `fetch()` call the backend's internal container name or the public Nginx URL?"* -> It MUST call the public Nginx URL. Javascript executes in the client's browser, which is outside the Docker network.
*   *"What does exposing a port in Docker Compose do vs just specifying a port internally?"* -> Exposing (`ports: - "80:80"`) binds a port on the host machine to the container, opening it to the outside. Specifying it internally means it is only accessible to other containers on the same Docker Bridge network.

### 4. Production Architecture Diagram
```text
[ INTERNET ]
     |
     v (HTTPS :443)
[ NGINX REVERSE PROXY ]
  /                 \
 / (Path /)          \ (Path /api/)
v                     v
[ STATIC FRONTEND ]   [ FLASK API ]
                      |
                      v
                [ POSTGRES DB ]
```

### 5. How this knowledge helps you in the real world:
*   **Deploying ML Models:** Machine learning models are often wrapped in simple web servers (like Flask or FastAPI). You should *never* expose an raw ML server to the internet. Nginx acts as the buffer, handling SSL, rate limiting so your GPU doesn't get DDoSed, and routing.
*   **FastAPI Inference Servers:** FastAPI is incredibly fast, but it's still an application server. Putting Nginx in front lets Nginx serve static assets (like a dashboard) and route only the heavy API inference requests to FastAPI.
*   **Real-world Backend Systems:** This exact pattern (Nginx -> App Servers -> DB) powers millions of websites, from small startups to enterprise architectures. You now understand the fundamental blueprint of the web.

Great work today! You are now capable of architecting and deploying secure, production-ready multi-container environments.
