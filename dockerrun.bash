#!/bin/bash

nginx
poetry run gunicorn -c "/amanuensis/deployment/wsgi/gunicorn.conf.py"