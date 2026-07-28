# Day 7: Kubernetes + Docker Swarm Basics

Welcome to Day 7! I am your Senior DevOps Mentor. Over the last six days, you've mastered containers, CI/CD, and cloud deployments. 

Today is the final frontier: **Container Orchestration**. 
When you deploy a single server in the cloud (Day 6), you have a single point of failure. If that server dies, your app dies. Today, you will learn how large tech companies run thousands of containers across hundreds of servers simultaneously, with zero downtime. 

Grab a coffee. We are diving into Docker Swarm and Kubernetes (K8s).

---

## PART 1: Why Container Orchestration?

### The Problem with Docker Compose
Up until now, you used Docker Compose. It is fantastic for 1 laptop or 1 small cloud server. You type `docker compose up` and 3 containers start.

But what happens when you have:
*   **100 containers** of your Flask API because of a massive traffic spike?
*   **10 different physical servers** (Nodes) because 1 server isn't powerful enough?
*   **A server failure**? (If Server 3 catches fire, how do its containers automatically move to Server 4?)
*   **Rollbacks**? (You deployed v2, it crashed, you need to instantly go back to v1 without users noticing).

Docker Compose cannot do this. It only understands ONE machine.

### The Solution: Orchestrators
An orchestrator is a "brain" that manages a fleet of servers. You don't tell a server "run this container". You tell the orchestrator, *"I want 5 copies of my Flask API running across our 10 servers at all times."* 
If a server dies, taking down 2 containers, the orchestrator instantly notices you only have 3 running, and starts 2 new ones on healthy servers.

### 🛑 Checkpoint 1
If you are deploying a blog for 100 users, should you use Kubernetes?
*(Answer: No! Docker Compose on a single VPS is perfect. Orchestration solves problems of massive scale and high availability. It adds immense complexity that small apps don't need.)*

---

## PART 2: Docker Swarm Introduction

Before we jump into the massive beast that is Kubernetes, we must learn **Docker Swarm**.

### What is Docker Swarm?
Docker Swarm is Docker's native clustering tool. It turns a pool of Docker hosts (multiple servers) into a single, virtual Docker host.

**Architecture:**
```text
                  [ Manager Node ]  <-- The Brain. Gives orders.
                   /            \
                  /              \
    [ Worker Node 1 ]          [ Worker Node 2 ]  <-- The Muscle. Runs containers.
      | | | Containers           | | | Containers
```

*   **Services**: In Swarm, you don't run containers. You run "Services" (e.g., "Run the Redis service").
*   **Tasks**: A single container running as part of a service.
*   **Replicas**: How many copies (tasks) of that service you want.

---

## PART 3: Docker Swarm Hands-On

Imagine you have two servers.

**On Server 1 (Manager):**
```bash
docker swarm init
```
*What happens:* Server 1 becomes the Swarm Manager. It generates a token that other servers can use to join.

**On Server 2 (Worker):**
```bash
docker swarm join --token <the-token-from-manager> <manager-ip>:2377
```
*What happens:* Server 2 connects to Server 1. They are now a cluster!

**Deploying a Service (Run this on the Manager):**
```bash
docker service create --name my-web --publish 8080:80 nginx
```
*What happens:* The manager tells a worker (or itself) to pull the `nginx` image and run it.

**Scaling the Service:**
```bash
docker service scale my-web=5
```
*What happens:* The manager looks at the cluster and spins up 4 more Nginx containers, spreading them evenly across Server 1 and Server 2!

**View Services:**
```bash
docker service ls
```

---

## PART 4: Swarm Deployment Project

Instead of running long `docker service` commands, Swarm can read your `docker-compose.yml`!

**`flask-swarm-project/docker-compose.yml`**
```yaml
version: '3.8'

services:
  backend:
    image: my-flask-app:latest
    deploy:
      replicas: 3 # Run 3 copies of this Flask app!
      update_config:
        parallelism: 1 # Update 1 container at a time (Rolling update)
        delay: 10s
    networks:
      - swarm-net

networks:
  swarm-net:
    driver: overlay # OVERLAY network spans ACROSS multiple servers!
```

To deploy this across a 5-server cluster, you just type:
```bash
docker stack deploy -c docker-compose.yml my_stack
```
*What happens:* An `overlay` network is created. This is a magical virtual network. A container on Server A can talk to a container on Server B as if they were on the same laptop.

---

## PART 5: Kubernetes Introduction

Swarm is easy, but the industry standard is **Kubernetes** (often abbreviated as **K8s**). Originally built by Google, it is the most powerful orchestrator in the world.

### The Kubernetes Cluster Architecture

```text
                  [ CONTROL PLANE (The Brain) ]
                    - API Server (Talks to you)
                    - Scheduler (Assigns pods to nodes)
                    - Controller (Ensures desired state matches actual state)
                    - etcd (The database storing the cluster state)
                               |
        -----------------------------------------------
        |                                             |
   [ WORKER NODE 1 ]                             [ WORKER NODE 2 ]
    - kubelet (Agent)                             - kubelet
    - kube-proxy (Networking)                     - kube-proxy
    - Container Runtime (Docker)                  - Container Runtime
        |                                             |
      [ Pod ] [ Pod ]                               [ Pod ]
```

When you type a command, you talk to the **API Server**. You say "I want 3 Flask containers". 
The **Scheduler** finds servers with enough free RAM/CPU.
The **kubelet** on those servers receives the order and starts Docker containers.
The **Controller** watches them. If one dies, it tells the Scheduler to make a new one.

---

## PART 6: Kubernetes Core Concepts

Kubernetes does NOT use containers directly. It wraps them in its own concepts.

**1. Pod**
A Pod is the smallest unit in K8s. It is a "wrapper" around a container (or sometimes multiple tightly-coupled containers). You don't scale containers; you scale Pods.

**2. Deployment**
You rarely create a Pod directly. You create a **Deployment**. A Deployment manages a **ReplicaSet**, which ensures a specific number of Pods are always running. If you want 5 Pods, the Deployment makes it happen.

**3. Service**
Pods are ephemeral. They die and get new IP addresses constantly. A **Service** provides a single, permanent IP address and DNS name that load-balances traffic across a set of shifting Pods.
*   *ClusterIP*: Internal only (default).
*   *NodePort*: Exposes a port on the physical server's IP.
*   *LoadBalancer*: Talks to AWS/GCP to create a real cloud load balancer.

**4. Namespace**
A virtual cluster inside your physical cluster. If you have a Data Science team and a Backend team sharing 100 servers, you put them in different namespaces so their apps don't collide.

---

## PART 7: Install Kubernetes Locally

You don't need 10 servers to learn K8s. We use **Minikube** (or Docker Desktop's built-in Kubernetes), which runs a complete 1-node cluster inside a virtual machine on your laptop.

