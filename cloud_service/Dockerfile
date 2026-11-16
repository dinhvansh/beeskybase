FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY cloud_service/requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir -r /app/requirements.lock && useradd --uid 10001 --create-home cloud && chown cloud:cloud /app
COPY --chown=cloud:cloud cloud_service /app/cloud_service
COPY --chown=cloud:cloud cloud-preview /app/cloud-preview
USER cloud
WORKDIR /app/cloud_service
EXPOSE 8000
CMD ["gunicorn","beesky_cloud.wsgi:application","--bind","0.0.0.0:8000","--workers","2","--threads","4","--timeout","30","--access-logfile","-"]
