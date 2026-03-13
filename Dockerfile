FROM python:3.11-slim

# Install CA certificates
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    update-ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# Set working directory
WORKDIR /app

# Set timezone to Vietnam
ENV TZ=Asia/Ho_Chi_Minh
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY api.py .
COPY main.py .
COPY test.py .
COPY sheduler.py .
COPY snapshot.py .
COPY service_account.json .
COPY tools ./tools
COPY send_email.py .

EXPOSE 8386 8387

# Run scheduler
CMD ["python", "-u", "sheduler.py"]