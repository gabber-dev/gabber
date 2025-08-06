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