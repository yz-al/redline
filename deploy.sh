#!/bin/bash

# Deployment script for Document Redlining API to Google Cloud Run
# Usage: ./deploy.sh [PROJECT_ID] [BUCKET_NAME] [REGION]

set -e

# Default values
PROJECT_ID=${1:-$(gcloud config get-value project)}
BUCKET_NAME=${2:-"document-redlining-bucket"}
REGION=${3:-"us-central1"}
SERVICE_NAME="document-redlining-api"

echo "Deploying Document Redlining API to Google Cloud Run..."
echo "Project ID: $PROJECT_ID"
echo "Bucket Name: $BUCKET_NAME"
echo "Region: $REGION"
echo "Service Name: $SERVICE_NAME"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Error: Not authenticated with gcloud. Please run 'gcloud auth login' first."
    exit 1
fi

# Set the project
gcloud config set project $PROJECT_ID

# Build and push the Docker image
echo "Building and pushing Docker image..."
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"
docker build -t $IMAGE_NAME .
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars "GCS_BUCKET_NAME=$BUCKET_NAME,GCS_PROJECT_ID=$PROJECT_ID" \
    --set-env-vars "PYTHONUNBUFFERED=1"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo "Deployment completed successfully!"
echo "Service URL: $SERVICE_URL"
echo "API Documentation: $SERVICE_URL/docs"
echo ""
echo "To test the API, you can use the Postman collection: Document_Redlining_API.postman_collection.json"
echo "Remember to update the base_url variable in Postman to: $SERVICE_URL" 