.PHONY: setup check dev data-list data-plan data-sync profile pipeline train-fraud evaluate docker
PORT ?= 8000

setup:
	uv sync --locked --group ml

check:
	uv run --locked --group ml ruff check .
	uv run --locked --group ml ruff format --check .
	uv run --locked --group ml pytest -q

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

pipeline:
	uv run --locked --group ml python -m factored_banking.data_pipeline --export-sqlite

train-fraud:
	uv run --locked --group ml python -m factored_banking.train_fraud

evaluate:
	uv run --locked --group ml python -m factored_banking.system_evaluation

docker:
	docker build -t claro-banking:local .
