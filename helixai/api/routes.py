"""
GenoCloud — FastAPI Backend
Handles file uploads, pipeline submission, and results retrieval
"""

from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3
import uuid
import os

app = FastAPI(
    title="GenoCloud API",
    description="Genomic Variant Analysis Platform",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ────────────────────────────────────────
class JobStatus(BaseModel):
    job_id: str
    sample_id: str
    status: str
    message: str = ""

# ── Routes ───────────────────────────────────────
@app.get("/")
async def root():
    return {"name": "GenoCloud API", "version": "2.0.0", "status": "running"}

@app.post("/upload", response_model=JobStatus)
async def upload_sample(file: UploadFile):
    """Accept FASTQ file, push to S3, trigger K8s Job"""
    if not file.filename.endswith(('.fastq', '.fastq.gz', '.bam')):
        raise HTTPException(400, "Only .fastq, .fastq.gz, .bam files accepted")

    sample_id = str(uuid.uuid4())[:8]
    s3_key = f"raw/{sample_id}_{file.filename}"

    # Upload to S3
    s3 = boto3.client('s3')
    s3.upload_fileobj(file.file, os.environ['S3_BUCKET'], s3_key)

    # Submit Kubernetes Job
    job_id = _submit_k8s_job(sample_id, s3_key)

    return JobStatus(
        job_id=job_id,
        sample_id=sample_id,
        status="QUEUED",
        message=f"Pipeline started for {file.filename}"
    )

@app.get("/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    """Check pipeline job status"""
    dynamo = boto3.resource('dynamodb').Table('GenoCloud-Jobs')
    result = dynamo.get_item(Key={'job_id': job_id})
    item = result.get('Item')
    if not item:
        raise HTTPException(404, f"Job {job_id} not found")
    return JobStatus(**item)

@app.get("/variants/{sample_id}")
async def get_variants(sample_id: str, impact: str = None):
    """Fetch variant results with optional impact filter"""
    dynamo = boto3.resource('dynamodb').Table('GenoCloud-Variants')
    result = dynamo.get_item(Key={'sample_id': sample_id})
    item = result.get('Item', {})
    if impact:
        item['variants'] = [v for v in item.get('variants', []) if v['impact'] == impact]
    return item

@app.get("/health")
async def health():
    return {"status": "healthy"}

# ── Helpers ──────────────────────────────────────
def _submit_k8s_job(sample_id: str, s3_key: str) -> str:
    """Submit a Kubernetes Job for the pipeline"""
    from kubernetes import client, config
    config.load_incluster_config()
    batch_v1 = client.BatchV1Api()

    job = client.V1Job(
        metadata=client.V1ObjectMeta(name=f"pipeline-{sample_id}"),
        spec=client.V1JobSpec(
            template=client.V1PodTemplateSpec(
                spec=client.V1PodSpec(
                    restart_policy="Never",
                    containers=[client.V1Container(
                        name="pipeline",
                        image="genocloudd/pipeline:latest",
                        env=[
                            client.V1EnvVar(name="SAMPLE_ID", value=sample_id),
                            client.V1EnvVar(name="S3_KEY", value=s3_key),
                        ]
                    )]
                )
            )
        )
    )
    batch_v1.create_namespaced_job("bioinformatics", job)
    return f"pipeline-{sample_id}"
