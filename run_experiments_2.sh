#!/bin/bash

DIRECTORIES="archives lunasvg_execpathlength_experiment_output lunasvg_memory_experiment_output lunasvg_codecoverage_experiment_output libxml2_codecoverage_experiment_output"
mkdir -p $DIRECTORIES
for dir in $DIRECTORIES; do
  rm -rf "$dir"/*
done

python3 evaluation/execution_feedback/run_experiment.py evaluation/execution_feedback/experiment_configurations/lunasvg_execpathlength.yaml --population-size 1000 --repetitions 10 --output-dir lunasvg_execpathlength_experiment_output/
python3 evaluation/execution_feedback/run_experiment.py evaluation/execution_feedback/experiment_configurations/lunasvg_memory.yaml --population-size 1000 --repetitions 10 --output-dir lunasvg_memory_experiment_output/
python3 evaluation/execution_feedback/run_experiment.py evaluation/execution_feedback/experiment_configurations/lunasvg_codecoverage.yaml --population-size 1000 --repetitions 10 --output-dir lunasvg_codecoverage_experiment_output/

python3 evaluation/execution_feedback/run_experiment.py evaluation/execution_feedback/experiment_configurations/libxml2_codecoverage.yaml --population-size 1000 --repetitions 10 --output-dir libxml2_codecoverage_experiment_output/

echo "now zipping"

for dir in $DIRECTORIES; do
    tar -czf "archives/$dir.tar.gz" "$dir"
done