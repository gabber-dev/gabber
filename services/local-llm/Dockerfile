# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

FROM vllm/vllm-openai:nightly-e5e9067e61600eedd4e75bd1c512ec52872916aa

RUN pip install vllm[audio]
RUN apt-get update && apt-get install -y \
    libx264-dev \
    ffmpeg