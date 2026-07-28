# Day 6: Cloud Deployment with Docker

Welcome to Day 6! I am your Cloud and DevOps mentor. 

Over the past five days, you've mastered containers, orchestrated multi-service architectures, set up reverse proxies, and automated your workflows. Today is the day we go live. We are taking everything you've built and putting it on the internet for the world to use.

This is a comprehensive 60-90 minute lesson on how real companies deploy backend systems and ML models to the cloud. We will cover server provisioning, manual deployment, domain names, security, and connecting your CI/CD pipeline. 

Let's dive in.

---

## PART 1: Understanding Cloud Deployment

### Why do applications need servers?
When you develop on your laptop, the app only exists while your laptop is awake and connected to WiFi. You are the only user. If you want 1,000 users across the globe to use your app 24/7, you need a computer that never sleeps, has a massive internet connection, and is highly secure.

**Local vs Cloud:**
```text
[ Local ] My Laptop ---> Docker Containers (Available only to me)
[ Cloud ] User Browser ---> Internet ---> Cloud Server ---> Docker Containers (Available to everyone)
```

### What is Cloud Computing?
Instead of buying a $10,000 physical server and putting it in a closet, you "rent" a slice of a massive server owned by Amazon (AWS), Google (GCP), or Microsoft (Azure). You pay by the minute, and you can destroy it when you're done.

**Why companies use the cloud:**
*   **Scalability**: If your app goes viral, you can click a button and get 10x more CPU power in 60 seconds.
*   **Reliability**: If a hard drive fails in an Amazon data center, they transparently move your app to a new hard drive.
*   **Availability**: Data centers have backup power generators and massive internet pipes. Your app stays up 99.99% of the time.
*   **Global Access**: You can deploy a server in Tokyo, London, and New York simultaneously to serve users faster.

