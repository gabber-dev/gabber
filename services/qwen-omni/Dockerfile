FROM vllm/vllm-openai:v0.10.0

RUN pip install vllm[audio]
RUN apt-get update && apt-get install -y \
    libx264-dev \
    ffmpeg