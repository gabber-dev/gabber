.PHONY: engine editor repository frontend all generate add-license livekit kitten-tts

GABBER_REPOSITORY_DIR ?= $(shell pwd)/.gabber
GABBER_SECRET_FILE ?= $(shell pwd)/.secret
GABBER_MCP_CONFIG ?= $(shell pwd)/mcp.yaml

engine:
	export GABBER_REPOSITORY_DIR=$(GABBER_REPOSITORY_DIR) && \
	export GABBER_SECRET_FILE=$(GABBER_SECRET_FILE) && \
	cd engine && \
	make engine

editor:
	export GABBER_REPOSITORY_DIR=$(GABBER_REPOSITORY_DIR) && \
	export GABBER_SECRET_FILE=$(GABBER_SECRET_FILE) && \
	cd engine && \
	make editor

repository:
	export GABBER_REPOSITORY_DIR=$(GABBER_REPOSITORY_DIR) && \
	export GABBER_SECRET_FILE=$(GABBER_SECRET_FILE) && \
	cd engine && \
	make repository 

mcp-proxy-client:
	cd engine && \
	make mcp-proxy-client

generate:
	engine/.venv/bin/python engine/gabber/main.py generate-editor-schema | json2ts -o frontend/generated/editor.ts
	engine/.venv/bin/python engine/gabber/main.py generate-repository-schema | json2ts -o frontend/generated/repository.ts
	engine/.venv/bin/python engine/gabber/main.py generate-state-machine-schema | json2ts -o frontend/generated/stateMachine.ts

	engine/.venv/bin/python engine/gabber/main.py generate-runtime-schema | json2ts -o sdks/javascript/src/generated/runtime.ts
	make generate-python

generate-python:
	mkdir -p .gabber/.generate/python && \
	engine/.venv/bin/python engine/gabber/main.py generate-runtime-schema > .gabber/.generate/python/runtime.json && \
	cd .gabber/.generate/python && \
	uv venv && uv pip install datamodel-code-generator && \
	uv run datamodel-codegen --input runtime.json --input-file-type jsonschema --output runtime.py --use-standard-collections --output-model pydantic_v2.BaseModel --use-annotated  && \
	mkdir -p ../../../sdks/python/gabber/generated && \
	touch ../../../sdks/python/gabber/generated/__init__.py && \
	echo "from . import runtime" > ../../../sdks/python/gabber/generated/__init__.py && \
	echo "__all__ = ['runtime']" >> ../../../sdks/python/gabber/generated/__init__.py && \
	cp runtime.py ../../../sdks/python/gabber/generated/runtime.py

generate-csharp:
	mkdir -p .gabber/.generate/csharp && \
	engine/.venv/bin/python engine/gabber/main.py generate-runtime-schema > .gabber/.generate/csharp/runtime.json && \
	cd .gabber/.generate/csharp && \
	nswag jsonschema2csclient runtime.json -o Runtime.cs -c Gabber.Runtime -d

frontend:
	cd frontend && \
	npm install && \
	npm run dev

add-license:
	addlicense -c "Fluently AI, Inc. DBA Gabber. All rights reserved." -l "SUL-1.0" -s -ignore frontend/node_modules -ignore frontend/.next -ignore engine/.venv engine frontend services
	addlicense -c "Fluently AI, Inc. DBA Gabber. All rights reserved." -l "Apache-2.0" -s -ignore **/node_modules sdks examples

livekit:
	LIVEKIT_LOG_LEVEL=INFO livekit-server --dev --bind=0.0.0.0

# kitten-tts:
# 	cd services/kitten-tts && ./start.sh

# 	make kitten-tts 2>&1 | while IFS= read -r line; do printf "\033[0;33m[KITTEN-TTS]\033[0m %s\n" "$$line"; done & KITTEN_TTS_PID=$$!; \

all:
	make engine 2>&1 | while IFS= read -r line; do printf "\033[0;34m[ENGINE]\033[0m %s\n" "$$line"; done & ENGINE_PID=$$!; \
	make editor 2>&1 | while IFS= read -r line; do printf "\033[0;32m[EDITOR]\033[0m %s\n" "$$line"; done & EDITOR_PID=$$!; \
	make repository 2>&1 | while IFS= read -r line; do printf "\033[0;35m[REPOSITORY]\033[0m %s\n" "$$line"; done & REPOSITORY_PID=$$!; \
	make frontend 2>&1 | while IFS= read -r line; do printf "\033[0;36m[FRONTEND]\033[0m %s\n" "$$line"; done & FRONTEND_PID=$$!; \
	make livekit 2>&1 | while IFS= read -r line; do printf "\033[0;37m[LIVEKIT]\033[0m %s\n" "$$line"; done & LIVEKIT_PID=$$!; \
	trap 'echo "Stopping all processes..."; kill 0' INT;\
	wait
