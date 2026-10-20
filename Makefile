.PHONY: setup dev refresh test lint frontend-build

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
export PATH := $(HOME)/.local/bin:$(PATH)

setup:
	cd $(ROOT)/backend && uv sync --group dev
	cd $(ROOT)/frontend && npm install

dev:
	$(ROOT)/scripts/dev.sh

refresh:
	cd $(ROOT)/backend && uv run python -m garleb_desk.connectors.refresh

test:
	cd $(ROOT)/backend && uv run pytest -q
	cd $(ROOT)/frontend && npx tsc -b --pretty false

lint:
	cd $(ROOT)/frontend && npm run lint

frontend-build:
	cd $(ROOT)/frontend && npm run build
