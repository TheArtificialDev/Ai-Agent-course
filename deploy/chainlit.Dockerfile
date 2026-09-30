FROM python:3.13-slim

ARG APP_DIR=chatbot_complete
ENV APP_DIR=${APP_DIR}
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY chatbot ./chatbot
COPY chatbot_complete ./chatbot_complete
COPY multi_agent_chatbot ./multi_agent_chatbot
COPY chroma ./chroma
COPY data ./data

RUN useradd --create-home --shell /bin/bash appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data
USER appuser
WORKDIR /app/${APP_DIR}

EXPOSE 10000
CMD ["sh", "-c", "chainlit run ${CHAINLIT_APP:-4_authentication.py} --host 0.0.0.0 --port ${PORT:-10000}"]