*(Assuming you have minikube installed)*:
```bash
minikube start
```

Verify your cluster is alive:
```bash
kubectl get nodes
```
*(Returns `minikube   Ready   control-plane`)*

---

## PART 8: First Kubernetes Application

In Docker Compose, we used one YAML file. In K8s, we use many YAML files (manifests).

```text
kubernetes-flask/
│
├── deployment.yaml   # Defines our Flask Pods and Replicas
├── service.yaml      # Defines the static IP to reach the Pods
├── configmap.yaml    # Non-sensitive env vars (e.g., LOG_LEVEL)
├── secret.yaml       # Sensitive env vars (e.g., DB_PASSWORD)
```

---

## PART 9: Kubernetes YAML Deep Dive

Let's look at **`deployment.yaml`**:

```yaml
apiVersion: apps/v1      # The K8s API version
kind: Deployment         # What are we creating? A Deployment.
metadata:
  name: flask-api        # Name of the deployment
spec:
  replicas: 3            # We want 3 Pods running!
  selector:
    matchLabels:
      app: flask         # How the deployment knows which pods it owns
  template:              # The blueprint for the Pods
    metadata:
      labels:
        app: flask       # The label applied to the Pods
    spec:
      containers:        # The actual Docker container specs
      - name: flask-container
        image: my-flask-app:v1
        ports:
        - containerPort: 5000
```
**Explanation:** 
Everything in K8s is declarative. You are declaring the "Desired State". The cluster will read this YAML and work infinitely to make the actual state match this desired state.

---

## PART 10: Deploy Flask Application

