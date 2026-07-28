# Day 5: CI/CD with Docker (Continuous Integration & Continuous Deployment)

Welcome to Day 5! Today, I am putting on my DevOps hat. You have learned how to containerize apps, write Compose files, and setup production networks. 

But as a developer, you shouldn't be manually running `docker build` or SSH-ing into servers to type `docker compose up` every time you change a line of code. That is slow, error-prone, and stressful.

Today, we are building a pipeline. You push code, and robots take over: they test it, package it into Docker, and deploy it to production. Let's build your first automated CI/CD pipeline.

---

## PART 1: Understanding CI/CD

### What is CI (Continuous Integration)?
CI is the practice of automatically integrating code changes from multiple developers into a single main branch. More importantly, it means **automatically testing** that code every time someone makes a change to ensure it didn't break anything.

### What is CD (Continuous Deployment/Delivery)?
CD is the automated process of taking that tested code, packaging it (into a Docker image), and safely deploying it to a server so users can access it.

**Without CI/CD:**
```text
Developer codes  -->  Manually runs tests locally  -->  Manually builds Docker image  -->  Logs into production server  -->  Manually pulls and restarts
```
*(This is how things break at 2 AM on a Friday).*

**With CI/CD:**
```text
Developer pushes code  -->  GitHub runs tests  -->  GitHub builds image  -->  GitHub deploys it
```

**Why automation matters:**
*   **Faster releases:** You can deploy 10 times a day without fear.
*   **Fewer human errors:** Robots don't forget to run tests or type the wrong command.
*   **Consistent deployments:** Every deployment happens exactly the same way.

---

## PART 2: Git Workflow for Teams

CI/CD pipelines usually rely on a strict Git workflow. 

```text
1. Developer creates branch `feature-login`
        |
2. Developer pushes code & opens a Pull Request (PR)
        |
3. Code Review & CI Pipeline runs tests on the PR.
        |
4. If tests pass, code is merged to `main`.
        |
5. The `main` CI/CD Pipeline triggers -> Builds Image -> Deploys to Production.
```
*   **`main` branch:** The holy grail. Code here must ALWAYS be ready for production.
*   **Tags/Releases:** We often trigger deployments only when we tag a release (e.g., `v1.2.0`).

### 🛑 Checkpoint 1
Should a CI/CD pipeline deploy code to production when a developer pushes to a `feature` branch?
*(Answer: No! Feature branches should only trigger tests (CI). Deployments (CD) should only happen from the `main` branch or specific release tags.)*

---

## PART 3: Create Project

We are going to use a modified version of yesterday's project. Create this structure:

```text
production-flask-app/
│
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/                  <-- NEW: We need tests for CI!
│       └── test_app.py
│
├── frontend/                   <-- (Keep Day 4's frontend)
│   └── Dockerfile
│
├── nginx/                      <-- (Keep Day 4's nginx config)
│   └── nginx.conf
│
├── docker-compose.yml          <-- (Keep Day 4's compose file)
│
├── deploy.sh                   <-- NEW: Our automated deployment script
│
├── .github/                    <-- NEW: The magic folder for GitHub Actions
│   └── workflows/
│       └── docker-ci.yml
│
└── README.md
```

---

## PART 4: Testing Before Deployment

You cannot have Continuous Integration without tests. If you automate deployment of broken code, you just automated taking your servers down.

Let's write a simple `pytest` for our Flask app. Inside `backend/tests/test_app.py`:

**`backend/tests/test_app.py`**
```python
import pytest
from app import app

@pytest.fixture
def client():
    # This creates a test client that can simulate HTTP requests to our Flask app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_message(client):
    """Test that the /api/message endpoint returns 200 OK and the correct message."""
    response = client.get('/api/message')
    
    # 1. Check status code
    assert response.status_code == 200
    
    # 2. Check the JSON payload
    data = response.get_json()
    assert "message" in data
    assert data["message"] == "Hello from backend in production!"
```
*(You will need to add `pytest==7.4.0` to your `backend/requirements.txt` for this to work).*

---

## PART 5: GitHub Actions Introduction

### What is GitHub Actions?
It is a CI/CD platform built directly into GitHub. It spins up temporary, isolated servers (called runners) in the cloud to execute scripts every time an event (like a `push`) happens in your repository.

### The Hierarchy:
1.  **Workflow**: The entire automated process (e.g., "Build and Deploy App").
2.  **Job**: A specific set of tasks (e.g., "Run Tests" or "Build Docker Image"). Jobs can run in parallel.
3.  **Step**: Individual commands inside a job (e.g., `pip install -r requirements.txt`).

