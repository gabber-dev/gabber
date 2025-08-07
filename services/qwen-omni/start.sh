#!/bin/bash
# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0


# Stop and remove any existing container named qwen-omni
docker stop qwen-omni
docker rm qwen-omni

# Run the new container
docker run \
  --name qwen-omni \
  --gpus all \
  -p 127.0.0.1:7002:80 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:v0.10.0 \
  --model Qwen/Qwen2.5-Omni-7B-AWQ  \
  --port 80 \
  --gpu-memory-utilization 0.95 \
  --max-model-len 4096
#   --enforce-eager