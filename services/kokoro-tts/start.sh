BASEDIR=$(dirname "$0")
echo "$BASEDIR"

docker stop kokoro-tts
docker rm kokoro-tts

docker build --tag kokoro-tts:latest "$BASEDIR"

docker run \
  --name kokoro-tts \
  --gpus all \
  -p 127.0.0.1:7002:80 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
    kokoro-tts:latest