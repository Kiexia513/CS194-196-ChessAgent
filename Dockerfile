FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Windows checkouts may produce CRLF + non-executable scripts; fix for Linux containers
RUN sed -i 's/\r$//' run.sh && chmod +x run.sh

# Cloud Run sets PORT; controller reads HOST/PORT via pydantic-settings
ENV HOST=0.0.0.0
ENV PORT=8010

EXPOSE 8010

CMD ["agentbeats", "run_ctrl"]