### 🛑 Checkpoint 1
If you are launching a new startup and expect unpredictable traffic (maybe 10 users, maybe 10,000), why is Cloud Computing better than buying your own physical server?
*(Answer: Scalability. You don't have to guess and over-pay for hardware upfront. You scale up only when traffic hits, and scale down to save money when it drops.)*

---

## PART 2: Cloud Service Models

When you rent from the cloud, you can choose how much "management" you want to do yourself.

1.  **IaaS (Infrastructure as a Service)**: You rent raw hardware (A Virtual Machine/Server). You must install the OS, Docker, and manage everything. (Examples: AWS EC2, DigitalOcean Droplets).
2.  **PaaS (Platform as a Service)**: You just provide your code or Docker Image, and the platform handles the servers, networking, and scaling automatically. (Examples: Heroku, AWS Elastic Beanstalk, Google Cloud Run).
3.  **SaaS (Software as a Service)**: The fully finished product you sell to customers. (Examples: Gmail, Slack).

**Where Docker fits:**
We usually deploy Docker on **IaaS** (by installing Docker on a rented server) or on specialized Container PaaS platforms (like AWS ECS or Kubernetes). Today, we will use IaaS to learn how the raw plumbing works.

---

## PART 3: Virtual Machines and Servers

### What is a VPS?
VPS stands for Virtual Private Server. Cloud providers have massive physical machines (Host nodes). They use software (Hypervisors) to slice that physical machine into smaller, isolated "Virtual Machines". 

```text
Physical Server (64 Cores, 256GB RAM)
        |
        |---> Virtual Machine 1 (Ubuntu, 2 Cores, 4GB RAM)  <-- You rent this!
        |       |---> Docker Containers
        |
        |---> Virtual Machine 2 (CentOS, 4 Cores, 8GB RAM)  <-- Someone else rents this
```

### Choosing Server Specifications
When you rent a VPS, you choose:
*   **CPU**: Handles computations. (Web routing, logic).
*   **RAM**: Holds data in memory. (Databases, Caches, ML models loading into memory).
*   **Storage**: Hard drive space. (Logs, database files).
*   **Network Ports**: The doors to your server (Port 80/443).

**Examples:**
*   **Small Flask API**: 1-2 vCPUs, 1GB - 2GB RAM is plenty.
*   **Large ML API**: Requires heavy RAM to load the model (8GB+), lots of CPU for inference, and potentially a specialized GPU server if running deep learning models.

---

## PART 4: Create Cloud Deployment Project

We are going to deploy the complete architecture from Day 4 and 5.

**The Architecture:**
```text
                 User
                  |
                  |
         [ Cloud Server IP ]
                  |
                Nginx (:80/:443)
                  |
       ----------------------
       |                    |
    Frontend             Backend
                            |
                  ----------------
                  |              |
              PostgreSQL       Redis
```

---

## PART 5: Setting Up a Cloud Server

*(To do this for real, you would create an account on AWS, DigitalOcean, or Linode).*

When you provision a server, you get:
1.  **Public IP Address**: The unique address (e.g., `198.51.100.23`) that anyone on the internet can use to reach your server.
2.  **Private IP Address**: Used only for servers within the same cloud datacenter to talk to each other securely.
3.  **Firewall (Security Groups)**: A digital bouncer. By default, it blocks EVERYTHING. You must explicitly open Port 22 (SSH), Port 80 (HTTP), and Port 443 (HTTPS).

### Connecting to your Server (SSH)
You manage cloud servers via the command line using **SSH (Secure Shell)**.

```bash
ssh root@198.51.100.23
```
*What happens internally:* Your laptop reaches out to the server on Port 22. The server asks for cryptographic proof of your identity (an SSH Key) or a password. If correct, you are granted an encrypted terminal session directly into the cloud server.

---

## PART 6: Server Preparation

When you log into a brand new Linux server, it's totally empty. Production servers should be minimal—do not install graphical interfaces (GUI) or unnecessary software. It keeps them fast and reduces security vulnerabilities.

You must install three things:
1. Docker
2. Docker Compose
3. Git

Once installed, you verify them:
```bash
docker --version
docker compose version
git --version
```

---

## PART 7: Deploy Application Manually

Let's do the initial deployment by hand so you understand the mechanics.

**Step 1. Clone the repository**
```bash
git clone https://github.com/your-username/production-flask-app.git
cd production-flask-app
```

**Step 2. Create environment variables**
Never commit `.env` to Git. You must recreate it securely on the server.
```bash
nano .env 
# (Type your secrets: POSTGRES_PASSWORD=supersecret... then save and exit)
```

**Step 3. Build the containers**
```bash
docker compose build
```

**Step 4. Start the application**
```bash
docker compose up -d
```

**Step 5. Check status and logs**
```bash
docker compose ps
docker compose logs -f backend
```

At this point, if you type your server's Public IP into your browser, you will see your app live!

### 🛑 Checkpoint 2
Why did we use `nano .env` on the server instead of just pushing the `.env` file to GitHub with `git commit`?
*(Answer: Committing secrets to a git repository is a massive security risk. Anyone with access to the repo—or the public internet if the repo is public—can steal your database passwords.)*

---

## PART 8: Domain and DNS

Typing `198.51.100.23` is terrible for user experience. We need a domain name (like `example.com`).

**DNS (Domain Name System)** is the phonebook of the internet. It translates human-readable names into IP addresses.

**The DNS Flow:**
```text
Browser types example.com
       |
Browser asks DNS Server: "Who is example.com?"
       |
DNS Server replies: "198.51.100.23"
       |
Browser connects to Cloud Server IP -> Nginx -> Application
```

### DNS Records you must know:
*   **A Record**: Maps a domain name directly to an IPv4 Address. (e.g., `example.com` -> `198.51.100.23`).
*   **CNAME Record**: Maps a domain name to *another* domain name. (e.g., `www.example.com` -> points to -> `example.com`).
*   **DNS Propagation**: When you change a record, it can take anywhere from 5 minutes to 24 hours for the new phonebook entry to update across the globe.

---

## PART 9: Production HTTPS Setup

Right now, your site is HTTP. We need HTTPS (Secure).

**Setup Flow:**
```text
Domain (example.com) ---> Nginx ---> Let's Encrypt SSL Certificate
```

**Let's Encrypt & Certbot:**
Let's Encrypt is a free, automated Certificate Authority. 
**Certbot** is a tool you install on your server. It talks to Let's Encrypt, proves you own the domain, downloads the cryptographic SSL certificates, and actually edits your `nginx.conf` automatically to enable Port 443 (HTTPS)!

Certbot also sets up a background cron job to renew the certificates automatically every 90 days, so you never have to think about it again.

---

## PART 10: Using CI/CD for Deployment

In Day 5, we created a GitHub Action to test and build images. Now, let's achieve **Continuous Deployment**.

Instead of you logging in to run `git pull` and `docker compose up`, we automate it.

**The Automated Pipeline:**
```text
Developer pushes code 
        |
GitHub Actions runs tests 
        |
Builds Docker Image & Pushes to Docker Hub
        |
(NEW!) GitHub Actions uses an SSH Key to log into your Cloud Server
        |
(NEW!) Server runs `./deploy.sh` (Pulls new image, restarts Docker Compose)
```

With this in place, pushing to the `main` branch automatically updates the live website within minutes. You have achieved senior-level deployment automation.

---

## PART 11: Server Security Basics

A cloud server is constantly under attack by automated bots guessing passwords. You must secure it.

**Crucial Practices:**
1.  **Never expose DB ports publicly**: In `docker-compose.yml`, your PostgreSQL should NEVER have `ports: - "5432:5432"`. Let it communicate only on the internal Docker network.
2.  **Use SSH Keys**: Disable password login entirely. Only allow logins via cryptographic SSH keys.
3.  **Firewall Rules (UFW)**: Block all ports except 22 (SSH), 80 (HTTP), and 443 (HTTPS).
4.  **Keep packages updated**: Run `apt-get update && apt-get upgrade` regularly to patch OS vulnerabilities.

**Common Beginner Mistake**: Binding Docker ports to `0.0.0.0` carelessly. If you do `ports: - "6379:6379"` for Redis, the whole internet can access your cache!

---

## PART 12: Monitoring and Logs

Once deployed, you need to know if the server is surviving the traffic.

### Docker Monitoring
*   `docker stats`: Shows a live dashboard of CPU and RAM usage for every running container. (Crucial for seeing if your ML model is eating all the RAM).
*   `docker logs <container>`: View the application output. 

### Server Monitoring (Linux commands)
*   `htop` or `top`: Shows overall Server CPU and Memory usage.
*   `df -h`: Shows Disk space usage. (Servers crash when the hard drive fills up with un-rotated logs!)

**Why monitoring matters**: You can't fix a bottleneck if you don't know it exists. If `docker stats` shows your Flask container at 100% CPU, you know it's time to scale up!

---

## PART 13: Cloud Deployment Debugging

When production goes down, stay calm and check the layers.

**Problem 1: Website not loading at all (Timeout)**
*   *Check DNS*: Is the A Record pointing to the correct IP?
*   *Check Firewall*: Did you open Port 80 and 443 on the cloud provider's dashboard?
*   *Check Nginx*: Is the Nginx container running? (`docker compose ps`).

**Problem 2: 502 Bad Gateway**
*   *Check Backend*: Nginx is alive, but the backend is dead. Run `docker compose logs backend` to see why it crashed.
*   *Check Port Mapping*: Is Nginx proxying to the right internal port?

**Problem 3: Database connection error**
*   *Check Env Vars*: Did you misspell the password in the server's `.env` file?
*   *Check DB Container*: Did the database container crash due to lack of RAM? (`docker stats`).

---

## PART 14: Production Improvements

As systems scale to millions of users, we move beyond a single VPS:

*   **Managed Databases (RDS)**: Instead of running Postgres in Docker, you pay AWS to host Postgres for you. They handle backups, scaling, and redundancy.
*   **Object Storage (S3)**: Don't store user uploads (images, CSVs) on the VPS hard drive. Save them to cheap, infinite cloud storage like Amazon S3.
*   **CDN (Content Delivery Network)**: Cache your static frontend assets (JS/CSS) on servers around the globe so they load instantly for everyone.
*   **Load Balancers**: A cloud service that sits in front of *multiple* VPS servers and distributes traffic across all of them.
*   **Infrastructure as Code (Terraform)**: Writing code that automatically creates servers, networks, and databases on AWS, so you don't have to click buttons in a dashboard.

---

## PART 15: Hands-On Challenge

It is time to prove your skills.

1.  **Rent a Server**: Get a cheap $5-$6 VPS on DigitalOcean, Linode, or AWS Lightsail.
2.  **Provision it**: SSH in, install Docker and Git.
3.  **Deploy**: Clone your Day 4/5 project, configure the `.env`, and run `docker compose up -d`.
4.  **Connect a Domain**: Buy a cheap domain name (or use a free one), point the A Record to your server's IP.
5.  **Secure it**: Install Certbot and get a green padlock (HTTPS) on your domain.
6.  *(Bonus)*: Try to trigger an automatic deployment by pushing code to GitHub!

---

## Final Output

### 1. Complete Day 6 Summary
Today you conquered the Cloud. You learned how to provision a Virtual Private Server, SSH into it, and manually deploy a complex Docker-based architecture. You mastered DNS records to map a domain to an IP, secured traffic with HTTPS/Certbot, and connected your CI/CD pipeline to achieve continuous deployment. You are now officially a Cloud Engineer.

### 2. Cloud Deployment Checklist
1. [ ] Server created & SSH keys secured.
2. [ ] Firewall allows only 22, 80, 443.
3. [ ] Docker & Git installed.
4. [ ] Code cloned & `.env` securely created.
5. [ ] `docker compose up -d` successful.
6. [ ] DNS A Record points to Public IP.
7. [ ] Certbot SSL applied to Nginx.

### 3. Important Linux Server Commands
*   `ssh user@ip`: Connect to server.
*   `htop`: Monitor CPU/RAM.
*   `df -h`: Check disk space.
*   `ufw status`: Check firewall rules (Ubuntu).
*   `nano filename`: Edit files in the terminal.

### 4. Docker Deployment Interview Questions
*   *"If your Dockerized application is running slow in the cloud, how do you diagnose if it's a CPU, RAM, or Database issue?"* -> Run `htop` for host metrics, `docker stats` for container metrics, and check `docker logs` for application bottlenecks or DB timeouts.
*   *"Why is it a bad idea to run a production database inside a Docker container on a single VPS?"* -> Because if the VPS hardware fails, you lose all data. In enterprise production, we prefer Managed Databases (like AWS RDS) for automatic backups, replication, and high availability.
*   *"How does Nginx know how to route traffic to your Docker container?"* -> It uses the container's service name provided by Docker's internal DNS network via `proxy_pass http://backend:5000`.

### 5. How this applies to your career:
*   **Deploying ML Models:** Data Scientists train models, but MLOps Engineers deploy them. You now know how to put a heavy PyTorch model into a container, rent a high-RAM/GPU cloud server, and deploy it securely behind Nginx for the world to query.
*   **FastAPI Inference Servers:** You can spin up a dedicated server just for model inference, allowing it to scale independently from your main web backend.
*   **RAG Applications:** Retrieval-Augmented Generation apps need vector databases (like Milvus or Qdrant), a backend API, and a frontend. You now know exactly how to orchestrate that multi-container beast in the cloud.
*   **Data Science Projects:** Want to share a complex Streamlit or Dash dashboard? Don't send a link to your local machine. Containerize it and deploy it to a $5 VPS!

Congratulations! You have completed the 6-Day Docker & Backend Infrastructure Masterclass. You are ready to tackle real-world engineering challenges.
