.PHONY: setup generate train-demo train challenge train-all run tests

setup:
	pip install -r requirements.txt

generate:
	python -m src.data.generate_synthetic_cases

train-demo:
	python -m src.models.train_baseline
	python -m src.models.train_lgbm

# Backward-compatible alias
train: train-demo

challenge:
	python -m src.models.train_challenger

train-all: train-demo challenge

run:
	uvicorn src.api.main:app --reload

tests:
	pytest -q