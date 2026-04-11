#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="quest-493015"
REGION="us-central1"

gcloud config set project "${PROJECT_ID}"
SERVICE_NAME="quest-api"
IMAGE="gcr.io/${PROJECT_ID}/quest-api"

ENV_FILE=".env"
ENV_VARS_LIST=()

if [[ -f "${ENV_FILE}" ]]; then
  while IFS= read -r line || [[ -n "${line}" ]]; do
    # Trim leading/trailing whitespace
    line="${line#${line%%[![:space:]]*}}"
    line="${line%${line##*[![:space:]]}}"

    # Skip comments and empty lines
    if [[ -z "${line}" || "${line:0:1}" == "#" ]]; then
      continue
    fi

    # Drop optional export prefix
    if [[ "${line}" == export* ]]; then
      line="${line#export }"
    fi

    if [[ "${line}" != *"="* ]]; then
      continue
    fi

    key="${line%%=*}"
    value="${line#*=}"

    if [[ "${key}" == "ANTHROPIC_API_KEY" ]]; then
      continue
    fi

    ENV_VARS_LIST+=("${key}=${value}")
  done < "${ENV_FILE}"
fi

ENV_VARS=""
if [[ ${#ENV_VARS_LIST[@]} -gt 0 ]]; then
  IFS=',' ENV_VARS="${ENV_VARS_LIST[*]}"
fi

gcloud builds submit --config cloudbuild.yaml --substitutions="_IMAGE=${IMAGE}" .

DEPLOY_CMD=(
  gcloud run deploy "${SERVICE_NAME}"
  --image "${IMAGE}"
  --region "${REGION}"
  --platform managed
  --allow-unauthenticated
  --port 8080
  --memory 512Mi
  --timeout 3600
  --min-instances 1
  --set-secrets "ANTHROPIC_API_KEY=anthropic-api-key:latest"
)

if [[ -n "${ENV_VARS}" ]]; then
  DEPLOY_CMD+=(--set-env-vars "${ENV_VARS}")
fi

"${DEPLOY_CMD[@]}"

gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --platform managed \
  --format "value(status.url)"
