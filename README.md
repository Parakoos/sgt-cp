This was the initial repo for all my Circuit Python code to do with Shared Game Timer.

As the code grew and the number of devices multiplied, I needed to switch over to a more modular system. The idea is that each device will have its own repo, with imported sub-repos holding shared code.

The last few commits in this repo does some of this splitting up 'logically'. I will then copy over the code in each folder to new repos (named something like 'sgt-cp-core').