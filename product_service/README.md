# GitHub Actions Docker Release Pipeline

Automated CI/CD pipeline that:

- Builds a Docker image
- Tags image with Semantic Version
- Tags image with Git Commit SHA
- Pushes image to Docker Hub
- Creates GitHub Release
- Generates Release Notes

## Tech Stack

- GitHub Actions
- Docker
- Docker Hub
- Python Flask
- Semantic Versioning

## Setup

### Clone Repository

```bash
git clone https://github.com/username/github-actions-docker-release.git

cd github-actions-docker-release
```

### Configure Secrets

Add:

```text
DOCKER_USERNAME
DOCKER_TOKEN
```

in GitHub Repository Secrets.

### Build Locally

```bash
docker build -t flask-demo .
```

### Run Locally

```bash
docker run -p 5000:5000 flask-demo
```

## Release Process

Create a new version:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Pipeline automatically:

1. Builds Docker image
2. Tags image with version
3. Tags image with commit SHA
4. Pushes image to Docker Hub
5. Generates release notes
6. Creates GitHub Release

## Example Docker Images

```text
username/flask-demo:v1.0.0
username/flask-demo:3ab9f2c
```

## Project Outcome

A fully automated release pipeline where every Git tag becomes a deployable Docker release.
