.PHONY: setup check dev data-list data-plan data-sync profile
PORT ?= 8000

setup:
	uv sync --locked

check:
	uv run --locked ruff check .
	uv run --locked ruff format --check .
	uv run --locked pytest -q

dev:
	uv run --locked uvicorn factored_banking.api:app --host 127.0.0.1 --port $(PORT) --reload

data-list:
	./scripts/aws.sh s3 ls s3://factored-datathon-2026-s3-157725502942-us-east-2-an/data/

data-plan:
	./scripts/aws.sh s3 sync s3://factored-datathon-2026-s3-157725502942-us-east-2-an/data/ data/raw/ --dryrun --no-progress

data-sync:
	./scripts/aws.sh s3 sync s3://factored-datathon-2026-s3-157725502942-us-east-2-an/data/ data/raw/ --no-progress --only-show-errors

profile:
	uv run --locked python -m factored_banking.profile --data-dir data/raw --output artifacts/data-profile.json
