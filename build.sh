#!/bin/sh

# Bail on first failure
set -e

pip install -e .[dev] 1> /dev/null
pip install -e .[web] 1> /dev/null
pytest ingest/*
python setup.py sdist