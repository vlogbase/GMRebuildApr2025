#!/bin/bash
gunicorn main:app -k gevent -w 4 --timeout 300 --bind 0.0.0.0:5000 --reload
