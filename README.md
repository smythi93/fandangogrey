# Combining Input Constraints with Execution Goals

## Overview

This repository contains the reproducibility package of our ICST 2026 paper.

## Repository

This repository contains the implementation of our FandangoGrey tool, which is based on the [Fandango fuzzer](https://github.com/fandango-fuzzer/fandango), extending it with _soft constraints and execution feedback_.
The table below lists the most important files of our implementation.

| File                                                       | Description                                            |
|------------------------------------------------------------|--------------------------------------------------------|
| ./Dockerfile/                                              | Dockerfile to reproduce experiments                    |
| ./fcc.tar.gz                                               | LLVM-based instrumentation and analysis tools + PUTs   |
| ./experiment_artifacts.tar.gz                              | Raw data produced by our experiments                   |
| ./evaluation/execution_feedback/experiment_configurations/ | Experiment configuration files (.YAML files)           |
| ./evaluation/execution_feedback/subjects/                  | Input specifications for all evaluation subjects       |
| ./evaluation/execution_feedback/run_experiment.py          | Experiment entry point                                 |
| ./src/fandango/constraints/base.py                         | Soft constraints / TDigest / exponential scaling       |
| ./src/fandango/evolution/evaluation.py                     | Integration of soft constraints into evolution         |
| ./src/fandango/execution/analysis.py                       | Impl. of dynamic analysis and execution metrics        |
| ./tests/test_execution_feedback.py                         | Tests (execution feedback)                             |
| ./tests/test_softconstraint.py                             | Tests (soft constraints)                               |


## Installation prerequisites

> **System Requirements:** We recommend to use Ubuntu 22.04 and a x86 architecture. macOS works in principle, but some subjects (graphviz) don't build on macOS/arm. We ran the experiments on a AMD Ryzen Threadripper 3960X 24-Core Processor with 256 GB of memory.

## Running the experiments

We provide a Dockerfile to reproduce our experiments.
This Dockerfile installs all requirements builds and install our drop-in compiler replacement and analysis tools, `fcc` and `fan`.
The experiments can be run as follows:

```bash
docker build -f Dockerfile -t fandangogrey .
docker run fandangogrey # Idly run docker container indefinitely, you may need to open a new shell to continue
docker container ls # To find the docker container id
docker exec -it <container_id_goes_here> bash # Run a shell in the docker container
```

Now, inside the docker container shell, build the subjects:
```bash
$ cd fcc
$ make subjects/graphviz 
$ make subjects/lunasvg
$ make subjects/libxml2
$ cd ..
```

Next, run the experiments:
```bash
# Individual fitness experiments
$ mkdir experiment_output_graphviz_execpathlength &&\
python3 evaluation/execution_feedback/run_experiment.py\
    evaluation/execution_feedback/experiment_configurations/graphviz_execpathlength.yaml\
    --output-dir experiment_output_graphviz_execpathlength

$ mkdir experiment_output_graphviz_memory &&\
python3 evaluation/execution_feedback/run_experiment.py\
    evaluation/execution_feedback/experiment_configurations/graphviz_memory.yaml\
    --output-dir experiment_output_graphviz_memory

$ mkdir experiment_output_graphviz_codecoverage &&\
python3 evaluation/execution_feedback/run_experiment.py\
    evaluation/execution_feedback/experiment_configurations/graphviz_codecoverage.yaml\
    --output-dir experiment_output_graphviz_codecoverage

# Population fitness experiment
$ mkdir experiment_output_graphviz_afl &&\
python3 evaluation/execution_feedback/run_experiment.py\
    evaluation/execution_feedback/experiment_configurations/graphviz_afl.yaml\
    --output-dir experiment_output_graphviz_afl

# Replace "graphviz" with "lunasvg" or "libxml2" above to run those experiments.
```

Experiment outputs will be written to the respective output directories.
For an experiment run time of one hour, except a total run time of about two hours, as we replay generated inputs.

To change experiment configurations, one can either change configuration variables in the `.yaml` files directly, or override them using command-line arguments.
For instance, to run an experiment for one minute instead of one hour, with only one repetition, one could use:
```bash
python3 evaluation/execution_feedback/run_experiment.py\
    evaluation/execution_feedback/experiment_configurations/graphviz_execpathlength.yaml\
    --output-dir experiment_output_graphviz_execpathlength\
    --timelimit 60\
    --repetitions 1
```


To run the "Directed Greybox Fuzzing" experiment, use:
```bash
$ mkdir experiment_output_cjson &&\
python3 evaluation/execution_feedback/run_experiment.py\
    evaluation/execution_feedback/experiment_configurations/cjson_dgf.yaml\
    --output-dir experiment_output_cjson
```


## Adding your own experiment

1. Add your program under test and build it with `fcc` and extract static analysis information with `fan`. For instance, this is the build script for lunasvg, `fcc/subjects/lunasvg/build.sh`:

```bash
export CC=$(cd ../../llvm/build/compiler && pwd)/fcc
export CXX=$(cd ../../llvm/build/compiler && pwd)/fcc++
export FAN=$(cd ../../llvm/build/compiler && pwd)/fan

rm -fr lunasvg
git clone https://github.com/sammycage/lunasvg.git
cd lunasvg
git checkout 57f859fb936e1a33c6d2c232dca39cb07c36496f
cmake -B build .
cmake --build build
mkdir instrumentation && cp ./build/examples/svg2png instrumentation/
$FAN instrumentation/svg2png
cd ..
```



2. Add an experiment configuration file.
For instance, this is `evaluation/execution_feedback/experiment_configurations/lunasvg_execpathlength.yaml`:

```yaml
title: lunasvg-svg2png (Execution Path Length)

put: fcc/subjects/lunasvg/lunasvg/instrumentation/svg2png

specifications:
  - title: Execution Feedback
    short-title: executionfeedback
    plot-color: "#ff7f0e"
    path: evaluation/execution_feedback/subjects/lunasvg/specifications/lunasvg-execpathlength-0.fan

  - title: Input Spec.
    short-title: inputspec
    plot-color: "#1f77b4"
    path: evaluation/execution_feedback/subjects/lunasvg/specifications/lunasvg-execpathlength-1.fan

  - title: Input Spec. + Execution Feedback
    short-title: inputspec_executionfeedback
    plot-color: "#2ca02c"
    path: evaluation/execution_feedback/subjects/lunasvg/specifications/lunasvg-execpathlength-2.fan

metric: 'trace.ExecutionPathLength()'
aggregation: max
repetitions: 10
timelimit: 3600
population-size: 1000
y-label: Execution Path Length

output-dir: experiment_output/
```

3. Add the input specification files (`.fan`) referenced from the experiment configuration file, consisting of a grammar, potential hard input constraints, and soft constraints involving execution feedback.
For instance, this is `evaluation/execution_feedback/subjects/lunasvg/specifications/lunasvg-execpathlength-2.fan`:

```bash
<start> ::= <SVG>
...

where len(str(<start>)) <= 60
maximizing DynamicAnalysis(str(<start>)).ExecutionPathLength()
```

For more information on writing Fandango specifications, please refer to the [Fandango Language Reference](https://fandango-fuzzer.github.io/Language.html).
