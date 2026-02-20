import argparse
import tarfile
import os
import re
import matplotlib.pyplot as plt
from tqdm import tqdm

from fandango.logger import LOGGER
from fandango.execution.analysis import StaticAnalysis, DynamicAnalysis

class InputRunner:
    def __init__(self, da: DynamicAnalysis, metric: str):
        self.da = da
        self.metric = metric
    
    def run(self, input_data: str):
        trace: dict = self.da.trace_input(input_data)
        score: int = eval(self.metric) # uses trace
        #assert isinstance(score, int), f"Score must be an integer. Got {type(score)}."
        return score

def output_csv(data: list, csv_output_file: str):
    with open(f"{csv_output_file}", "w") as f:
        f.write("timestamp,score\n")
        for timestamp, score in data:
            f.write(f"{timestamp},{score}\n")

def main(experiment_output_file: str, put: str, put_args: list[str], metric: str, csv_output_file: str):
    assert metric.startswith("trace."), f"Invalid metric: {metric}. Must start with 'trace.'."
    assert os.path.exists(os.path.dirname(csv_output_file)), f"Parent directory of {os.path.dirname(csv_output_file)} does not exist."

    root_directory: str = os.path.dirname(put)
    cfg_directory: str = os.path.join(root_directory, ".cfg/")
    bb_to_dbg_json: str = os.path.join(root_directory, ".bb_to_dbg.json")

    LOGGER.info("Setting up static and dynamic analysis.")
    sa = StaticAnalysis(cfg_directory, bb_to_dbg_json)
    da = DynamicAnalysis(sa, root_directory, put, put_args)
    inputRunner = InputRunner(da, metric)


    LOGGER.info("Loading and processing inputs.")
    data = []
    max_score = None
    regex_individual_fitness = re.compile(r"^inp-(\d+)-(\d+)$")
    regex_population_fitness = re.compile(r"^inp-(\d+)-(\d+)-(\d+)$")
    with tarfile.open(experiment_output_file, "r") as tar:
        input_objs = sorted([m for m in tar.getmembers() if m.isfile()], key=lambda m: m.name)
        if regex_individual_fitness.match(input_objs[0].name):
            print("Individual fitness...")
            for input_obj in tqdm(input_objs, desc="Processing inputs", unit="input"):
                match = regex_individual_fitness.match(input_obj.name)
                assert match, f"Input name {input_obj.name} does not match expected pattern."
                input_index = int(match.group(1))
                input_timestamp = int(match.group(2))
                input_file = tar.extractfile(input_obj)
                if input_file is not None:
                    input = input_file.read().decode("utf-8")
                    try:
                        score: int = inputRunner.run(input)
                        data.append((input_timestamp, score))
                    except Exception as e:
                        LOGGER.error(f"Error while running the input in the PUT — maybe the input made the PUT crash? {e}")
                        continue
        elif regex_population_fitness.match(input_objs[0].name):
            print("Population fitness...")
            seen = {}
            covered_bbs = set()
            for input_obj in tqdm(input_objs, desc="Processing inputs", unit="input"):
                match = regex_population_fitness.match(input_obj.name)
                assert match, f"Input name {input_obj.name} does not match expected pattern."
                input_index = int(match.group(1))
                input_timestamp = int(match.group(2))
                input_pos_in_pop = int(match.group(3))
                input_file = tar.extractfile(input_obj)
                if input_file is not None:
                    if input_index not in seen:
                        seen[input_index] = -1
                        if covered_bbs != set():
                            data.append((input_timestamp, len(covered_bbs)))
                        covered_bbs = set()
                    # Assert everything is in order
                    assert input_pos_in_pop == seen[input_index]+1
                    seen[input_index] = input_pos_in_pop
                    input = input_file.read().decode("utf-8")
                    try:
                        covered: dict = inputRunner.run(input)
                        covered_bbs.update(covered)
                    except Exception as e:
                        LOGGER.error(f"Error while running the input in the PUT — maybe the input made the PUT crash? {e}")
                        continue
            data.append((input_timestamp, len(covered_bbs)))
        else:
            assert False, "Invalid filenames in .tar"

    output_csv(data, csv_output_file)

def tar_file_path(path: str) -> str:
    if not path.endswith(".tar"):
        raise argparse.ArgumentTypeError("The output file must end with '.tar'")
    return path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay execution feedback and plot.")
    parser.add_argument(
        "--experiment-output-file",
        type=tar_file_path,
        required=True,
        help="Path to the experiment output file (.tar)",
    )

    parser.add_argument(
        "--metric",
        type=str,
        required=True,
        help="The metric to be used for evaluation. Example: 'trace.ExecutionPathLength()'",
    )

    parser.add_argument(
        "--csv-output-file",
        type=str,
        required=True,
        help="Path to the output csv file. Example: 'path/to/file.csv'",
    )

    parser.add_argument(
        "put",
        metavar="command",
        type=str,
        nargs="?",
        help="command to be invoked with a Fandango input",
    )

    parser.add_argument(
        "put_args",
        metavar="args",
        type=str,
        nargs=argparse.REMAINDER,
        help="the arguments of the command",
    )

    args = parser.parse_args()

    main(
        experiment_output_file=args.experiment_output_file,
        put=args.put,
        put_args=args.put_args,
        metric=args.metric,
        csv_output_file=args.csv_output_file,
    )


