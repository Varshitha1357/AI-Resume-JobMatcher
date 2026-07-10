FROM python:3.12-slim

# Hugging Face Spaces runs containers as this user
RUN useradd -m -u 1000 user

WORKDIR /app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

USER user
ENV HOME=/home/user \
    WARM_START=1 \
    FLASK_DEBUG=0

EXPOSE 7860

# Single worker (the embedding model lives in memory), threads for concurrency,
# generous timeout because a cold search can take ~1-2 minutes on free CPUs
CMD ["gunicorn", "--workers", "1", "--threads", "4", "--timeout", "300", "--bind", "0.0.0.0:7860", "app:app"]
