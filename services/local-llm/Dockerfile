# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

FROM vllm/vllm-openai:v0.10.0

RUN pip install vllm[audio]
RUN apt-get update && apt-get install -y \
    libx264-dev \
    ffmpeg