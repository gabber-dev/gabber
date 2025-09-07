.PHONY: engine editor repository

install: 
	uv sync && \
	uv sync --group dev

engine:
	make install && \
	.venv/bin/python -u src/main.py engine 

repository:
	make install && \
	.venv/bin/watchfiles ".venv/bin/python -u src/main.py repository" src

editor:
	make install && \
	.venv/bin/watchfiles ".venv/bin/python -u src/main.py editor" src

mcp-proxy-client:
	make install && \
	.venv/bin/python -u src/main.py mcp-proxy-client 

lint:
	make install && \
	.venv/bin/python -m ruff check .

format:
	make install && \
	.venv/bin/python -m ruff format .