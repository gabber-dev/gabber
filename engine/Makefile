.PHONY: engine editor repository

install: 
	uv sync && \
	uv sync --group dev

engine:
	make install && \
	.venv/bin/python src/main.py engine 

repository:
	make install && \
	.venv/bin/watchfiles ".venv/bin/python src/main.py repository" src

editor:
	make install && \
	.venv/bin/watchfiles ".venv/bin/python src/main.py editor" src

lint:
	make install && \
	.venv/bin/python -m ruff check .

format:
	make install && \
	.venv/bin/python -m ruff format .