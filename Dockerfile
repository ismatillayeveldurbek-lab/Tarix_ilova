# ---- 1-bosqich: Mini App (React) ni yig'ish ----
FROM node:22-alpine AS webapp
WORKDIR /webapp
COPY webapp/package.json webapp/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY webapp/ ./
COPY backend/tests/translit_cases.json /backend/tests/translit_cases.json
RUN npm run build

# ---- 2-bosqich: Python server (bot + API + admin panel) ----
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=webapp /webapp/dist /app/webapp/dist

# Ishga tushganda: jadvallarni yangilash -> imtihon formatini yaratish -> ilovani ishga tushirish
CMD alembic upgrade head && python -m scripts.seed --faqat-format && python -m app.main
