This cluster definition file (basic_aws_cluster.yaml) is basically a lightly modified version of the example 
Ray cluster configuration that I've updated to demonstrate how to develop on Ray within a Github repo. Many of the comments 
in the file were present in the original documentation file and are thus not my work, but it seemed 
valuable to keep them in the file because they were useful. 



The first thing to know is that this is a cluster using AWS EC2 nodes as both the head and worker 
nodes. So, if you don't have an AWS account with a Access Key and Secret Key, it's not going to be possible 
to work through this example. I by-default have set the worker nodes to relatively large machines 
(generally a sensible thing when parallelizing, since there's a fixed cost to each setup, and it's nice 
to get more CPUs per payment of that cost), so if you're testing this on your account, do make sure 
to tear the cluster down once you're finished working with it (using the `ray down` syntax) so you don't 
get charged lots of money. That said: the main pre-requisite to using this code is installing this 
repo's `requirements.txt` and configuring your credentials (by running `aws configure`). 

## How to use this file
To start a new cluster, use the Ray command: `ray up basic_aws_cluster.yaml`. 
This will trigger the creation of a head node, as well as however many worker nodes you specified in `initial_workers`. 
Whenever a new node is created, the contents of the `setup_commands` parameter in the file are run on that node. 
In this file, setup consists of: 
1. Adding an Anaconda version of Python 3.6 to the PATH
2. Installing Ray 
3. Cloning this repo (`mvp_ray_sacred`)
4. Checking out whichever hash of the repo we were most recently working on, and installing the repo's `requirements.txt` 

## Options for Syncing Code & Development Environment
A central problem of running Sacred experiments on Ray is that you can't just send a pickled function over to a worker; 
because Sacred experiments cannot be pickled, and must be imported, you need to have the code of the repo available 
on all of the workers so they can do that importing. In general, when using Ray, you want to have some way of 1) auto-syncing your 
code to (at least) the head machine, and 2) installing all of your dependencies on both the head and worker nodes. The most simplified way to do this 
(as far as I can tell) is what I've done here: have a public git repo that contains a `requirements.txt`, sync that down to the new machine, and install 
your Python dependencies based on the requirements file. In particular, I'm checking out the hash of the repo that matches whatever the 
current hash of master is, on the machine that I'm triggering cluster creation from. An important note: if you're developing on a branch other than 
master, change the branch that is referenced within the `file_mounts` command. The file mounts command is basically copying a file from your local machine, 
in this case the current git head ref, to the remote machine. However, this can also be used for copying generic files up to your remote machine from the 
development environment. 

If you want more certainty of having the same environment as a local install, another alternative is to create a virtualenv 
within the repo itself, such that the remote machine can just execute `source myvirtualenv/bin/activate` and then be using
the same environment you have for development. A downside here is that a VirtualEnv is a fairly bulky object to have 
in a Git repo. The most flexible option, though also the one with the highest startup cost and requisite knowledge, 
is to use a Docker container that contains your code and has all of your Python and system dependencies installed. If you have 
such a container created and available on DockerHub, the Ray cluster syntax has a built-in way to specify that container, which will then 
be downloaded and run on each of your head and worker nodes. 

## Autoscaling
Ray AWS clusters have the ability to scale up and turn off clusters according to the compute needs of your job. You can control this
by specifying min and max workers, by setting `idle_timeout_minutes` to however long you'd like your machine to run idle 
before it's shut off, and by setting `target_utilization_fraction` to the proportion of the cluster of cluster 
usage at which you want to trigger spinning up another node. Word to the wise: this system *mostly* works, but is 
slightly buggy, so I'd recommend checking on your jobs, even if you think they should have autoscaled down, so you don't accidentally
leave a bunch of big machines running for an extended period. The `head_node` and `worker_node` parameters of the config 
can be used to specify what size of machines you'd like to use for head and worker respectively. 

## AWS Authentication 
In order to create and connect to EC2 instances, Ray needs to specify a key pair that it will use. If you have an existing Key Pair 
that you'd like to use, you can set that in `ssh_private_key`, otherwise it will create one with a default name and use that. 




