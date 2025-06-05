.PHONY: install test run clean lint format help run-offline test-connection

# Development setup
install:
	export PATH="$$HOME/.local/bin:$$PATH" && uv sync --dev

# Testing
test:
	export PATH="$HOME/.local/bin:$PATH" && uv run pytest tests/ -v --asyncio-mode=auto

# Test MCP server functionality
test-server:
	export PATH="$HOME/.local/bin:$PATH" && \
	OFFLINE_MODE=true DEMO_MODE=true \
	uv run python test_server.py

# Code quality
lint:
	export PATH="$$HOME/.local/bin:$$PATH" && uv run mypy src/
	export PATH="$$HOME/.local/bin:$$PATH" && uv run ruff check src/

format:
	export PATH="$$HOME/.local/bin:$$PATH" && uv run black src/ tests/
	export PATH="$$HOME/.local/bin:$$PATH" && uv run isort src/ tests/

# Running
run:
	export PATH="$$HOME/.local/bin:$$PATH" && uv run python -m homey_mcp

# Offline development mode
run-offline:
	export PATH="$$HOME/.local/bin:$$PATH" && \
	OFFLINE_MODE=true DEMO_MODE=true LOG_LEVEL=DEBUG \
	uv run python -m homey_mcp

# Test Homey connection
test-connection:
	@echo "Testing Homey connection..."
	@export PATH="$$HOME/.local/bin:$$PATH" && \
	if [ -f .env ]; then \
		source .env && curl -s -H "Authorization: Bearer $$HOMEY_LOCAL_TOKEN" \
		"http://$$HOMEY_LOCAL_ADDRESS/api/manager/system" | head -100; \
	else \
		echo "❌ No .env file found"; \
	fi

run-dev:
	export PATH="$$HOME/.local/bin:$$PATH" && \
	HOMEY_LOCAL_ADDRESS=192.168.1.100 \
	HOMEY_LOCAL_TOKEN=your-token \
	LOG_LEVEL=DEBUG \
	uv run python -m homey_mcp

# MCP Inspector voor testing
inspector:
	npx @modelcontextprotocol/inspector \
		--server "uv" \
		--server-args "run" "python" "-m" "homey_mcp"

# Cleanup
clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -delete

# Help
help:
	@echo "Available commands:"
	@echo "  install         - Install dependencies"
	@echo "  test           - Run tests"
	@echo "  lint           - Run linting"
	@echo "  format         - Format code"
	@echo "  run            - Run MCP server (uses .env)"
	@echo "  run-offline    - Run in offline/demo mode"
	@echo "  test-connection- Test connection to Homey"
	@echo "  run-dev        - Run with debug logging"
	@echo "  inspector      - Open MCP Inspector"
	@echo "  clean          - Clean build artifacts"
