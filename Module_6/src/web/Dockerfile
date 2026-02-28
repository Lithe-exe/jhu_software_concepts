FROM python:3.11-slim
WORKDIR /app
COPY src/web/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY . .
EXPOSE 8080
USER 1000
CMD ["python", "src/web/run.py"]
