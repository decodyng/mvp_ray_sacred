from sacred import Experiment
from sacred.observers import FileStorageObserver

inner_ex = Experiment('inner_ex')


@inner_ex.config
def baseline_config():
    exponent = 2
    offset = 10
    min_val = 0
    max_val = 5
    _ = locals()
    del _


@inner_ex.main
def my_inner_experiment(exponent, offset, min_val, max_val):
    print(f"Offset: {offset}")
    print(f"Exponent: {exponent}")
    print(f"Min val: {min_val}")
    print(f"Max val: {max_val}")
    return (max_val - min_val)**exponent + offset


if __name__ == "__main__":
    observer = FileStorageObserver.create('inner_results')
    inner_ex.observers.append(observer)
    inner_ex.run_commandline()