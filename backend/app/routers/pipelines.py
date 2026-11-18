import httpx
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings


router = APIRouter(
    prefix="/api/v1/pipelines",
    tags=["CI/CD Pipelines"],
)

GITHUB_API_BASE = "https://api.github.com"


@router.get("/runs")
async def pipeline_runs(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
):
    """读取配置仓库中的 GitHub Actions 运行记录。"""
    if not settings.GITHUB_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="GitHub Token is not configured on the backend",
        )

    repository = settings.GITHUB_REPOSITORY.strip()
    if not repository or "/" not in repository:
        raise HTTPException(
            status_code=500,
            detail="GITHUB_REPOSITORY must use owner/repository format",
        )

    url = f"{GITHUB_API_BASE}/repos/{repository}/actions/runs"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                url,
                headers=headers,
                params={"per_page": per_page, "page": page},
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="GitHub API request timed out",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to GitHub API",
        ) from exc

    if response.status_code in (401, 403):
        raise HTTPException(
            status_code=502,
            detail=(
                "GitHub API authorization failed; check that the token is valid "
                "and has Actions read permission"
            ),
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=502,
            detail=(
                "GitHub repository was not found or the token cannot access it; "
                "check GITHUB_REPOSITORY and repository access"
            ),
        )

    if not response.is_success:
        raise HTTPException(
            status_code=502,
            detail=f"GitHub API returned HTTP {response.status_code}",
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="GitHub API returned an invalid response",
        ) from exc

    runs = []
    for item in payload.get("workflow_runs", []):
        actor = item.get("actor") or {}
        runs.append(
            {
                "id": item.get("id"),
                "name": item.get("name") or "未命名工作流",
                "run_number": item.get("run_number"),
                "display_title": item.get("display_title") or "",
                "event": item.get("event") or "",
                "status": item.get("status") or "",
                "conclusion": item.get("conclusion"),
                "branch": item.get("head_branch") or "",
                "head_sha": item.get("head_sha") or "",
                "html_url": item.get("html_url") or "",
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
                "run_started_at": item.get("run_started_at"),
                "actor": actor.get("login") or "",
            }
        )

    return {
        "repository": repository,
        "total_count": payload.get("total_count", 0),
        "page": page,
        "per_page": per_page,
        "runs": runs,
    }
