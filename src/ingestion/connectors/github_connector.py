import httpx
from typing import Optional
from src.app.core.config import settings

API_BASE = "https://api.github.com"

async def get_latest_github_action_logs() -> Optional[str]:
    if not settings.GITHUB_TOKEN or not settings.GITHUB_REPO:
        print("GitHub settings (TOKEN, REPO) not configured, skipping log fetch.")
        return None

    headers = {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            runs_url = f"{API_BASE}/repos/{settings.GITHUB_REPO}/actions/runs?per_page=1&status=completed"
            resp_runs = await client.get(runs_url, headers=headers)
            resp_runs.raise_for_status()
            
            runs_data = resp_runs.json()
            if not runs_data.get("workflow_runs"):
                print("No completed GitHub workflow runs found.")
                return None
            
            latest_run_id = runs_data["workflow_runs"][0]["id"]
            
            jobs_url = f"{API_BASE}/repos/{settings.GITHUB_REPO}/actions/runs/{latest_run_id}/jobs"
            resp_jobs = await client.get(jobs_url, headers=headers)
            resp_jobs.raise_for_status()

            jobs_data = resp_jobs.json()
            if not jobs_data.get("jobs"):
                print(f"No jobs found for GitHub run {latest_run_id}.")
                return None
            
            first_job_id = jobs_data["jobs"][0]["id"]
            logs_url = f"{API_BASE}/repos/{settings.GITHUB_REPO}/actions/jobs/{first_job_id}/logs"
            
            resp_log_redirect = await client.get(logs_url, headers=headers, follow_redirects=False)
            
            if resp_log_redirect.status_code == 302:
                log_content_url = resp_log_redirect.headers['location']
                resp_logs = await client.get(log_content_url)
                resp_logs.raise_for_status()
                return resp_logs.text
            else:
                resp_logs = await client.get(logs_url, headers=headers)
                resp_logs.raise_for_status()
                return resp_logs.text

    except httpx.HTTPStatusError as e:
        print(f"Error fetching GitHub logs: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred fetching GitHub logs: {e}")
        return None