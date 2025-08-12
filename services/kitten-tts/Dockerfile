# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn pydantic https://github.com/KittenML/KittenTTS/releases/download/0.1/kittentts-0.1.0-py3-none-any.whl

COPY main.py /app/main.py

CMD ["python", "main.py"]