You apply configurations using `kubectl` (Kube-Control).

```bash
kubectl apply -f deployment.yaml
```

**Check what happened:**
```bash
kubectl get pods
```
*(You will see 3 Pods in "ContainerCreating", then "Running").*

**Get deep details on a Pod:**
```bash
kubectl describe pod <pod-name>
```

**Read the logs:**
```bash
kubectl logs <pod-name>
```

---

## PART 11: Scaling Applications

**Manual Scaling:**
Sudden traffic spike? Just type:
```bash
kubectl scale deployment flask-api --replicas=10
```
Within seconds, 7 new Pods are created across your servers.

**Automatic Scaling (HPA):**
A **Horizontal Pod Autoscaler** monitors CPU. 
*Architecture:* Traffic increases -> CPU usage on existing Pods hits 80% -> HPA automatically updates the Deployment to 10 replicas -> Traffic drops -> CPU drops -> HPA kills 7 Pods to save money.

---

## PART 12: Updating Applications (Rolling Updates)

Never take your app down to update it.

If you change `image: my-flask-app:v1` to `v2` in your YAML and run `kubectl apply`, K8s performs a **Rolling Update**.
1. It creates 1 new `v2` Pod.
2. It waits for it to become healthy.
3. It kills 1 old `v1` Pod.
4. It repeats until all Pods are `v2`. 
**Result:** Zero downtime.

**Check status:**
```bash
kubectl rollout status deployment/flask-api
```

**Oh no, v2 is crashing! Rollback instantly:**
```bash
kubectl rollout undo deployment/flask-api
```

---

## PART 13: Kubernetes Networking

**Docker Compose vs Kubernetes:**
In Compose, containers use their service name (e.g., `http://backend:5000`).
In K8s, Pods use the **Service** name. 

If you create a Service named `redis-svc`, your Flask app connects to `http://redis-svc:6379`. K8s CoreDNS intercepts this, translates it to the Service's static IP, and the Service load-balances the request to one of the healthy Redis Pods.

---

## PART 14: Storage in Kubernetes

Pods die. If a Postgres Pod dies, its data dies.

*   **Persistent Volume (PV)**: A piece of actual hard drive on AWS (like an EBS volume).
*   **Persistent Volume Claim (PVC)**: A "ticket" your Pod submits saying "I need 10GB of storage".

```text
Postgres Pod  --->  PVC (The Claim)  --->  PV (The actual 10GB Disk)
```
If the Postgres Pod dies and restarts on a different server, K8s unplugs the PV from Server A and plugs it into Server B, so no data is lost!

---

## PART 15: Kubernetes Secrets and Configurations

Never hardcode variables.

**ConfigMap:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  ENVIRONMENT: "production"
```

**Secret:** (Values must be Base64 encoded)
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-passwords
type: Opaque
data:
  password: c3VwZXJzZWNyZXQ= # "supersecret" in base64
```
You then inject these into your Deployment YAML as environment variables. K8s handles decrypting them securely inside the Pod.

---

## PART 16: Kubernetes Debugging

Debugging K8s is a primary skill for DevOps.

**1. Pod stuck in `Pending`**
*   *Cause:* The Scheduler cannot find a server with enough CPU/RAM to fit your Pod. 
*   *Check:* `kubectl describe pod <name>` (Look at the "Events" section at the bottom).

**2. Pod status is `CrashLoopBackOff`**
*   *Cause:* Your Flask app crashed immediately (e.g., Syntax error, DB connection failed). K8s keeps trying to restart it, but it keeps crashing.
*   *Check:* `kubectl logs <name>`.

**3. Pod status is `ImagePullBackOff`**
*   *Cause:* K8s cannot download your Docker image. You misspelled the tag, or you forgot to give K8s the password to your private Docker Registry.

---

## PART 17: Docker Swarm vs Kubernetes

| Feature | Docker Swarm | Kubernetes (K8s) |
| :--- | :--- | :--- |
| **Learning Curve** | Very Easy (1 day) | Very Steep (Months) |
| **Setup** | Built into Docker | Complex (Use EKS/GKE in cloud) |
| **Features** | Basic orchestration | Auto-scaling, RBAC, infinite customization |
| **Industry Adoption**| Low (Small teams) | Massive (The absolute standard) |

