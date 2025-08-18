.PHONY: engine editor repository frontend all generate add-license livekit kitten-tts

GABBER_REPOSITORY_DIR ?= $(shell pwd)/.gabber
GABBER_SECRET_FILE ?= $(shell pwd)/.secret

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

generate:
	engine/.venv/bin/python engine/src/main.py generate-editor-schema | json2ts -o frontend/generated/editor.ts
	engine/.venv/bin/python engine/src/main.py generate-repository-schema | json2ts -o frontend/generated/repository.ts
	engine/.venv/bin/python engine/src/main.py generate-state-machine-schema | json2ts -o frontend/generated/stateMachine.ts

	engine/.venv/bin/python engine/src/main.py generate-runtime-schema | json2ts -o sdks/javascript/src/generated/runtime.ts
	engine/.venv/bin/python engine/src/main.py generate-runtime-schema | json2ts -o sdks/react/src/generated/runtime.ts

frontend:
	cd frontend && \
	npm install && \
	npm run dev

add-license:
	addlicense -c "Fluently AI, Inc. DBA Gabber. All rights reserved." -l "SUL-1.0" -s -ignore frontend/node_modules -ignore frontend/.next -ignore engine/.venv engine frontend services
	addlicense -c "Fluently AI, Inc. DBA Gabber. All rights reserved." -l "Apache-2.0" -s -ignore **/node_modules sdks examples

livekit:
	LIVEKIT_LOG_LEVEL=INFO livekit-server --dev --bind=0.0.0.0

kitten-tts:
	cd services/kitten-tts && ./start.sh

all:
	make engine 2>&1 | while IFS= read -r line; do printf "\033[0;34m[ENGINE]\033[0m %s\n" "$$line"; done & ENGINE_PID=$$!; \
	make editor 2>&1 | while IFS= read -r line; do printf "\033[0;32m[EDITOR]\033[0m %s\n" "$$line"; done & EDITOR_PID=$$!; \
	make repository 2>&1 | while IFS= read -r line; do printf "\033[0;35m[REPOSITORY]\033[0m %s\n" "$$line"; done & REPOSITORY_PID=$$!; \
	make frontend 2>&1 | while IFS= read -r line; do printf "\033[0;36m[FRONTEND]\033[0m %s\n" "$$line"; done & FRONTEND_PID=$$!; \
	make livekit 2>&1 | while IFS= read -r line; do printf "\033[0;37m[LIVEKIT]\033[0m %s\n" "$$line"; done & LIVEKIT_PID=$$!; \
	make kitten-tts 2>&1 | while IFS= read -r line; do printf "\033[0;33m[KITTEN-TTS]\033[0m %s\n" "$$line"; done & KITTEN_TTS_PID=$$!; \
	trap 'echo "Stopping all processes..."; kill 0' INT;\
	wait