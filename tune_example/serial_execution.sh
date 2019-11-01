#!/usr/bin/env bash
for i in $(seq 1 200); do python inner_experiment.py with exponent=$i; done