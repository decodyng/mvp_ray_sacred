A test project to create a Ray tune experiment that runs as its worker function 
versions of Sacred experiments modified with values from the Ray tune config. Currently 
only tested in a single-machine, multi-CPU setting.  

To test, run: 
`python macro_experiment.py with hyperparameter_search`


Serial Execution: 
real    0m43.327s
user    0m55.614s
sys     0m12.676s

Parallel Execution
real    0m14.558s
user    0m7.180s
sys     0m2.147s
