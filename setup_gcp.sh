#!/bin/bash

# Setup script for Google Cloud resources needed for Document Redlining API
# Usage: ./setup_gcp.sh [PROJECT_ID]

set -e

# Default values
PROJECT_ID=${1:-$(gcloud config get-value project)}
BUCKET_NAME="document-redlining-bucket-${PROJECT_ID}"
SERVICE_ACCOUNT_NAME="document-redlining-sa"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
SERVICE_NAME="document-redlining-api"
REGION="us-central1"

echo "Setting up Google Cloud resources for Document Redlining API..."
echo "Project ID: $PROJECT_ID"
echo "Bucket Name: $BUCKET_NAME"
echo "Service Account: $SERVICE_ACCOUNT_EMAIL"
echo "Region: $REGION"
echo ""

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Error: Not authenticated with gcloud. Please run 'gcloud auth login' first."
    exit 1
fi

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable iam.googleapis.com

# Create GCS bucket
echo "Creating GCS bucket..."
if ! gsutil ls -b gs://$BUCKET_NAME >/dev/null 2>&1; then
    gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME
    echo "Bucket $BUCKET_NAME created successfully"
else
    echo "Bucket $BUCKET_NAME already exists"
fi

# Create service account
echo "Creating service account..."
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL >/dev/null 2>&1; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="Document Redlining API Service Account" \
        --description="Service account for Document Redlining API"
    echo "Service account $SERVICE_ACCOUNT_EMAIL created successfully"
else
    echo "Service account $SERVICE_ACCOUNT_EMAIL already exists"
fi

# Grant Storage Object Admin role to service account
echo "Granting Storage Object Admin permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.objectAdmin"

# Grant Storage Object Viewer role to service account (for reading)
echo "Granting Storage Object Viewer permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.objectViewer"

# Grant Cloud Run Invoker role to service account
echo "Granting Cloud Run Invoker permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/run.invoker"

# Create service account key (optional, for local development)
echo "Creating service account key for local development..."
if [ ! -f "service-account-key.json" ]; then
    gcloud iam service-accounts keys create service-account-key.json \
        --iam-account=$SERVICE_ACCOUNT_EMAIL
    echo "Service account key created: service-account-key.json"
    echo "WARNING: Keep this file secure and don't commit it to version control!"
else
    echo "Service account key already exists: service-account-key.json"
fi

# Update deployment script with correct values
echo "Updating deployment script..."
sed -i.bak "s/document-redlining-bucket-\$PROJECT_ID/$BUCKET_NAME/g" deploy.sh

echo ""
echo "Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Deploy the application: ./deploy.sh"
echo "2. Or use Cloud Build: gcloud builds submit --config cloudbuild.yaml"
echo ""
echo "Environment variables for local development:"
echo "export GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json"
echo "export GCS_BUCKET_NAME=$BUCKET_NAME"
echo "export GCS_PROJECT_ID=$PROJECT_ID" 