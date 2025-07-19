# setup dataproc

1. copy the script run.sh in gs://bucket-name/utils/scripts/

2. Run this command to configure the dataproc cluster

```
CLUSTER_NAME="retail-datalake-cluster"
REGION="asia-south2"
BUCKET_NAME="retailer-datalake"

gcloud dataproc clusters create ${CLUSTER_NAME} \
    --region ${REGION} \
    --num-workers=2 \
    --worker-machine-type=n1-standard-2 \
    --worker-boot-disk-size=50 \
    --master-machine-type=n1-standard-2 \
    --master-boot-disk-size=50 \
    --image-version=2.0-debian10 \
    --enable-component-gateway \
    --optional-components=JUPYTER \
    --initialization-actions=gs://${BUCKET_NAME}/utils/scripts/run.sh \
    --metadata bigquery-connector-version=1.2.0 \
    --metadata spark-bigquery-connector-version=0.21.0
```
