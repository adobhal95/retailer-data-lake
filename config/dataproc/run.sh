#!/bin/bash
# run.sh - Initialization Action

# Set up region and bucket variables
REGION=asia-south2
BUCKET_NAME=retailer-datalake

# Download connectors script from Google-provided bucket (for BigQuery)
gsutil cp gs://goog-dataproc-initialization-actions-${REGION}/connectors/connectors.sh /tmp/
bash /tmp/connectors.sh

# Copy PostgreSQL JDBC driver to Spark jars
gsutil cp gs://${BUCKET_NAME}/utils/jar/postgresql-42.7.7.jar /usr/lib/spark/jars/
chmod 644 /usr/lib/spark/jars/postgresql-42.7.7.jar