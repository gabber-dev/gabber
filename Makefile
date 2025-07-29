.PHONY: engine editor repository frontend

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

generate-ts:
	engine/.venv/bin/python engine/src/main.py generate-editor-schema | json2ts -o frontend/generated/editor.ts && \
	engine/.venv/bin/python engine/src/main.py generate-repository-schema | json2ts -o frontend/generated/repository.ts

frontend:
	cd frontend && \
	npm install && \
	npm run dev

add-license:
	addlicense -c "Fluently AI, Inc. DBA Gabber. All rights reserved." -l "SUL-1.0" -s -ignore frontend/node_modules -ignore frontend/.next -ignore engine/.venv engine frontend services

livekit:
	livekit-server --dev

BLUE=\033[0;34m
GREEN=\033[0;32m
MAGENTA=\033[0;35m
WHITE=\033[1;37m
CYAN=\033[0;36m
NC=\033[0m

all:
	{ make engine 2>&1 | while IFS= read -r line; do echo "${BLUE}[ENGINE] $${line}${NC}"; done } & \
	{ make editor 2>&1 | while IFS= read -r line; do echo "${GREEN}[EDITOR] $${line}${NC}"; done } & \
	{ make repository 2>&1 | while IFS= read -r line; do echo "${WHITE}[REPOSITORY] $${line}${NC}"; done } & \
	{ make frontend 2>&1 | while IFS= read -r line; do echo "${MAGENTA}[FRONTEND] $${line}${NC}"; done } & \
	{ make livekit 2>&1 | while IFS= read -r line; do echo "${CYAN}[LIVEKIT] $${line}${NC}"; done } & \
	wait