**Why YAML?**
Just like Docker Compose, CI pipelines are defined in YAML because it is easy to read, declarative (defines *what* should happen), and lives right inside your code repository (Infrastructure as Code).

---

## PART 6: Create First CI Pipeline

Let's tell GitHub how to test and build our app. Create this file at `.github/workflows/docker-ci.yml`.

**`.github/workflows/docker-ci.yml`**
```yaml
# The name of the workflow as it will appear in the GitHub UI
name: Docker CI Pipeline

# 1. Trigger on: When should this run?
on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

# 2. Jobs: The actual work to be done
jobs:
  test-and-build:
    # We want this job to run on a fresh Ubuntu Linux server provided by GitHub
    runs-on: ubuntu-latest

    # 3. Steps: The sequential commands
    steps:
      # Step 1: Download our code onto the GitHub server
      - name: Checkout code
        uses: actions/checkout@v3

      # Step 2: Set up Python
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      # Step 3: Install dependencies
      - name: Install dependencies
        run: |
          cd backend
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      # Step 4: Run the tests! (If this fails, the pipeline stops immediately)
      - name: Run Pytest
        run: |
          cd backend
          pytest tests/

      # Step 5: Build the Docker Image
      - name: Build Docker Image
        run: |
          cd backend
          docker build -t my-flask-app:latest .
```

### Explaining the keywords:
*   `on:` The event that triggers the workflow. Here, a push to `main` or a PR against `main`.
*   `uses:` Tells GitHub to use a pre-written community script (an "Action"). `actions/checkout@v3` is a script that runs `git clone` for you.
*   `run:` Executes a standard bash terminal command on the runner.

---

## PART 7: Docker Image Automation

Previously, you built images on your laptop (`docker build -t app .`). Now, GitHub is doing it on their servers. 

But building it on GitHub's server isn't enough. When the pipeline finishes, that temporary GitHub server is destroyed! We need to save our Docker image somewhere permanent so our production server can download it.

### Docker Image Tags
Versioning is critical in CI/CD.
*   `app:latest`: The most recent build. (Dangerous in production, because "latest" constantly changes).
*   `app:v1.0.0`: Semantic versioning (Safe).
*   `app:7a44144`: Using the Git Commit ID (Very safe and traceable).

---

## PART 8: Docker Hub Integration

### What is a Docker Registry?
It's like GitHub, but for Docker images. Docker Hub is the most popular public registry. AWS has ECR, Google has GCR.

**Architecture Flow:**
```text
GitHub Actions  --->  Builds Docker Image  --->  Pushes to Docker Hub  --->  Production Server Pulls from Docker Hub
```

Let's modify our workflow to push the image to Docker Hub. 

*(Note: To make this work in real life, you must go to your GitHub Repo Settings -> Secrets, and add `DOCKER_USERNAME` and `DOCKER_PASSWORD`).*

Update the bottom of your **`.github/workflows/docker-ci.yml`**:
```yaml
      # Step 5: Log in to Docker Hub securely using Secrets
      - name: Log in to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      # Step 6: Build AND Push to Docker Hub
      - name: Build and Push Docker Image
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          push: true
          # We tag it with the commit hash for perfect traceability
          tags: ${{ secrets.DOCKER_USERNAME }}/my-flask-app:${{ github.sha }}
```

**Security Rule:** Never, ever type your password directly into the YAML file. Anyone who can read your code can steal your account. Always use `${{ secrets.NAME }}`.

---

## PART 9: Deployment Pipeline

We have Continuous Integration (Tests pass) and Continuous Delivery (Image is pushed to Docker Hub). Now for **Continuous Deployment**.

**Full Pipeline Flow:**
```text
Code Push ↓
Run Tests ↓
Build Docker Image ↓
Push Image to Docker Hub ↓
SSH into Production Server ↓
Server Pulls New Image ↓
Server Restarts Docker Compose
```

---

## PART 10: Add Deployment Simulation

To tell our production server to update, we usually run a deployment script. Create `deploy.sh` in your root folder.

**`deploy.sh`**
```bash
#!/bin/bash
set -e # Stop script if any command fails

echo "Starting Deployment..."

# 1. Ensure we have the latest docker-compose.yml
git pull origin main

# 2. Pull the newest images from Docker Hub
docker compose pull

# 3. Restart the containers with the new images in the background
# The --remove-orphans flag cleans up old unused containers
docker compose up -d --remove-orphans

echo "Deployment Successful! 🚀"
```

In a real pipeline, your final GitHub Action step would use an SSH Action to log into your DigitalOcean/AWS server and execute `./deploy.sh`. 

---

## PART 11: CI/CD Debugging

