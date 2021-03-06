A simple toy example to demonstrate the basics of creating a Ray tune experiment that runs 
as its worker function versions of Sacred experiments modified with values from the Ray tune config. Currently 
only tested in a single-machine, multi-CPU setting.  

If you don't have any familiarity with [Ray Tune](https://ray.readthedocs.io/en/latest/tune.html) 
(a parallelization library) or [Sacred](https://github.com/IDSIA/sacred/tree/master/sacred) 
(an experiment configuration library), I'd recommend you taking a look over both of
their documentation before you read this. Credit where due: this code is essentially a 
simplified, teaching-friendly version of a setup from Adam Gleave's work on the [Adversarial 
Policies codebase](https://github.com/HumanCompatibleAI/adversarial-policies)

### Before getting started, install requirements (preferably in a virtualenv!)
`pip install -r requirements.txt`

### To run the Ray version of the Sacred experiment
Run from top level of repo: 
`python -m tune_example.outer_experiment`

### To try running the non-parallel equivalent: 
`source ./serial_execution.sh`

### At a high level, what's happening here is:

- We create our actual Sacred Experiment of interest. In a machine learning context, maybe this 
is training a model and capturing training accuracy.
- We create an outer Experiment. This outer Experiment is responsible for running many different 
configurations of the inner experiment. Since this is also a Sacred Experiment, you could imagine 
having one named configs of this that corresponds to hyperparameter tuning, and another 
config for batch-execution of your model over a range of different environments for final evaluation.
- For a given outer-experiment config, we have (1) a set of inner-experiment parameters that are specific 
to that config, but which we aren't varying with Ray Tune, and (2) a set of inner Experiment parameters that 
we are varying. Perhaps we want to run a hyperparameter tuning job over one specific possible environment 
(so we'd want to hold that fixed), but perform training runs over a range of different learning rates.
- In the main function of the outer experiment, we run ray.tune() such that it executes our inner 
experiment many times, combining the inner experiment's default parameters, the fixed parameters for 
our config, and the varying parameters of our config. 


### Okay, let's get deeper into the weeds

#### inner_experiment.py 
(Inner_experiment is pretty cookie-cutter basic Sacred, so if you're familiar with Sacred 
configs already, maybe skip through this bit)
```def baseline_config():
    exponent = 2
    offset = 10
```
This part is just setting some default values for our inner experiment.
```
@inner_ex.main
def my_inner_experiment(exponent, offset):
    max_rand_val = 0
    for i in range(10000000):
        rand_val = random()
        new_val = rand_val**exponent + offset
        max_rand_val = max(new_val, max_rand_val)
    return max_rand_val
```
I was too lazy to write actual model-training code for this example, so instead I'm just having 
the body of my Experiment function do a bit of pointless, low-memory, mildly CPU-intensive work, 
so we can actually notice when we succeed at parallelizing it. The inner_ex.main just means that
this is the method that is run when we call inner_ex.run() with a given config. 


#### outer_experiment.py
```def worker_function(inner_ex_config, config):
    from inner_experiment import inner_ex
    inner_ex_dict = dict(inner_ex_config)
    merged_config = update(inner_ex_dict, config)

    observer = FileStorageObserver.create(tune.get_trial_dir())
    inner_ex.observers.append(observer)
    ret_val = inner_ex.run(config_updates=merged_config)
    track.log(accuracy=ret_val.result)
```
This worker function is what's called on every iteration of Ray Tune. The `config` argument 
is automatically generated by Ray tune, and will contain the values of whatever parameters we're tuning over. 
The most frustrating part of this function (honestly, of the entire example), is the fact that 
because Sacred experiments can't be pickled, you can't just pass in the experiment object as a parameter, 
but instead have to re-import the Experiment from within the function (that is, each worker
imports the Experiment in its own process). This means that, when you start wanting to do 
multi-machine clusters, you need to make sure the experiment is importable by the workers. 
The `inner_ex_config` argument contains whatever updates that we want to make to our inner experiment's default config 
for this particular test, but that we aren't actually tune-sampling over; it'll get fed in 
within our outer experiment's main method. Once we merge those two config files together, we just 
create an observer to store the results from the inner experiment, and run it with the merged configs 
as updates to the defaults. In this case, we're simulating a real experiment that returns some scalar result
(for example: training accuracy), and we use `ray.tune.track.log` to log that result. This allows us to 
use some nice Ray tooling around "give me the best config for this hyperparameter search based on this metric's value". 


```@outer_exp.named_config
def hyperparameter_search(inner_ex):
    """
    :param inner_ex: The config dict for inner_ex, available because it is an ingredient of outer_exp
    :return:
    """
    exp_name = "hyperparameter_search"
    spec = {"exponent": tune.grid_search(list(range(1, 10)))}
    modified_inner_ex = dict(inner_ex)
    # To test that we can run tuning jobs with parameters modified from default config
    # but not being sampled over through Ray
    modified_inner_ex['offset'] = 8
```
Our imagined hyperparameter-tuning config. Here, `offset` is being modified from the default, but 
remains constant for all the hyperparameter tuning runs. `exponent` is being tuned over, with 
values between 1 and 10. 


```@outer_exp.main
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
    best_config = analysis.get_best_config(metric="accuracy", mode="max")
    print(f"Best config is: {best_config}")
    print("Results available at: ")
    print(analysis._get_trial_paths())
```
Okay, here's where the magic really happens. First, we take in `modified_inner_ex`, which we've 
updated in our hyperparameter tuning config to contain a different value of offset. We 
use a special copy function to copy that, because Sacred dicts are strange Read Only objects. 

Notionally, we'd do a currying function next, where we call `trainable_function=functools.partial(worker_function, inner_ex_config)`. 
However, the current pip version of Ray still has a bug where partials callables aren't considered functions, and thus 
don't work within tune. It's been updated on github, but for the time being, we're just making this silly 
function-in-a-function to use a fixed value of `inner_ex_config` but still take in dynamic ones of `config` from Ray. 

Again, we need to specially copy the spec, because Ray needs to pickle it, and Sacred config values can't 
natively be modified or pickled. Recall that `spec` was a dictionary containing parameter keys that we wanted to 
vary in our experiment, and `tune` operations defining the sample values we want to test. This dictionary 
gets passed in as the `config` parameter of Ray (apologies for how annoyingly overloaded that word is here). 
We pass in the `trainable_function` we just created, which, remember, is a function that takes in a 
Ray-generated `config` and runs our inner Experiment. 

We then capture the results of `ray.tune.run`, which is an Analysis object that knows the tracked metric values 
of all the runs, as well as the locations, so we print those out. 

