import httpx
from typing import Optional
from src.app.core.config import settings

async def get_latest_jenkins_build_log() -> Optional[str]:
    if not settings.JENKINS_URL or not settings.JENKINS_USERNAME or not settings.JENKINS_TOKEN or not settings.JENKINS_JOB_NAME:
        print("Jenkins settings (URL, USERNAME, TOKEN, JOB_NAME) not fully configured, skipping log fetch.")
        return None

    auth = (settings.JENKINS_USERNAME, settings.JENKINS_TOKEN)
    
    try:
        async with httpx.AsyncClient() as client:
            job_url = f"{settings.JENKINS_URL}/job/{settings.JENKINS_JOB_NAME}/api/json"
            resp_job = await client.get(job_url, auth=auth)
            resp_job.raise_for_status()
            
            job_data = resp_job.json()
            latest_build_num = job_data.get("lastBuild", {}).get("number")
            
            if not latest_build_num:
                print(f"No builds found for Jenkins job {settings.JENKINS_JOB_NAME}.")
                return None
                
            log_url = f"{settings.JENKINS_URL}/job/{settings.JENKINS_JOB_NAME}/{latest_build_num}/consoleText"
            resp_log = await client.get(log_url, auth=auth)
            resp_log.raise_for_status()
            
            return resp_log.text

    except httpx.HTTPStatusError as e:
        print(f"Error fetching Jenkins logs: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred fetching Jenkins logs: {e}")
        return None