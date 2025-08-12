#!/bin/bash
# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

BASEDIR=$(dirname "$0")
echo "$BASEDIR"

# Stop and remove any existing container named qwen-omni
docker stop qwen-omni
docker rm qwen-omni

docker build --tag qwen-omni:latest "$BASEDIR"

# Run the new container
docker run \
  --name qwen-omni \
  --gpus all \
  -p 127.0.0.1:7002:80 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -v ~/.cache/vllm:/root/.cache/vllm \
  qwen-omni:latest \
  --model Qwen/Qwen2.5-Omni-7B-AWQ  \
  --limit-mm-per-prompt '{"image":8,"video":8,"audio":8}' \
  --port 80 \
  --gpu-memory-utilization 0.95 \
  --max-model-len 32768 
#   --enforce-eager