import argparse
import yaml
import csv
import os
import subprocess
import logging
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import matplotlib.ticker as ticker

LOGGER = logging.getLogger("experiment")
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s:%(levelname)s:%(asctime)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

repo_root = Path(__file__).resolve().parent.parent.parent

def resolve_path(path: str, base: str = repo_root) -> Path:
    path = Path(path)
    return path if path.is_absolute() else (base / path).resolve()

def run_fandango(fan: Path, put: Path, args: str, experiment_output_file: Path, timelimit: int, population_size: int, fitness_type: str):
    command = [
        "fandango",
        "fuzz",
        "--no-cache",
        "-f", str(fan),
        "--experiment-output-file", str(experiment_output_file),
        "--stop-after-seconds", str(timelimit),
        "--stop-criterion", "lambda t: False",
        # "--random-seed", str(1),
        "-n", str(1),
        "-N", str(10000000000000),
        "--population-size", str(population_size),
        "--fitness-type", fitness_type,
        "--fcc",
        str(put),
    ]
    if args: command.append(args)
    LOGGER.info(f"Running command: {command}")
    proc = subprocess.Popen(
        command,
        stdout=open(os.devnull, 'w'), # subprocess.PIPE,
        stderr=open(os.devnull, 'w')  # subprocess.PIPE,
    )
    return proc

def run_replay(experiment_output_file: Path, put: Path, args: str, metric: str, csv_output_file: Path):
    command = [
        "python3",
        str(resolve_path("evaluation/execution_feedback/replay/replay.py")),
        "--experiment-output-file", str(experiment_output_file),
        "--metric", metric,
        "--csv-output-file", str(csv_output_file),
        str(put),
    ]
    if args: command.append(args)
    LOGGER.info(f"Running command: {command}")
    proc = subprocess.Popen(
        command,
        stdout=open(os.devnull, 'w'), # subprocess.PIPE,
        stderr=open(os.devnull, 'w')  # subprocess.PIPE,
    )
    return proc

# For debugging.
def individual_plot(timestamps, scores, title: str, plot_output_file: str):
    fig1, ax1 = plt.subplots()
    ax1.plot(timestamps, scores)
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Score")
    ax1.set_title(title)
    fig1.savefig(plot_output_file, format="pdf")

def consistent_human_format_factory(max_val):
    # Decide scale based on max_val
    if max_val >= 1e9:
        scale = 1e9
        suffix = 'B'
    elif max_val >= 1e6:
        scale = 1e6
        suffix = 'M'
    elif max_val >= 1e3:
        scale = 1e3
        suffix = 'K'
    else:
        scale = 1
        suffix = ''

    def formatter(x, pos):
        val = x / scale
        if val.is_integer():
            return f'{int(val)}{suffix}'
        else:
            return f'{val:.1f}{suffix}'
    return formatter

# Better: Add this to YAML
idx_to_linestyle = {
    0: ':',
    1: '--',
    2: '-.',
}

