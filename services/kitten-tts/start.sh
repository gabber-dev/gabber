# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

BASEDIR=$(dirname "$0")
echo "$BASEDIR"

docker stop kitten-tts
docker rm kitten-tts

docker build --tag kitten-tts:latest "$BASEDIR"

docker run \
  --name kitten-tts \
  -p 127.0.0.1:7003:80 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
    kitten-tts:latest