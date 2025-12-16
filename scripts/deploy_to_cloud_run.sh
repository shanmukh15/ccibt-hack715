#!/usr/bin/env bash
# Deploys the combined FastAPI + Vite app to Cloud Run.
# Optional env vars to customize the deployment.
#   PROJECT_ID     - GCP project id (defaults to gcloud config get project)
#   REGION         - Cloud Run region (defaults to us-central1)
#   SERVICE_NAME   - Cloud Run service name (defaults to ccibt-hack715)
#   REPOSITORY     - Artifact Registry repo name (defaults to app-images)
#   ALLOWED_ORIGINS- Comma-separated CORS origins (defaults to *)
#   USE_CLOUD_BUILD- Set to 1 to use gcloud builds submit instead of docker CLI

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-ccibt-hack715}"
REPOSITORY="${REPOSITORY:-app-images}"
ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-*}"
USE_CLOUD_BUILD="${USE_CLOUD_BUILD:-0}"
API_MODEL="${API_MODEL:-}"
API_KEY="${API_KEY:-}"

log() {
  printf "\033[1;34m[deploy]\033[0m %s\n" "$*"
}

die() {
  printf "\033[1;31m[error]\033[0m %s\n" "$*" >&2
  exit 1
}

ensure_project() {
  if [[ -z "$PROJECT_ID" ]]; then
    PROJECT_ID="$(gcloud config get-value project 2>/dev/null || true)"
  fi
  [[ -n "$PROJECT_ID" ]] || die "PROJECT_ID is not set and gcloud has no default project."
  log "Using project: $PROJECT_ID"
}

require_tools() {
  command -v gcloud >/dev/null || die "gcloud CLI is required"
  if [[ "$USE_CLOUD_BUILD" != "1" ]]; then
    command -v docker >/dev/null || die "docker CLI is required when USE_CLOUD_BUILD!=1"
  fi
}

frontend_build() {
  log "Installing frontend dependencies"
  npm install --prefix "$ROOT_DIR/frontend"
  log "Building frontend"
  npm run build --prefix "$ROOT_DIR/frontend"
}

backend_install() {
  log "Installing backend dependencies"
  pip install --upgrade pip
  pip install -e "$ROOT_DIR"
}

create_artifact_repo() {
  log "Ensuring Artifact Registry repo $REPOSITORY exists in $REGION"
  if ! gcloud artifacts repositories describe "$REPOSITORY" --location "$REGION" >/dev/null 2>&1; then
    gcloud artifacts repositories create "$REPOSITORY" \
      --repository-format=docker \
      --location="$REGION" \
      --description="Container images for $SERVICE_NAME"
  fi
}

build_and_push_image() {
  local image="$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$SERVICE_NAME:latest"
  log "Target image: $image"

  if [[ "$USE_CLOUD_BUILD" == "1" ]]; then
    log "Building with Cloud Build"
    gcloud builds submit "$ROOT_DIR" --region "$REGION" --tag "$image"
  else
    log "Building Docker image locally"
    docker build -t "$image" "$ROOT_DIR"
    log "Pushing Docker image"
    docker push "$image"
  fi

  echo "$image"
}

deploy_cloud_run() {
  local image="$1"
  local env_vars="ALLOWED_ORIGINS=$ALLOWED_ORIGINS,FRONTEND_DIST=/app/static"
  if [[ -n "$API_MODEL" ]]; then
    env_vars+="\,API_MODEL=$API_MODEL"
  fi
  if [[ -n "$API_KEY" ]]; then
    env_vars+="\,API_KEY=$API_KEY"
  fi
  log "Deploying Cloud Run service $SERVICE_NAME"
  gcloud run deploy "$SERVICE_NAME" \
    --image "$image" \
    --region "$REGION" \
    --allow-unauthenticated \
    --set-env-vars "$env_vars"
}

main() {
  ensure_project
  require_tools
  frontend_build
  backend_install
  create_artifact_repo
  image="$(build_and_push_image)"
  deploy_cloud_run "$image"
  log "Deployment complete"
  gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(status.url)'
}

main "$@"