def main(config: dict, only_generate_inputs: bool):
    put: Path = resolve_path(config["put"])
    args = config.get("args", "")
    output_dir: Path = resolve_path(config.get("output_dir"))

    assert put.exists(), f"PUT {put} does not exist."
    assert output_dir.exists() and output_dir.is_dir(), f"Output directory {output_dir} does not exist."
    for spec in config.get("specifications", []):
        assert resolve_path(spec['path']).exists(), f"Specification {resolve_path(spec['path'])} does not exist."

    only_plot = False
    if not only_plot:
        procs = []
        for i in range(config["repetitions"]):
            LOGGER.info(f"Starting experiment {i + 1}/{config['repetitions']}...")
            for spec in config.get("specifications", []):
                title: str = spec.get("title", f"no title {i}")
                shorttitle: str = spec.get("short-title", f"noshorttitle_{i}")
                fan: Path = resolve_path(spec["path"])
                experiment_output_file: Path = (output_dir / f"inputs_{shorttitle}_rep{i}.tar")
                proc = run_fandango(fan, put, args, experiment_output_file, config["timelimit"], config["population-size"], config["fitness-type"])
                procs.append(proc)
        
        LOGGER.info("Waiting for all processes to finish...")
        for proc in procs:
            proc.wait()
            if proc.returncode != 0:
                LOGGER.error(f"Process {proc.pid} failed with return code {proc.returncode}.")
            else:
                LOGGER.info(f"Process {proc.pid} finished successfully.")

        if only_generate_inputs:
            print("Only generating inputs, skipping replay and plotting.")
            return
        
        replay_procs = []
        LOGGER.info("Finished experiments")
        for i in range(config["repetitions"]):
            LOGGER.info(f"Replaying experiment {i + 1}/{config['repetitions']}...")
            for spec in config.get("specifications", []):
                title: str = spec.get("title", f"no title {i}")
                shorttitle: str = spec.get("short-title", f"noshorttitle_{i}")
                fan: Path = resolve_path(spec["path"])
                experiment_output_file: Path = (output_dir / f"inputs_{shorttitle}_rep{i}.tar")
                csv_output_file: Path = (output_dir / f"plot_{shorttitle}_rep{i}.csv")

                proc = run_replay(experiment_output_file, put, args, config["metric"], csv_output_file)
                replay_procs.append(proc)

        LOGGER.info("Waiting for all replay processes to finish...")
        for proc in replay_procs:
            proc.wait()
            if proc.returncode != 0:
                LOGGER.error(f"Process {proc.pid} failed with return code {proc.returncode}.")
            else:
                LOGGER.info(f"Process {proc.pid} finished successfully.")

    LOGGER.info("Combined plotting...")
    plot_output_file: Path = (output_dir / f"combined_plot.pdf")
    fig, ax = plt.subplots(figsize=(4,3)) # (6, 6))

    for n_spec, spec in enumerate(config.get("specifications", [])):
        xs = []
        ys = []
        for i in range(config["repetitions"]):
            shorttitle: str = spec.get("short-title", f"noshorttitle_{i}")
            csv_file: Path = (output_dir / f"plot_{shorttitle}_rep{i}.csv")
            with open(csv_file, "r") as f:
                reader = csv.reader(f)
                next(reader)
                data = [(int(timestamp), float(score)) for (timestamp, score) in reader]
                if len(data) == 0: continue # no inputs were generated
                t0 = data[0][0]
                shifted_timestamps = [t - t0 for t, _ in data]
                scores = [score for _, score in data]
                assert shifted_timestamps[0] == 0

                aggr_y_for_x = {}
                optimal_so_far = scores[0]
                # timestamps can be duplicate (i.e., multiple inputs were generated in the same second)
                # Hence, we have multiple xi's with the same value.
                for xi, yi in zip(shifted_timestamps, scores):
                    if config["aggregation"] == "max":
                        optimal_so_far = max(optimal_so_far, yi)
                    else:
                        optimal_so_far = min(optimal_so_far, yi)
                    aggr_y_for_x[xi] = optimal_so_far

                # Convert to sorted lists
                result_x = sorted(aggr_y_for_x.keys())
                result_y = [aggr_y_for_x[xi] for xi in result_x]

                # interpolate
                x = [i for i in range(config["timelimit"])]
                y = []
                j = 0
                for xi in x:
                    while j + 1 < len(result_x) and result_x[j + 1] <= xi:
                        j += 1
                    y.append(result_y[j])
                xs.append(x)
                ys.append(y)
                individual_plot(x, y, spec["title"], plot_output_file=str(csv_file)+".pdf")
        
        y_stack = np.stack(ys)
        mean_y = np.mean(y_stack, axis=0)
        sem_y = stats.sem(y_stack, axis=0) # standard error of the mean
        ci95 = 1.96 * sem_y # 95% confidence interval
        title: str = spec.get("title", f"no title {i}")

        ax.yaxis.set_major_formatter(ticker.FuncFormatter(consistent_human_format_factory(max(mean_y + ci95))))
        ax.tick_params(axis='both', labelsize=12)
        x_minutes = [xx / 60 for xx in xs[0]]

        ax.plot(x_minutes, mean_y, color=spec.get("plot-color", "blue"), linestyle=idx_to_linestyle[n_spec], label=title)
        ax.fill_between(x_minutes, mean_y - ci95, mean_y + ci95, color=spec.get("plot-color", "blue"), alpha=0.2)

    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
    fig.tight_layout()
    fig.savefig(plot_output_file, format="pdf", bbox_inches='tight', pad_inches=0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay execution feedback and plot.")
    parser.add_argument(
        "config_file",
        type=str,
        help="Path to the configuration file. Example: 'path/to/config.yaml'",
    )

    parser.add_argument(
        "--repetitions",
        type=int,
        help="Number of repetitions for the experiment. Overrides the config file.",
    )

    parser.add_argument(
        "--timelimit",
        type=int,
        help="Time limit for the experiment in seconds. Overrides the config file.",
    )

    parser.add_argument(
        "--population-size",
        type=int,
        help="Population size. Overrides the config file.",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        help="Directory to save the output files. Overrides the config file.",
    )

    parser.add_argument(
        "--fitness-type",
        type=str,
        help="Indicates whether we are measuring population fitness. This will serialize <input>'s instead of <start> for plotting. Overrides the config file. Options are: individual and population. Default is individual.",
    )

    parser.add_argument(
        "--only-generate-inputs",
        type=bool,
        default=False,
        help="If true, only generate inputs without replaying them or plotting. Default is false.",
    )

    args = parser.parse_args()
    with open(args.config_file, "r") as file:
        config = yaml.safe_load(file)

    assert "aggregation" in config and config["aggregation"] in ["max", "min"], f"Invalid aggregation method: {config['aggregation']}. Must be 'max' or 'min'."
    config["repetitions"] = args.repetitions if args.repetitions is not None else config.get("repetitions", 1)
    config["timelimit"] = args.timelimit if args.timelimit is not None else config.get("timelimit", 60)
    config["population-size"] = args.population_size if args.population_size is not None else config.get("population-size", 100)
    config["output_dir"] = args.output_dir if args.output_dir is not None else config.get("output_dir", "experiment_output")
    config["fitness-type"] = args.fitness_type if args.fitness_type is not None else config.get("fitness-type", "individual")

    main(config, args.only_generate_inputs)