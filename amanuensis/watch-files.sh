#!/bin/sh
while inotifywait -r -e modify,create,delete,move .; do
    pgrep uwsgi | xargs kill -9
    uwsgi --ini /etc/uwsgi/uwsgi.ini > /dev/null 2>&1 &
done