When pipelines fail, developers panic. Here is how DevOps engineers debug:

**1. Pipeline fails during tests**
*   *Debug:* Open the GitHub Actions tab. Click on the failed job. Expand the "Run Pytest" step. Read the Python traceback. Your code is broken, fix it locally and push again.

**2. Docker build fails**
*   *Causes:* Missing dependency in `requirements.txt`, incorrect file path in the `COPY` command inside your Dockerfile, or a typo in the `context: ./backend` path in your YAML.

**3. Docker push fails**
*   *Causes:* Your GitHub Secrets are empty, misspelled, or your Docker Hub token expired. Check permissions.

**4. Deployment succeeds but app fails**
*   *Causes:* The worst scenario. The pipeline says "Green/Success", but the website is down. 
    *   Did you forget to add a new environment variable to the production `.env` file?
    *   Did you change a port in `app.py` but not update `docker-compose.yml`?
    *   Did a database migration fail?

---

## PART 12: Production CI/CD Improvements

As you grow to a senior level, companies implement advanced pipeline features:

*   **Docker Image Scanning**: A pipeline step that scans your Docker image for known security vulnerabilities (CVEs) before pushing it.
*   **Rollbacks**: If step 4 (Deployment) fails health checks, the pipeline automatically runs `docker run` on the *previous* image tag to restore service instantly.
*   **Blue-Green Deployment**: You spin up a completely identical second environment (Green). You deploy the new Docker image there. You test it. If it works, Nginx swaps traffic to Green instantly. Zero downtime.
*   **Canary Deployment**: You deploy the new Docker container, but configure Nginx to only send 5% of your users to it. If they don't get errors, you slowly increase it to 100%.

---

## PART 13: Hands-On Challenge

Your challenge is to build a mock CI/CD pipeline locally.

1.  Initialize a Git repository in your folder (`git init`).
2.  Commit the code and push it to a private GitHub repository.
3.  Go to the "Actions" tab in your GitHub repo and watch your pipeline run!
4.  *Deliberately break the test* in `test_app.py` (e.g., `assert response.status_code == 404`). Push the code. Watch the pipeline glow red and block the Docker Build step. Fix it, push again, and watch it turn green.

---

## Final Output

### 1. Complete Day 5 Summary
You have mastered the bridge between Development and Operations. You learned that CI/CD is about building trust in your code through automated testing (`pytest`), building immutable artifacts (Docker Images), versioning them (`github.sha`), and automating the deployment lifecycle (`deploy.sh`) so developers can focus purely on writing features.

### 2. Important GitHub Actions Concepts
*   **Workflow YAML**: The instruction manual for the robots.
*   **Runners**: The temporary cloud servers executing your code.
*   **Secrets**: Encrypted variables to safely pass passwords to your pipeline.
*   **Contexts (`${{ github.sha }}`)**: Dynamic variables injected by GitHub, like the current commit ID.

### 3. CI/CD Interview Questions
*   *"Why do we run tests before building the Docker image?"* -> Because building images takes time and resources. If the logic is broken, we want to fail fast and provide immediate feedback to the developer.
*   *"How do you handle sensitive database passwords in a CI/CD pipeline?"* -> Never hardcode them. Store them in the CI provider's Secret Manager (GitHub Secrets) and inject them as environment variables during the workflow run.
*   *"What is the difference between Continuous Delivery and Continuous Deployment?"* -> Delivery means the Docker image is built, pushed to a registry, and *ready* to be deployed by a human clicking a button. Deployment means it is automatically pushed all the way to the live production servers without human intervention.

### 4. Common DevOps Mistakes Beginners Make
*   **Using `latest` tags in production.** If you rollback, you don't know what `latest` was yesterday. Always tag with commit hashes or version numbers.
*   **Skipping tests to make the pipeline faster.** A fast pipeline that deploys broken code is worse than a slow pipeline.

### 5. How this connects to the real world
*   **Machine Learning Model Deployment:** Data scientists push new model weights to Git. A pipeline runs tests to ensure model accuracy hasn't dropped. If tests pass, it builds a Docker image containing the new model and deploys it to AWS. (This is the core of **MLOps**!).
*   **FastAPI APIs:** Because FastAPI is heavily typed, pipelines often include a step to run `mypy` (type checking) alongside `pytest` before building the Docker container.
*   **Data Science Projects:** Instead of emailing Jupyter notebooks, teams use Docker and CI/CD to ensure that a data processing script runs identically on a massive cloud server as it did on the analyst's laptop.

You have made it through 5 days of intense infrastructure training. You are now equipped to containerize, orchestrate, proxy, and automate backend systems. Congratulations!
