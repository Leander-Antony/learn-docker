# Learn Docker Journey

Welcome to the Docker learning repository! This project tracks a step-by-step curriculum to master Docker, starting from the basics and moving to advanced multi-container orchestration.

## Curriculum

* **[Day 1](Day_1.md)**: Introduction to Docker basics. Covers images, containers, Dockerfiles, building (`docker build`), running (`docker run`), ports, and volumes.
* **[Day 2](Day_2.md)**: Masterclass on Docker Compose. Covers orchestrating multi-container applications, networking, and includes a hands-on project with two Flask microservices (`docker-compose-flask-project`).
* **[Day 3](Day_3.md)**: Production-Ready Docker. Covers full backend systems with PostgreSQL databases, Redis caching, persistent volumes, environment variables, and container health checks (`task-management-api`).
* **[Day 4](Day_4.md)**: Nginx & Production Networking. Teaches how real production traffic flows, utilizing Nginx as a reverse proxy, hiding application containers, load balancing, and advanced Docker networking (`nginx-docker-production`).
* **[Day 5](Day_5.md)**: CI/CD with Docker. Teaches automation using GitHub Actions, including automated testing (pytest), Docker Hub integration, deployment scripts, and CI/CD best practices.
* **[Day 6](Day_6.md)**: Cloud Deployment with Docker. Covers provisioning VPS servers (IaaS), SSH, DNS configuration, HTTPS/SSL via Certbot, server security, and bridging CI/CD pipelines to live cloud servers.
* **[Day 7](Day_7.md)**: Kubernetes & Docker Swarm. Covers enterprise container orchestration, highly available clusters, Pods, Deployments, Services, auto-scaling, rolling updates, and MLOps integrations.

---

## Quick Reference Summary

This is a comprehensive guide to using Docker for building, deploying, and managing containerized applications. Here's a summary of the key points:

1. **Dockerfile**: A recipe for creating a single container from your application code.
2. **`docker build`**: Builds a container image based on the instructions in the `Dockerfile`.
3. **`docker run`**: Creates and starts a new container instance from an existing image.
4. **`docker-compose.yml`**: A file that defines multiple containers as services, which can be built, started, and stopped together using `docker compose`.

Key commands:

* `docker build`: Builds a container image from the `Dockerfile`.
* `docker run`: Runs a new container instance from an existing image.
* `docker-compose up`: Starts all defined services in the `docker-compose.yml` file.
* `docker-compose down`: Stops and removes all containers.

Useful Docker commands:

* `docker ps`: Lists running containers.
* `docker stop`: Stops one or more containers.
* `docker rm`: Removes one or more containers from the host system.

Tips for working with Docker on a Mac:

* Use the latest version of Docker Desktop for Mac (with Compose support).
* Make sure to use `docker compose` (with a space) instead of `docker-compose`.
* When rebuilding an image, use `docker compose up --build`.

Best practices:

* Keep your `Dockerfile` and `docker-compose.yml` files in the same directory as your application code.
* Use `docker-compose` for managing multiple containers that depend on each other (e.g., a web server and a database).
* Use `.env` files to store sensitive configuration data, like API keys or database credentials.

I hope this summary helps you get started with using Docker in your development workflow!