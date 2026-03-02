FROM python:3.11-slim AS system-deps

WORKDIR /app

RUN set -eux; \
    if [ -f /etc/apt/sources.list ]; then \
      sed -i 's|http://deb.debian.org/debian|https://deb.debian.org/debian|g' /etc/apt/sources.list; \
      sed -i 's|http://security.debian.org/debian-security|https://security.debian.org/debian-security|g' /etc/apt/sources.list; \
    fi; \
    if [ -d /etc/apt/sources.list.d ]; then \
      find /etc/apt/sources.list.d -type f \( -name '*.list' -o -name '*.sources' \) -print0 \
        | xargs -0 -r sed -i \
          -e 's|http://deb.debian.org/debian|https://deb.debian.org/debian|g' \
          -e 's|http://security.debian.org/debian-security|https://security.debian.org/debian-security|g'; \
    fi; \
    apt-get update && apt-get install -y \
      gcc \
      g++ \
      libreoffice-writer \
      fonts-dejavu \
      fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

FROM system-deps AS app

WORKDIR /app

COPY requirements.txt .
COPY requirements-embeddings-local.txt .
ARG WITH_LOCAL_EMBEDDINGS=false
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "$WITH_LOCAL_EMBEDDINGS" = "true" ]; then pip install --no-cache-dir -r requirements-embeddings-local.txt; fi

COPY . .
RUN mkdir -p /app/uploads

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
