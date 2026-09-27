#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Dedicated participant profile: never fall back to an unrelated AWS account.
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_SECURITY_TOKEN
export AWS_SHARED_CREDENTIALS_FILE="$project_dir/.local/aws-credentials"
export AWS_CONFIG_FILE="$project_dir/.local/aws-config"
export AWS_PROFILE=factored-2026
export AWS_DEFAULT_REGION=us-east-2
export AWS_REGION=us-east-2
export AWS_PAGER=""
export AWS_RETRY_MODE=standard
export AWS_MAX_ATTEMPTS=3
if [[ ! -f "$AWS_SHARED_CREDENTIALS_FILE" && "${1:-}" != configure ]]; then
  echo 'Dataset credentials are missing. Follow docs/SETUP.md.' >&2
  exit 1
fi
exec aws "$@"
