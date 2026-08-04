FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Preserve the backend/ package layout so both `backend.server` (as used by
# the compression/artifacts routers and the test suite) and a flat run from
# /app resolve the same way.
COPY . ./backend
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000"]
