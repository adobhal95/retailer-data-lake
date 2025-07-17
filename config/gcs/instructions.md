### set up buckets

```
# In your current project
PROJECT_ID=$(gcloud config get-value project)

gcloud storage buckets create gs://retailer-datalake \
  --location=asia-south2 \
  --uniform-bucket-level-access \
  --public-access-prevention \
  --soft-delete-duration=7d \
  --project=$PROJECT_ID
```
