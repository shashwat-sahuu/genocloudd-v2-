# 🧬 GenoCloud — Genomic Variant Analysis Platform

> An AI-powered, cloud-native bioinformatics pipeline that identifies genetic variants, interprets clinical significance using Claude AI, and orchestrates analysis jobs via Kubernetes.

![GenoCloud Dashboard](docs/preview.png)

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Visit%20Site-00d4ff?style=for-the-badge)](https://shashwat-sahuu.github.io/genocloudd-v2-)
[![Python](https://img.shields.io/badge/Python-3.10+-3572a5?style=for-the-badge&logo=python)](https://python.org)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Orchestrated-326ce5?style=for-the-badge&logo=kubernetes)](https://kubernetes.io)
[![Claude AI](https://img.shields.io/badge/Claude-AI%20Powered-a78bfa?style=for-the-badge)](https://anthropic.com)

---

## 🌟 Features

- **Variant Calling Pipeline** — BWA-MEM2 + GATK HaplotypeCaller on hg38 reference genome
- **AI Interpretation** — Claude API automatically generates plain-English clinical summaries for HIGH-impact variants
- **Kubernetes Orchestration** — Each pipeline step runs as an independent K8s Job with parallel chromosome processing
- **Interactive Dashboard** — Real-time variant visualization, pod status monitoring, and live AI Q&A
- **Cloud-Ready** — Designed for AWS (S3, Batch, DynamoDB) with local minikube support

---

## 🏗️ Architecture

```
FASTQ Input → S3/Local
     ↓
FastQC (K8s Job) → Quality Control
     ↓
BWA-MEM2 (K8s Job) → Read Alignment to hg38
     ↓
GATK HaplotypeCaller (K8s Job × 24 chromosomes in parallel)
     ↓
SnpEff (K8s Job) → Variant Annotation
     ↓
Claude AI (K8s Deployment) → Clinical Interpretation
     ↓
GenoCloud Dashboard → Interactive Results
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Pipeline | Python, GATK 4.4, BWA-MEM2, SnpEff |
| AI | Claude API (Anthropic) |
| Orchestration | Kubernetes, Docker |
| Backend | FastAPI, boto3 |
| Storage | AWS S3, DynamoDB (or SQLite locally) |
| Frontend | HTML, CSS, JavaScript |
| CI/CD | GitHub Actions |

---

## 🚀 Quick Start

### Run Locally
```bash
# Clone the repo
git clone https://github.com/shashwat-sahuu/genocloudd-v2-.git
cd genocloudd-v2-

# Install Python dependencies
pip install -r requirements.txt

# Set your Anthropic API key
export ANTHROPIC_API_KEY=your_key_here

# Run the pipeline on sample data
python pipeline/variant_pipeline.py --sample NA12878 --input data/sample.fastq.gz
```

### Run on Kubernetes (minikube)
```bash
# Start minikube
minikube start

# Deploy all services
kubectl apply -f k8s/

# Check pods
kubectl get pods -n bioinformatics
```

---

## 📁 Project Structure

```
genocloudd/
├── index.html              # Interactive dashboard (live demo)
├── pipeline/
│   ├── variant_pipeline.py # Main pipeline orchestrator
│   ├── ai_interpreter.py   # Claude AI integration
│   └── utils.py            # Helper functions
├── api/
│   ├── routes.py           # FastAPI endpoints
│   └── models.py           # Data models
├── k8s/
│   ├── pipeline-job.yaml   # GATK Kubernetes Job
│   ├── ai-deployment.yaml  # AI service deployment
│   └── namespace.yaml      # K8s namespace config
├── docs/
│   └── architecture.md     # Detailed architecture docs
├── requirements.txt        # Python dependencies
└── README.md
```

---

## 🧬 Sample Results

The pipeline was tested on the **NA12878** public dataset (1000 Genomes Project):

| Metric | Value |
|--------|-------|
| Total Variants | 12,847 |
| HIGH Impact | 342 |
| Ti/Tv Ratio | 2.14 ✅ |
| Mean Coverage | 34× |
| AI Interpretations | 342 variants |

---

## 🤖 AI Integration

Each HIGH-impact variant is automatically analyzed by Claude AI:

```python
from pipeline.ai_interpreter import AIVariantInterpreter

interpreter = AIVariantInterpreter()
result = interpreter.interpret(variant)
# Returns: clinical significance, associated diseases,
#          treatment options, confidence score
```

---

## ☁️ AWS Deployment

See [docs/architecture.md](docs/architecture.md) for full AWS deployment guide including:
- S3 bucket setup
- AWS Batch configuration
- DynamoDB schema
- EKS cluster setup

---

## 📄 License

MIT License — feel free to use this project as a reference.

---

## 👤 Author

**Shashwat Sahu**
- GitHub: [@shashwat-sahuu](https://github.com/shashwat-sahuu)
- Live Demo: [genocloudd.github.io](https://shashwat-sahuu.github.io/genocloudd-v2-)

---

⭐ If you found this useful, please give it a star!
