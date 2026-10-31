# Site público do PRISMA (Railway ou qualquer serviço que rode Docker).
# Guia passo a passo: DEPLOY.md
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PRISMA_DADOS=/data \
    PRISMA_DEMO_PUBLICA=1 \
    PRISMA_PROXY_CONFIAVEL=*

WORKDIR /app
COPY backend/requirements-nuvem.txt backend/
RUN pip install --no-cache-dir -r backend/requirements-nuvem.txt
COPY . .
RUN mkdir -p /data

WORKDIR /app/backend
EXPOSE 8000
# a porta vem da variável PORT (o Railway define sozinho); sem ela, 8000
CMD ["python", "-X", "utf8", "-m", "adaptador.api"]
