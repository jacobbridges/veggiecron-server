#!/bin/sh

PYTHONPATH=$PYTHONPATH:$(pwd) pytest --tb=line -v
