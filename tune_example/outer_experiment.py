from inner_experiment import inner_ex
from sacred import Experiment
from sacred.observers import FileStorageObserver
from ray import tune
import ray
from utils import sacred_copy, update, detect_ec2

outer_exp = Experiment('outer_exp', ingredients=[inner_ex])


def worker_function(inner_ex_config, config):
    """
    Combines experiment config and auto-generated Ray config, and runs an iteration of
    inner_ex on that combined config.

    :param inner_ex_config: The current values of inner experiment config, including
    any modifications we might have made in an macro_experiment config update
    :param config: Config generated by Ray tune
    :return:
    """
    from inner_experiment import inner_ex
    # Something that runs inner_ex by combining "base" config and ray experiment config
    inner_ex_dict = dict(inner_ex_config)
    merged_config = update(inner_ex_dict, config)

    # This will create an observer in the Tune trial directory, meaning that
    # inner experiment configs will be saved at <trial.log_dir>/1
    observer = FileStorageObserver.create(tune.get_trial_dir())
    inner_ex.observers.append(observer)
    ret_val = inner_ex.run(config_updates=merged_config)
    tune.report(accuracy=ret_val.result)


@outer_exp.config
def base_config(inner_ex):
    ray_server = None # keeping this here as a reminder we could start an autoscaling server if we wanted
    exp_name = "hyperparameter_search"
    spec = {"exponent": tune.grid_search(list(range(1, 10)))}
    modified_inner_ex = dict(inner_ex)
    # To test that we can run tuning jobs with parameters modified from default config
    # but not being sampled over through Ray
    modified_inner_ex['offset'] = 8


@outer_exp.main
def multi_main(modified_inner_ex, exp_name, spec):
    inner_ex_config = sacred_copy(modified_inner_ex)

    def trainable_function(config):
        # Turns out functools.partial() doesn't parse as a function for Ray's purpose of
        # validating the passed-in run function, so I'm doing this silly thing
        worker_function(inner_ex_config, config)

    # Need to sacred_copy spec because otherwise it's a ReadOnlyDict, which causes problems
    spec_copy = sacred_copy(spec)
    if detect_ec2():
        ray.init(address="auto")
    else:
        ray.init(num_cpus=5)
    analysis = tune.run(
        trainable_function,
        name=exp_name,
        verbose=0,
        config=spec_copy,
        # This tells Ray to save its results inside the outer experiment's
        # File Observer directory
        local_dir=outer_exp.observers[0].dir
    )
    best_config = analysis.get_best_config(metric="accuracy", mode="max")
    print(f"Best config is: {best_config}")
    print("Results available at: ")
    print(analysis._get_trial_paths())


def main():
    observer = FileStorageObserver.create('macro_results')
    outer_exp.observers.append(observer)
    outer_exp.run_commandline()


if __name__ == '__main__':
    main()
