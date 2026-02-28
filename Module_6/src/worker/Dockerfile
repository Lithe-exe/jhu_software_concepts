FROM python:3.11-slim
WORKDIR /app
COPY src/worker/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY . .
USER 1000
CMD ["python", "src/worker/consumer.py"]
