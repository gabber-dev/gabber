#!/bin/bash
# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0


# Stop and remove any existing container named joy-caption
docker stop joy-caption
docker rm joy-caption

# Run the new container
docker run \
  --name joy-caption \
  --gpus all \
  -p 127.0.0.1:7002:80 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:v0.8.5.post1 \
  --model fancyfeast/llama-joycaption-beta-one-hf-llava \
  --port 80 \
  --gpu-memory-utilization 0.95 \
  --max-model-len 4096 \
  --enforce-eager \
  --limit-mm-per-prompt image=2
