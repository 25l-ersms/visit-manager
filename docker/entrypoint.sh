#!/bin/sh

# Set Google OAuth2 environment variables
export GOOGLE_CLIENT_ID="16014019269-8188pkjj04s2pjcch1q9k6riojvdq46p.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="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"

if [ "$1" = "debug" ]; then
    poetry run uvicorn --reload visit_manager.app.main:app --port 8082 --host 0.0.0.0
elif [ "$1" = "run" ]; then
    uvicorn --workers "${UVICORN_WORKERS:=4}" visit_manager.app.main:app --port 8082
else
    echo "Usage:
    $0 (run|debug)"
    exit 1
fi
