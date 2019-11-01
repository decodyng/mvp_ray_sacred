The goal of this repo is to show simplified patterns for how the Ray distributed computing
 library can be used to accelerate Sacred experiments. It currently has three sections: 
 
 I. A toy example using the basic Ray API to run experiments
 
 II. A toy example using Ray Tune (a hyperparameter-tuning library within Ray) to run 
 experiments 
 
 III. An example of a simplified but confirmed-working yaml configuration to create an AWS cluster. 
 
 ## What is Sacred? 
 Sacred is a Python experiment framework library that specifies ways to define different configuration
 parameters of an experiment, and, whenever an experiment is run, automatically store results along with the 
 exact configuration used for that experiment. 
 
 
 ## What is Ray? 
 Ray is a distributed computing library created by the RISE Lab at Berkeley. It's designed 
 with AI applications particularly in mind, and is fast, lightweight, and relatively easy to use. 
 One notable benefit of it is the ability for it to be easily scaled up to run across a large cluster using
 the same code as in a local environment. 
 
 ## How Do Ray & Sacred Work Together? 
 At a high level, both of these examples work by 1) creating a worker function that calls the 
 `ex.run()` method of whatever experiment you'd like to run parallelized trials of and 2) creating 
 some mechanism for passing in the different config changes you'd like to have apply in each of the
 trials. This is relatively straightforward, but has a few quirks, as a result of Sacred design decisions. 
 The most notable strange thing is that you cannot directly pass an experiment into a generic Ray worker 
 function, because all objects passed to workers have to be pickle-able, and Sacred experiments can't 
 be pickled. Additionally, Sacred config objects are ReadOnlyDicts with strange and somewhat unpredictable properties, 
 and so we often need to convert them into simple Python objects in order to modify them or 
 pass them around. 
 
 
 ## When To Use Ray vs Ray Tune?
 The basic Ray API uses a very simple syntax of turning functions into remote functions by applying a decorator, 
 and then calling that function an arbitrary number of times, with an arbitrary set of different parameter values, 
 with `function_name.remote()`. The user is responsible for each individual call of the function, and for 
 what to do with the results. It's straightforward highly flexible. 
 
 The Tune API is more specified to a particular use case: that of hyperparameter tuning. It assumes a structure 
 whereby your function has some set of parameters, and we want to run a number of trials varying the values 
 of these parameters and tracking the results. It has some nice utilities built around this use case, including 
 storing of each trial's results in a separate folder that it returns a list of at the end of the aggregated run, 
 and a straightforward API for logging metrics from each trial and easily identifying the configuration that 
 gave the highest value of the metric. One downside of this more prescriptive API is that it can be harder to adapt 
 to use cases that are slightly different from what it expects. An example of this is the fact that Tune assumes
 that parameter values vary independently across trials, and it can be a bit tricky if you have an experiment where this
 is not the case (if, for example, you need to set your model class to `LSTM` for some specific set of environments). 
 It's possible to engineer solutions around this, and one example of such a solution is present in the example, but it 
 is mildly annoying.
 
 Overall, my recommendation would be to start out by using the basic Ray API for simple use cases, and if you have a larger-scale project, 
 take the time to make it work with the more full-featured Tune API. Another consideration is that Tune is nicer to work
 with if you are relying a lot on the saved-file output stored by a FileStorageObserver, because Tune will auto-create 
 directories for each run according to the tuned parameter values, so you don't have to worry about creating separate 
 observers for each run the way you do in base Ray. 
 
 
 
 