#!/usr/bin/env bash
for i in $(seq 1 50); do python inner_experiment.py with exponent=$i; done