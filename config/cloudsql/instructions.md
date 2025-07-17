### Setup Cloud Sql

1. setup cloudsql instances

```
# Ensure you are logged into the correct GCP project
# In your active project
PROJECT-ID=$(gcloud config get-value project)
gcloud config set project $PROJECT-ID

# create two instances named cloudsql-retailer and cloudsql-supplier
gcloud sql instances create INSTANCE-NAME \
  --database-version=POSTGRES_14 \
  --region=asia-south1 \
  --tier=db-custom-2-20480 \
  --storage-size=20GB \
  --storage-type=SSD \
  --availability-type=ZONAL \
  --edition=ENTERPRISE \
  --assign-external-ip \
  --authorized-networks=0.0.0.0/0 \
  --root-password="YOUR_SECURE_PASSWORD" \
  --project=YOUR_PROJECT_ID
```

2. Setup database in both these two instances

```
# create database retailer_db in cloudsql-retailer
gcloud sql databases create retailer_db \
  --instance=retailer_instance \
  --project=$PROJECT-ID
# create database supplier_db in cloudsql-supplier
gcloud sql databases create supplier_db \
  --instance=cloudsql-supplier \
  --project=$PROJECT-ID
```

3. setup username and password

```
gcloud sql users create retailer_user \
  --host=% \
  --instance=cloudsql-retailer \
  --password="password123" \
  --project=$PROJECT-ID

gcloud sql users create supplier_user \
  --host=% \
  --instance=cloudsql-supplier \
  --password="password123" \
  --project=$PROJECT-ID
```

4. Go to GCP console, search for cloudsql and inside the cloudsql instance go to each sql instance. Login to cloud sql studio withthe username and password created earlier and run the scripts for creating the tables and inserting data.
