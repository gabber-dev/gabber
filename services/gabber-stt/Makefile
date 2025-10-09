.PHONY: server test-client install 

download-weights:
	curl -L -o weights/smart-turn-v3.0.onnx https://huggingface.co/pipecat-ai/smart-turn-v3/resolve/main/smart-turn-v3.0.onnx?download=true
	curl -L 

install: 
	uv sync && \
	uv sync --group dev

server:
	make install && \
	.venv/bin/watchfiles ".venv/bin/python -u src/main.py" src 

test-client:
	make install && \
	.venv/bin/watchfiles ".venv/bin/python -u src/test_client.py" src 

all:
	make server 2>&1 | while IFS= read -r line; do printf "\033[0;34m[SERVER]\033[0m %s\n" "$$line"; done & SERVER_PID=$$!; \
	make test-client 2>&1 | while IFS= read -r line; do printf "\033[0;32m[TEST_CLIENT]\033[0m %s\n" "$$line"; done & CLIENT_PID=$$!; \
	trap 'echo "Stopping all processes..."; kill 0' INT;\
	wait