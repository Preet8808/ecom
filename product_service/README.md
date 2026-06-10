# E-Commerce Microservice CI/CD Pipeline

## Project Overview

This project demonstrates a complete DevOps workflow for a containerized e-commerce microservice application.

The application is built using Flask and is fully automated using GitHub Actions. Every semantic version tag triggers a CI/CD pipeline that runs tests, builds a Docker image, pushes the image to Docker Hub, and creates a GitHub Release.

---

## Features

* Flask-based REST API
* Dockerized application
* Automated CI/CD with GitHub Actions
* Semantic Versioning
* Docker Hub image publishing
* Automated GitHub Releases
* Unit testing with Pytest
* Test-gated deployments

---

## Technology Stack

* Python 3.12
* Flask
* Pytest
* Docker
* GitHub Actions
* Docker Hub

---

## Project Structure

```text
.
├── app.py
├── test_app.py
├── requirements.txt
├── Dockerfile
├── VERSION
├── README.md
└── .github
    └── workflows
        └── ci.yml
```

---

## API Endpoints

### Home

```http
GET /
```

Response:

```json
{
  "service": "ecommerce-microservice",
  "status": "running"
}
```

### Products

```http
GET /products
```

### Cart

```http
GET /cart
```

### Health Check

```http
GET /health
```

---

## Local Setup

### Clone Repository

```bash
git clone <repository-url>
cd ecommerce-microservice
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Application

```bash
python app.py
```

Application URL:

```text
http://localhost:5000

1. Trigger on semantic version tags
6. Push image to Docker Hub

```text
Push Tag
   ↓
   ↓
Push to Docker Hub
   ↓
Create GitHub Release

---

## Required GitHub Secrets
Configure the following repository secrets:

```text
DOCKER_USERNAME
DOCKER_TOKEN
```

---

## Example Release

```bash
git push origin v1.0.0
```

Generated Docker Images:

```text
dockerhub-user/ecommerce-service:v1.0.0
dockerhub-user/ecommerce-service:<commit-sha>
```

---

## Learning Outcomes

This project demonstrates:

* Containerization with Docker
* Automated CI/CD pipelines
* Version-controlled releases
* Test-driven deployment workflows
* Docker image management
* DevOps best practices

---

## Author

Built as a DevOps portfolio project demonstrating CI/CD automation, Dockerization, and release management.
git tag v1.0.0

```
Build Docker Image
   ↓
Run Tests
7. Generate release notes

Pipeline Flow:
8. Create GitHub Release

   * Semantic Version
   * Git Commit SHA
2. Install dependencies
3. Run unit tests
4. Build Docker image
5. Tag image with:
## CI/CD Workflow

The GitHub Actions pipeline performs the following steps:

---

```

git push origin v1.0.0
```
---
Create a release:

```bash
git tag v1.0.0
```


```text
1.0.0 Initial Release
1.0.1 Bug Fix
1.1.0 New Feature
2.0.0 Breaking Change

Examples:

Execute unit tests:

```bash
docker build -t ecommerce-service .
MAJOR.MINOR.PATCH
```
Version format:

```text
### Verify
```

---

## Semantic Versioning

curl http://localhost:5000/health

```bash

```
```
  -p 5000:5000 \
  ecommerce-service
docker run -d \
  --name ecommerce-app \
```bash
### Run Container


pytest -v
## Docker Usage
### Build Image




---
```
```bash

