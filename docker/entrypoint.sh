#!/bin/sh

if [ "$1" = "debug" ]; then
    poetry run uvicorn --reload visit_manager.app.main:app --port 8082 --host 0.0.0.0
elif [ "$1" = "run" ]; then
    uvicorn --workers "${UVICORN_WORKERS:=4}" visit_manager.app.main:app --port 8082
else
    echo "Usage:
    $0 (run|debug)"
    exit 1
fi
