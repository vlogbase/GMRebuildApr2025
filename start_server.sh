#!/bin/bash
export ENABLE_RAG=true
export PYTHONPATH=$PYTHONPATH:$(pwd)
python app.py
