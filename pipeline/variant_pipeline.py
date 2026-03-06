"""
GenoCloud — Variant Calling Pipeline
Orchestrates: FastQC → BWA-MEM2 → GATK → SnpEff → Claude AI
"""

import boto3
import subprocess
import logging
import argparse
from pathlib import Path
from ai_interpreter import AIVariantInterpreter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VariantPipeline:
    def __init__(self, sample_id: str, s3_bucket: str = None, local_mode: bool = True):
        self.sample_id = sample_id
        self.local_mode = local_mode
        self.s3_bucket = s3_bucket
        self.work_dir = Path(f"/tmp/{sample_id}")
        self.work_dir.mkdir(exist_ok=True)

        if not local_mode:
            self.s3 = boto3.client('s3')
            import boto3
            self.dynamo = boto3.resource('dynamodb').Table('GenoCloud-Variants')

    def quality_control(self, fastq: Path) -> bool:
        """Run FastQC quality control"""
        logger.info(f"Running FastQC on {fastq}")
        result = subprocess.run(
            ["fastqc", str(fastq), "--outdir", str(self.work_dir)],
            capture_output=True
        )
        return result.returncode == 0

    def align_reads(self, fastq: Path) -> Path:
        """Align reads to hg38 using BWA-MEM2"""
        logger.info("Aligning reads with BWA-MEM2...")
        bam_out = self.work_dir / f"{self.sample_id}.bam"
        subprocess.run([
            "bwa-mem2", "mem", "-t", "16",
            "/ref/hg38.fa", str(fastq),
            "|", "samtools", "sort", "-o", str(bam_out)
        ], check=True, shell=False)
        subprocess.run(["samtools", "index", str(bam_out)], check=True)
        logger.info(f"Alignment complete: {bam_out}")
        return bam_out

    def call_variants(self, bam: Path) -> Path:
        """Call variants using GATK HaplotypeCaller"""
        logger.info("Calling variants with GATK HaplotypeCaller...")
        vcf_out = self.work_dir / f"{self.sample_id}.vcf.gz"
        subprocess.run([
            "gatk", "HaplotypeCaller",
            "-R", "/ref/hg38.fa",
            "-I", str(bam),
            "-O", str(vcf_out),
            "--native-pair-hmm-threads", "16"
        ], check=True)
        logger.info(f"Variant calling complete: {vcf_out}")
        return vcf_out

    def annotate_variants(self, vcf: Path) -> Path:
        """Annotate variants with SnpEff"""
        logger.info("Annotating variants with SnpEff...")
        annotated_vcf = self.work_dir / f"{self.sample_id}.annotated.vcf"
        subprocess.run([
            "java", "-jar", "snpEff.jar",
            "hg38", str(vcf)
        ], stdout=open(annotated_vcf, 'w'), check=True)
        return annotated_vcf

    def ai_interpret(self, vcf: Path) -> dict:
        """Use Claude AI to interpret HIGH-impact variants"""
        logger.info("Running AI interpretation with Claude...")
        interpreter = AIVariantInterpreter()
        return interpreter.interpret_vcf(vcf)

    def store_results(self, vcf: Path, ai_results: dict):
        """Store results to S3 + DynamoDB or locally"""
        if self.local_mode:
            results_dir = Path("results")
            results_dir.mkdir(exist_ok=True)
            import json
            with open(results_dir / f"{self.sample_id}_ai_results.json", 'w') as f:
                json.dump(ai_results, f, indent=2)
            logger.info(f"Results saved locally to results/{self.sample_id}_ai_results.json")
        else:
            self.s3.upload_file(str(vcf), self.s3_bucket, f"results/{self.sample_id}.vcf.gz")
            self.dynamo.put_item(Item={
                'sample_id': self.sample_id,
                'status': 'COMPLETE',
                'vcf_s3_key': f"results/{self.sample_id}.vcf.gz",
                'ai_interpretations': str(ai_results)
            })

    def run(self, input_fastq: str):
        """Run full pipeline end to end"""
        fastq = Path(input_fastq)
        logger.info(f"Starting GenoCloud pipeline for sample: {self.sample_id}")

        self.quality_control(fastq)
        bam = self.align_reads(fastq)
        vcf = self.call_variants(bam)
        annotated = self.annotate_variants(vcf)
        ai_results = self.ai_interpret(annotated)
        self.store_results(annotated, ai_results)

        logger.info(f"✅ Pipeline complete for {self.sample_id}")
        return ai_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='GenoCloud Variant Pipeline')
    parser.add_argument('--sample', required=True, help='Sample ID')
    parser.add_argument('--input', required=True, help='Input FASTQ file')
    parser.add_argument('--s3-bucket', help='S3 bucket (optional)')
    parser.add_argument('--local', action='store_true', default=True, help='Run in local mode')
    args = parser.parse_args()

    pipeline = VariantPipeline(
        sample_id=args.sample,
        s3_bucket=args.s3_bucket,
        local_mode=args.local
    )
    pipeline.run(args.input)
