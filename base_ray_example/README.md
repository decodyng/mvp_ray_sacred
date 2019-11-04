This example is designed to show how to use Ray to accelerate Sacred experiments without using the Ray Tune API. 
In the Ray Tune API, tuning runs are defined in terms of sets of parameters which are sampled independently from one another 
for each run. The base Ray is more flexible: rather than designing a sampling procedure and having your runs come from that sampling procedure, 
in base Ray you call each invocation of the function you want to parallelize (in this case, a function that runs your Sacred experiment) independently and 
directly. This can make it easier to parallelize a set of runs whose parameters vary jointly, or in some other complex way. On the negative side, it also lacks 
some of the helpful utilities of Ray Tune, including Tune's native utility for collecting and organizing the results of each run in separate directories. 

This example works by: 
1. In the config function for the outer Experiment, defining a set of config_permutations, representing the different sets of parameters we want to use on 
this specific outer-experiment run, including both the direct Sacred parameters we want to change and also any inner_experiment named_configs we want to apply.  
2. Defining a worker function that takes in the the config updates and named configs, creates a FileStorageObserver, and then runs the inner expeiment with
those config updates and named configs. 
3. In the outer Experiment main function, calls the `worker_function.remote()` for each set of parameters. Calls to remote functions don't return values, but only ObjectIds, 
which means the program doesn't block on those functions completing their computation until we call `ray.get(results)`. By contrast, if we did a for loop where at 
each iteration we called `result = worker_function.remote()` and then `ray.get(result)`, we wouldn't experience any benefits from parallelization because Ray would wait for 
the prior task to complete before initiating the next one. 

