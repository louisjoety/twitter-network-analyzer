FROM node:24-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements/base.txt requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt \
    && useradd --create-home --uid 10001 app \
    && mkdir runtime && chown app:app runtime
COPY app.py ./
COPY backend/ backend/
COPY analysis/ analysis/
COPY tests/fixtures/users.csv tests/fixtures/users.csv
COPY --from=frontend /build/dist frontend/dist/
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)" || exit 1
ENTRYPOINT ["python", "app.py", "--host", "0.0.0.0"]
CMD ["--offline"]
