# alpine for a smaller image size
FROM python:3.12-alpine

ENV HOST=HOST
ENV DATABASE=DATABASE
ENV USER=USER
ENV PASSWORD=PASSWORD

WORKDIR /app

COPY requirements.txt .

# no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

COPY gunicorn_config.py .

COPY . .

EXPOSE 8500

# gunicorn config still confuses me. Same port ?
CMD ["gunicorn", "--config", "gunicorn_config.py", "app:server"]