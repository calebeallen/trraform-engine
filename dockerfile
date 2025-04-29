FROM python:3.11-slim

# Install cron (and any build deps you need)
RUN apt-get update \
  && apt-get install -y --no-install-recommends cron \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install your Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy your pre-made cron file into the system cron.d directory
COPY cron /etc/cron.d/my-cron

# Give it the right permissions and register it
RUN chmod 0644 /etc/cron.d/my-cron \
  && crontab /etc/cron.d/my-cron

# Run cron in foreground so Docker keeps the container alive
CMD ["cron", "-f"]
