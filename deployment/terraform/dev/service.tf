# Copyright 2025 Google LLC
# Vertex AI Agent Engine resources have been removed for the dev environment. Cloud Run
# deployment is now performed via container builds (Dockerfile) and the deploy script or
# Cloud Build pipelines.
  # Make dependencies conditional to avoid errors.
  depends_on = [google_project_service.services]
}
