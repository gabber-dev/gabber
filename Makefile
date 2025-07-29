.PHONY: engine editor repository generate-ts frontend add-license

engine:
	cd engine && make engine

editor:
	cd engine && make editor

repository:
	export GABBER_REPOSITORY_DIR=$(shell pwd)/.gabber && cd engine && make repository

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
