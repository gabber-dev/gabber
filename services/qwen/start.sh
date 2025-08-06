#!/bin/bash
# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0


# Stop and remove any existing container named qwen
docker stop qwen
docker rm qwen

# Run the new container
docker run \
  --name qwen \
  --gpus all \
  -p 127.0.0.1:7002:80 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:v0.8.5.post1 \
  --model Qwen/Qwen2.5-VL-3B-Instruct \
  --port 80 \
  --gpu-memory-utilization 0.95 \
  --max-model-len 4096 \
  --enforce-eager \
  --limit-mm-per-prompt image=10
