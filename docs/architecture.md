# GenoCloud — Architecture Documentation

## Overview

GenoCloud is a cloud-native genomic variant analysis platform. It processes raw sequencing data through a multi-step bioinformatics pipeline, orchestrated by Kubernetes, with AI-powered clinical interpretation via Claude API.

## System Components

### 1. Pipeline Workers (Kubernetes Jobs)
Each tool runs as an independent K8s Job:
- **FastQC** — Quality control on raw reads
- **BWA-MEM2** — Alignment to hg38 reference genome
- **GATK HaplotypeCaller** — Variant calling (runs in parallel across 24 chromosomes)
- **SnpEff** — Variant annotation with functional impact prediction

### 2. AI Interpretation Service (Kubernetes Deployment)
- 3 replicas for high availability
- Calls Claude API for each HIGH-impact variant
- Returns structured JSON with clinical summary, diseases, and actionability
- Stores results in DynamoDB

### 3. FastAPI Backend (Kubernetes Deployment)
- Handles file uploads to S3
- Submits K8s Jobs programmatically
- Serves variant results to the dashboard

### 4. Dashboard (Static Site)
- Hosted on S3 + CloudFront (or GitHub Pages for demo)
- Connects to FastAPI backend via API Gateway
- Shows real-time K8s pod status, variant tables, and AI interpretations

## AWS Infrastructure

```
User → CloudFront → S3 (Dashboard)
              ↓
         API Gateway
              ↓
         ECS Fargate (FastAPI)
              ↓
    ┌─────────────────────────┐
    │     EKS Cluster         │
    │  ┌──────────────────┐   │
    │  │  Pipeline Jobs   │   │
    │  │  AI Service      │   │
    │  └──────────────────┘   │
    └─────────────────────────┘
              ↓
    S3 (Results) + DynamoDB
```

## Local Development

Run the full stack locally using minikube:

```bash
# Start local K8s cluster
minikube start --memory=8192 --cpus=4

# Apply all manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/

# Port forward the API
kubectl port-forward svc/genocloudd-api 8000:8000 -n bioinformatics

# Open dashboard
open index.html
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Claude API key | Yes |
| `S3_BUCKET` | AWS S3 bucket name | Cloud only |
| `AWS_REGION` | AWS region | Cloud only |
| `DYNAMO_TABLE` | DynamoDB table name | Cloud only |
