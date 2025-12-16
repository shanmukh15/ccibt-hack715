#!/bin/bash
set -e

echo "Cleaning up Docker images..."
docker system prune -af
docker builder prune -f

export PROJECT_ID=ccibt-hack25ww7-715
export REGION=us-central1
export SERVICE_NAME=ccibt-hack715

IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/app-images/$SERVICE_NAME:latest"

echo "Building and pushing Docker image: $IMAGE"
docker build -t "$IMAGE" .
docker push "$IMAGE"

echo "Deploying to Cloud Run service: $SERVICE_NAME"
gcloud run deploy $SERVICE_NAME \
  --image "$IMAGE" \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "ALLOWED_ORIGINS=*"

echo "Deployment complete."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo "Service URL: $SERVICE_URL"
