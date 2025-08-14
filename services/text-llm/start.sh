#!/bin/bash
# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

MODEL="${MODEL:-Qwen/Qwen3-14B-AWQ}"

# Stop and remove any existing container named qwen-omni
docker stop text-llm 
docker rm text-llm 

# Run the new container
docker run \
  --name text-llm \
  --gpus all \
  -p 127.0.0.1:7002:80 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -v ~/.cache/vllm:/root/.cache/vllm \
  vllm/vllm-openai:v0.10.0 \
  --model "$MODEL" \
  --port 80 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 1024 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
