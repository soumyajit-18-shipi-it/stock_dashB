# Stage 1: Build Frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Build Backend
FROM python:3.11-slim AS backend-builder
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 3: Final Production Image
FROM python:3.11-slim
WORKDIR /app

# Copy backend dependencies from builder
COPY --from=backend-builder /install /usr/local

# Copy frontend build from builder
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Copy backend code
COPY backend/ ./backend/
COPY backend/models/ ./models/
COPY run.py ./

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend

# Expose the local default port. Hosted platforms can inject PORT at runtime.
EXPOSE 8000

CMD ["python", "run.py"]
