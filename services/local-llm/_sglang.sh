#!/bin/bash
# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

BASEDIR="$(dirname "$(realpath "$0")")"
MODEL="${MODEL:-Qwen/Qwen2.5-Omni-7B-AWQ}"

# Stop and remove any existing container named qwen-omni
docker stop local-llm 
docker rm local-llm 

# Run the new container
docker run \
  --name local-llm \
  --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -v ~/.cache/vllm:/root/.cache/vllm \
  --network host \
  --shm-size=8gb \
  lmsysorg/sglang:v0.5.5.post1 \
  python3 -m sglang.launch_server --model-path "$MODEL" --port 7002 --host 0.0.0.0 --chunked-prefill-size 2048 --context-length 8000 --mem-fraction-static 0.7 --enable-multimodal --tool-call-parser qwen \
