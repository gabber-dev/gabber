#!/bin/bash
# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

BASEDIR="$(dirname "$(realpath "$0")")"

# Stop and remove any existing container named qwen-omni
docker stop local-llm
docker rm local-llm

docker build --tag local-llm:latest "$BASEDIR"

# Run the new container
docker run \
  --name local-llm \
  --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -v ~/.cache/vllm:/root/.cache/vllm \
  -v $(pwd):/root \
  --network host \
  local-llm:latest \
  --model "Qwen/Qwen2.5-VL-7B-Instruct-AWQ" \
  --port 7002 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 32000 \
  --limit-mm-per-prompt '{"image":8,"video":8,"audio":8}' \
  --enable-auto-tool-choice \
  --chat-template /root/qwen2.5-vl-chat-template-tools.jinja \
  --enforce-eager \
  --tool-call-parser hermes
