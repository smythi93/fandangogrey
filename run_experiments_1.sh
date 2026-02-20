#!/bin/bash

DIRECTORIES="archives graphviz_execpathlength_experiment_output graphviz_memory_experiment_output graphviz_codecoverage_experiment_output libxml2_execpathlength_experiment_output libxml2_memory_experiment_output"
mkdir -p $DIRECTORIES
for dir in $DIRECTORIES; do
  rm -rf "$dir"/*
done

python3 evaluation/execution_feedback/run_experiment.py evaluation/execution_feedback/experiment_configurations/graphviz_execpathlength.yaml --population-size 1000 --repetitions 10 --output-dir graphviz_execpathlength_experiment_output/
python3 evaluation/execution_feedback/run_experiment.py evaluation/execution_feedback/experiment_configurations/graphviz_memory.yaml --population-size 1000 --repetitions 10 --output-dir graphviz_memory_experiment_output/
python3 evaluation/execution_feedback/run_experiment.py evaluation/execution_feedback/experiment_configurations/graphviz_codecoverage.yaml --population-size 1000 --repetitions 10 --output-dir graphviz_codecoverage_experiment_output/

python3 evaluation/execution_feedback/run_experiment.py evaluation/execution_feedback/experiment_configurations/libxml2_execpathlength.yaml --population-size 1000 --repetitions 10 --output-dir libxml2_execpathlength_experiment_output/
python3 evaluation/execution_feedback/run_experiment.py evaluation/execution_feedback/experiment_configurations/libxml2_memory.yaml --population-size 1000 --repetitions 10 --output-dir libxml2_memory_experiment_output/

echo "now zipping"

for dir in $DIRECTORIES; do
    tar -czf "archives/$dir.tar.gz" "$dir"
done