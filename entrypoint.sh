#!/bin/bash

# Function to read from secrets if available
read_secret() {
  local secret_path=$1
  if [ -f "$secret_path" ]; then
    cat "$secret_path"
  else
    echo ""
  fi
}

# Override environment variables with secrets if present
DB_HOST=${DB_HOST:-$(read_secret $DB_HOST_SECRET)}
DB_NAME=${DB_NAME:-$(read_secret $DB_NAME_SECRET)}
DB_USER=${DB_USER:-$(read_secret $DB_USER_SECRET)}
DB_PASSWORD=${DB_PASSWORD:-$(read_secret $DB_PASSWORD_SECRET)}

# Export the variables so they can be accessed by Python scripts
export DB_HOST
export DB_NAME
export DB_USER
export DB_PASSWORD

# Determine the script to run
if [ "$1" == "monitor" ]; then
  python3 /app/monitor.py
elif [ "$1" == "query" ]; then
  python3 /app/query.py
elif [ "$1" == "usage" ]; then
  python3 /app/usage.py
elif [ "$1" == "initial" ]; then
  python3 /app/initial-run.py
else
  echo "Usage: docker run <image> [monitor|query|usage|initial]"
  exit 1
fi

