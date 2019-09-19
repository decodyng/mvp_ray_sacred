from inner_experiment import inner_ex
from sacred import Experiment
from sacred.observers import FileStorageObserver
from ray import tune
import os.path as osp
from ray.tune import track
from utils import sacred_copy, update

macro_ex = Experiment('macro_ex', ingredients=[inner_ex])


def worker_function(inner_ex_config, config):
    from inner_experiment import inner_ex
    # Something that runs inner_ex by combining "base" config and ray experiment config
    inner_ex_dict = dict(inner_ex_config)
    merged_config = update(inner_ex_dict, config)

    observer = FileStorageObserver.create(osp.join('inner_nested_results'))
    inner_ex.observers.append(observer)
    ret_val = inner_ex.run(config_updates=merged_config)
    track.log(accuracy=ret_val.result)

@macro_ex.named_config
def hyperparameter_search(inner_ex):
    exp_name = "hyperparameter_search"
    spec = {"exponent": tune.grid_search([1, 2, 4, 8])}
    modified_inner_ex = dict(inner_ex)
    modified_inner_ex['offset'] = 8
    _ = locals()
    del _


@macro_ex.config
def base_config(inner_ex):
    spec = {}
    ray_server = None # keeping this here as a reminder we could start an autoscaling server if we wanted
    _ = locals()
    del _


@macro_ex.main
def multi_main(modified_inner_ex, exp_name, spec):
    inner_ex_config = sacred_copy(modified_inner_ex)

    def trainable_function(config):
        # Turns out functools.partial() doesn't parse as a function for Ray's purpose of
        # validating the passed-in run function, so I'm doing this silly thing
        worker_function(inner_ex_config, config)

    spec_copy = sacred_copy(spec)
    analysis = tune.run(
        trainable_function,
        name=exp_name,
        config=spec_copy
    )
    best_config = analysis.get_best_config(metric="accuracy")
    print(f"Best config is: {best_config}")
    print("Results available at: ")
    print(analysis._get_trial_paths())


def main():
    observer = FileStorageObserver.create('macro_results')
    macro_ex.observers.append(observer)
    macro_ex.run_commandline()


if __name__ == '__main__':
    main()
