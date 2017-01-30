#!/bin/sh

PYTHONPATH=$PYTHONPATH:$(pwd) coverage run --source src -m py.test --tb=line -v && coverage html
