.PHONY: lint format type-check security docstrings quality \
	start-redpanda stop-redpanda inference-sec inference-prices training-sec training-prices

# --- Code quality (shared root config in pyproject.toml, applied repo-wide) ---
lint:
	uv run ruff check .
format:
	uv run ruff format .
	uv run ruff check . --fix
type-check:
	uv run mypy .
docstrings:
	uv run pydoclint .
security:
	uv run bandit -c pyproject.toml -r . --severity-level high
quality: format lint docstrings
	@echo "Quality checks complete."


#Running docker containers for redpanda cluster
start-redpanda:
	docker-compose -f redpanda.yml up -d
stop-redpanda:
	docker-compose -f redpanda.yml down


inference-sec:
	docker-compose -f docker-compose/system-inference/services-inference.yml \
	--profile sec up
inference-prices:
	docker-compose -f docker-compose/system-inference/services-inference.yml \
	--profile prices up

training-sec:
	docker-compose -f docker-compose/system-training/services-training.yml \
	--profile sec up
training-prices:
	docker-compose -f docker-compose/system-training/services-training.yml \
	--profile prices up
