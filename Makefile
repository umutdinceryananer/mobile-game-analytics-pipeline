#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = mobile_game_analytics_pipeline
PYTHON_VERSION = 3.11
PYTHON_INTERPRETER = python

export DBT_PROFILES_DIR := $(CURDIR)/dbt

#################################################################################
# COMMANDS                                                                      #
#################################################################################


## Install Python dependencies
.PHONY: requirements
requirements:
	$(PYTHON_INTERPRETER) -m pip install -U pip
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

RAW_CSV = data/raw/cookie_cats.csv
FABRICATED_RAW_CSV = data/raw/fabricated/cookie_cats.csv

## Rebuild synthetic dataset (clean_data.csv, events.parquet)
.PHONY: data
data:
ifeq ($(wildcard $(RAW_CSV)),)
	@echo "WARNING: $(RAW_CSV) not found. Using fabricated data, so results will not match the README."
	$(PYTHON_INTERPRETER) scripts/make_fabricated_raw_data.py
	$(PYTHON_INTERPRETER) -m mobile_game_analytics_pipeline.dataset --raw-csv $(FABRICATED_RAW_CSV)
else
	$(PYTHON_INTERPRETER) -m mobile_game_analytics_pipeline.dataset
endif

## Generate feature and label tables for modeling
.PHONY: features
features:
	$(PYTHON_INTERPRETER) -m mobile_game_analytics_pipeline.features

## Generate analytics tables (funnel, ROI, retention)
.PHONY: analytics
analytics:
	$(PYTHON_INTERPRETER) -m mobile_game_analytics_pipeline.analytics

## Train churn model and persist artefacts
.PHONY: train
train:
	$(PYTHON_INTERPRETER) -m mobile_game_analytics_pipeline.modeling.train

## Produce churn predictions using latest model
.PHONY: predict
predict:
	$(PYTHON_INTERPRETER) -m mobile_game_analytics_pipeline.modeling.predict

## Install dbt packages
.PHONY: dbt-deps
dbt-deps:
	cd dbt && dbt deps

## Build dbt models and run their tests
.PHONY: dbt-build
dbt-build: dbt-deps
	cd dbt && dbt build

## Generate and serve the dbt documentation site
.PHONY: dbt-docs
dbt-docs: dbt-deps
	cd dbt && dbt docs generate && dbt docs serve

## Regenerate the Mermaid lineage diagram in README.md
.PHONY: dbt-lineage
dbt-lineage: dbt-deps
	cd dbt && dbt parse
	$(PYTHON_INTERPRETER) scripts/dbt_lineage_mermaid.py

## Run full pipeline (data -> features -> analytics -> train -> dbt build)
.PHONY: pipeline
pipeline: data features analytics train dbt-build

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = '\n'.join([line for line in sys.stdin]); \
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n([a-zA-Z_-]+):', lines); \
print('Available rules:\n'); \
print('\n'.join(['{:25}{}'.format(*reversed(match)) for match in matches]))
endef
export PRINT_HELP_PYSCRIPT

help:
	@$(PYTHON_INTERPRETER) -c "${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)
