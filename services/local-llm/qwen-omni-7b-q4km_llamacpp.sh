#!/bin/bash

LLAMA_SERVER_PATH=${LLAMA_SERVER_PATH:-llama-server}

 $LLAMA_SERVER_PATH \
  --hf-repo unsloth/Qwen2.5-Omni-7B-GGUF \
  --hf-file Qwen2.5-Omni-7B-Q4_K_M.gguf \
  --mmproj-url 'https://huggingface.co/unsloth/Qwen2.5-Omni-7B-GGUF/resolve/main/mmproj-F16.gguf' \
  -cb \
  -np 4 \
  -c 16384 \
  --port 7002 \
  --host 0.0.0.0
