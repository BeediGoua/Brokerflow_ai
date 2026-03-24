.PHONY: setup train run tests generate

setup:
	pip install -r requirements.txt

generate:
	python -m src.data.generate_synthetic_cases

train:
	python -m src.models.train_baseline
	python -m src.models.train_lgbm

run:
	uvicorn src.api.main:app --reload

tests:
	pytest -q