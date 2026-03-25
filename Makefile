.PHONY: setup generate train-demo train challenge train-all run tests release-cli release-upload release-download

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

release-cli:
	python -m src.models.model_release --print-cli

release-upload:
	python -m src.models.build_raw_runtime_bundle
	gh release upload v1.0-models models/logreg_raw_runtime_bundle.joblib --repo BeediGoua/Brokerflow_ai --clobber
	gh release upload v1.0-models models/logreg_raw_runtime_manifest.json --repo BeediGoua/Brokerflow_ai --clobber
	gh release upload v1.0-models models/best_threshold.txt --repo BeediGoua/Brokerflow_ai --clobber
	gh release upload v1.0-models models/model_coefficients.csv --repo BeediGoua/Brokerflow_ai --clobber

release-download:
	python -m src.models.model_release --download