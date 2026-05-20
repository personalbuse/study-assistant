import httpx
from app.config import settings


def trigger_n8n_workflow(data: dict) -> dict:
    url = f"{settings.n8n_webhook_url}/process-document"
    with httpx.Client(timeout=60) as client:
        response = client.post(url, json=data)
        response.raise_for_status()
        return response.json()
