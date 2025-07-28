.PHONY: engine editor repository 

engine:
	uv sync && \
	uv pip install -r dev-requirements.txt && \
	.venv/bin/watchfiles ".venv/bin/python src/main.py engine" src

editor:
	uv sync && \
	uv pip install -r dev-requirements.txt && \
	.venv/bin/watchfiles ".venv/bin/python src/main.py editor" src

repository:
	uv sync && \
	uv pip install -r dev-requirements.txt && \
	.venv/bin/watchfiles ".venv/bin/python src/main.py repository" src

generate-editor-schema:
	uv sync && \
	.venv/bin/python src/main.py generate-editor-schema

generate-repository-schema:
	uv sync && \
	.venv/bin/python src/main.py generate-repository-schema