**When to choose:** Use Swarm if you have a small team, a tight deadline, and 3-5 servers. Use K8s if you are building an enterprise platform, a microservice architecture, or heavy Machine Learning pipelines.

---

## PART 18: Kubernetes + MLOps Connection

Why do Data Scientists and MLOps Engineers care about Kubernetes?

1.  **GPU Scheduling**: K8s allows you to say, "This specific Pod needs 2 NVIDIA A100 GPUs." K8s finds a server with GPUs and assigns the Pod there.
2.  **Model Serving at Scale**: If you have a FastAPI inference server running an LLM, a single request might take 2 seconds and max out a GPU. If 100 users hit it, K8s auto-scales your deployment to 100 Pods (if you have the hardware!) to serve them all in parallel.
3.  **A/B Testing Models**: You can run `v1` of your recommendation model and `v2` simultaneously, using K8s networking to send 10% of traffic to `v2` to see if it performs better.

---

## FINAL HANDS-ON PROJECT

Your capstone project:
Create a folder `k8s-production/`. Write the YAML files to deploy:
1. A Redis Deployment (1 replica) + Redis Service.
2. A PostgreSQL StatefulSet + PVC + Secret for passwords + Postgres Service.
3. A Flask API Deployment (3 replicas) + ConfigMap + API Service (Type: LoadBalancer).
*Apply them to Minikube, check the pods, and test the scaling!*

---

## Final Output

### 1. Complete Day 7 Summary
Today you crossed into Enterprise Infrastructure. You learned that orchestrators manage fleets of servers, ensuring high availability, zero-downtime rolling updates, and self-healing systems. You understand the K8s control plane, Pods, Deployments, Services, and how to debug them using `kubectl`.

### 2. Docker Swarm vs Kubernetes Cheat Sheet
*   **Swarm**: `docker service create`, Manager/Worker, Overlay networks, Stack deployments.
*   **K8s**: `kubectl apply -f`, Control Plane/Node, Pods/Deployments/Services, Heavy YAML configuration.

### 3. Important `kubectl` Commands
*   `kubectl apply -f file.yaml` (Create/Update resources)
*   `kubectl get pods` (List pods)
*   `kubectl describe pod <name>` (Detailed diagnostics)
*   `kubectl logs <name>` (Read application stdout)
*   `kubectl scale deployment <name> --replicas=5` (Scale manually)

### 4. Kubernetes Interview Questions
*   *"What is the difference between a Pod and a Container?"* -> A Pod is a K8s abstraction that encapsulates one or more tightly coupled containers that share the same network namespace (IP) and storage volumes.
*   *"How does a Deployment differ from a ReplicaSet?"* -> A ReplicaSet ensures N pods are running. A Deployment is a higher-level abstraction that manages ReplicaSets, enabling features like zero-downtime rolling updates and rollbacks.
*   *"What causes a CrashLoopBackOff?"* -> The application process inside the container is failing and exiting (e.g., missing env vars, syntax error). The kubelet restarts it, but it immediately fails again in a loop.

### 5. Full DevOps Learning Roadmap After This
1.  **Infrastructure as Code (IaC)**: Learn **Terraform** to provision AWS/GCP resources using code.
2.  **Helm**: Learn Helm to package complex Kubernetes YAML files into reusable templates.
3.  **Monitoring**: Learn **Prometheus** & **Grafana** to visualize metrics from your K8s cluster.
4.  **Service Meshes**: Learn **Istio** for advanced microservice security and traffic routing.

### 6. How these skills connect to your career:
*   **Backend Engineering**: You are no longer just writing Python. You understand exactly how your code runs in production, how it scales, and how it connects to databases securely. You are a complete backend engineer.
*   **Cloud Engineering**: You understand the underlying compute architecture (IaaS) and how orchestrated clusters utilize it.
*   **MLOps / Data Science Deployment**: You can take a Jupyter Notebook, extract the logic into a FastAPI app, containerize it (Day 1), set up CI/CD (Day 5), and deploy it to a GPU-enabled Kubernetes cluster (Day 7) that scales to millions of users. 

You have completed the entire 7-Day Journey. You now possess a highly lucrative, immensely powerful skillset. Congratulations, and happy building!
