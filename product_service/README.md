# Product Service - DevOps Release Automation

## Overview

This project demonstrates a complete DevOps CI/CD workflow using Flask, Docker, GitHub Actions, Semantic Versioning, and GitHub Releases.

## Features

- Flask Product Service API
- Dockerized Application
- Automated Testing
- GitHub Actions CI/CD
- Semantic Version Tagging
- Docker Hub Integration
- Automated GitHub Releases

## Tech Stack

- Python
- Flask
- Docker
- GitHub Actions
- Docker Hub

## API Endpoints

### Home

GET /

```json
{
  "message": "Product Service Running"
}
```

### Products

GET /products

```json
[
  {
    "id": 1,
    "name": "Laptop",
    "price": 50000
  }
]
```

## Run Container

docker run -p 5000:5000 product-service

## Semantic Versioning

Examples:

```text
v1.0.1
v1.1.0
```

```text
Git Tag
GitHub Actions
 ↓
Run Tests
 ↓
 ↓

DevOps Capstone Project## Author
```

Create GitHub Release
 ↓
Push Docker Image
Build Docker Image
 ↓
## Release Process

v2.0.0
v1.0.0
```
```bash

