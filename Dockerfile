FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

ARG INSTALL_DEV=false

COPY pyproject.toml README.md ./
COPY requirements ./requirements
COPY businessos ./businessos
COPY config ./config
RUN if [ "$INSTALL_DEV" = "true" ]; then \
      pip install --no-cache-dir -r requirements/development.lock; \
    else \
      pip install --no-cache-dir -r requirements/production.lock; \
    fi

COPY manage.py ./
COPY templates ./templates
COPY static ./static

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
