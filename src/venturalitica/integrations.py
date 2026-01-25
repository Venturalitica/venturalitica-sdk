import sys
import os
import uuid
from typing import Dict, List, Optional
from .core import ComplianceResult

def _get_upsell_link(control_id: str, metric_key: str) -> str:
    """Generates a link to the Venturalítica SaaS for triage."""
    base_url = os.getenv("VENTURALITICA_SAAS_URL", "http://www.venturalitica.ai")
    return f"{base_url}/projects/governance/triage?control={control_id}&metric={metric_key}"

def generate_report(results: List[ComplianceResult]) -> str:
    """Generates a markdown compliance report."""
    report = "# Governance Compliance Report\n\n"
    for res in results:
        status_icon = "✅" if res.passed else "❌"
        status_text = "PASSED" if res.passed else "FAILED"
        
        report += f"### {status_icon} Control {res.control_id}: {res.description}\n"
        report += f"- **Metric**: `{res.metric_key}`\n"
        report += f"- **Threshold**: `{res.actual_value:.4f} {res.operator} {res.threshold}`\n"
        report += f"- **Status**: {status_text}\n"
        
        if not res.passed:
            report += f"- **Action**: [Fix this in Venturalítica SaaS]({_get_upsell_link(res.control_id, res.metric_key)})\n"
        
        report += "\n"
    return report

def _log_mlflow(results: List[ComplianceResult], report_text: str):
    """Integrates with MLflow."""
    try:
        import mlflow
        if not mlflow.active_run():
            return
            
        metrics = {f"governance.{res.control_id}.score": (1.0 if res.passed else 0.0) for res in results}
        mlflow.log_metrics(metrics)
        
        tags = {f"governance.{res.control_id}": ("PASS" if res.passed else "FAIL") for res in results}
        tags["governance.overall"] = "PASS" if all(r.passed for r in results) else "FAIL"
        mlflow.set_tags(tags)
        
        mlflow.log_text(report_text, "governance_report.md")
        print("✓ [Venturalítica] Compliance results logged to MLflow")
    except (ImportError, Exception):
        pass

def _log_wandb(results: List[ComplianceResult], report_text: str):
    """Integrates with Weights & Biases."""
    try:
        import wandb
        if not wandb.run:
            return
            
        metrics = {f"governance.{res.control_id}.score": (1.0 if res.passed else 0.0) for res in results}
        wandb.log(metrics)
        
        for res in results:
            wandb.run.summary[f"governance.{res.control_id}"] = "PASS" if res.passed else "FAIL"
        wandb.run.summary["governance.overall"] = "PASS" if all(r.passed for r in results) else "FAIL"

        artifact_name = f"gov-report-{wandb.run.id}"
        temp_path = f"gov_{uuid.uuid4().hex}.md"
        with open(temp_path, "w") as f:
            f.write(report_text)
        
        artifact = wandb.Artifact(name=artifact_name, type="governance_report")
        artifact.add_file(temp_path, name="governance_report.md")
        wandb.log_artifact(artifact)
        
        try: os.remove(temp_path)
        except: pass
        
        print("✓ [Venturalítica] Compliance results logged to WandB")
    except (ImportError, Exception):
        pass

def _log_clearml(results: List[ComplianceResult], report_text: str):
    """Integrates with ClearML."""
    try:
        from clearml import Task
        task = Task.current_task()
        if not task:
            return
            
        logger = task.get_logger()
        current_tags = list(task.get_tags() or [])
        gov_tags = [f"governance.{res.control_id}:{'PASS' if res.passed else 'FAIL'}" for res in results]
        overall_status = "PASS" if all(r.passed for r in results) else "FAIL"
        gov_tags.append(f"governance.overall:{overall_status}")
        
        task.set_tags(current_tags + gov_tags)
        
        for res in results:
            logger.report_text(f"Governance: {res.control_id} = {'PASS' if res.passed else 'FAIL'}", iteration=1)
            
        logger.report_text(f"Governance Report:\n{report_text}", iteration=1)
        print("✓ [Venturalítica] Compliance results logged to ClearML")
    except (ImportError, Exception):
        pass

def auto_log(results: List[ComplianceResult]):
    """Orchestrates logging to all detected MLOps frameworks."""
    if not results:
        return
        
    report_text = generate_report(results)
    _log_mlflow(results, report_text)
    _log_wandb(results, report_text)
    _log_clearml(results, report_text)
