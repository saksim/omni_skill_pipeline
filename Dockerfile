FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OMNI_REPO_ROOT=/app

WORKDIR /app

COPY pyproject.toml README.md requirements-dev.txt ./
COPY src ./src
COPY apps ./apps
COPY docs/current/contracts ./docs/current/contracts

RUN python -m pip install --upgrade pip \
    && python -m pip install .[api] -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && mkdir -p /app/skills/drafts /app/skills/published

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
