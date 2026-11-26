# ---- 1-bosqich: Mini App (React) ni yig'ish ----
FROM node:22-alpine AS webapp
WORKDIR /webapp
COPY webapp/package.json webapp/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY webapp/ ./
RUN npm run build

# ---- 2-bosqich: Python server (bot + API + admin panel) ----
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY data/ /app/data/
COPY --from=webapp /webapp/dist /app/webapp/dist

# Ishga tushganda: jadvallar -> imtihon formati -> faktlar bazasi -> faktlardan test savollari -> ilova
CMD alembic upgrade head && python -m scripts.seed --faqat-format && python -m scripts.import_facts && python -m scripts.generate_questions && python -m app.main
