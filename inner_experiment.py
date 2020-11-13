from sacred import Experiment
from sacred.observers import FileStorageObserver
from numpy.random import random

inner_ex = Experiment('inner_ex')


@inner_ex.config
def baseline_config():
    exponent = 2
    offset = 10

@inner_ex.named_config
def high_offset():
    offset = 50


@inner_ex.main
def my_inner_experiment(exponent, offset):
    max_rand_val = 0
    for i in range(10000000):
        rand_val = random()
        new_val = rand_val**exponent + offset
        max_rand_val = max(new_val, max_rand_val)
    return max_rand_val


if __name__ == "__main__":
    observer = FileStorageObserver.create('inner_results')
    inner_ex.observers.append(observer)
    inner_ex.run_commandline()