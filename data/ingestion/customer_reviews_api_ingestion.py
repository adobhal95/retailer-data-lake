from pyspark.sql import SparkSession
import requests
import json
import pandas as pd
import datetime
from google.cloud import storage


# initialize spark session
spark = SparkSession.builder.appName("customer_reviews_api_ingestion").getOrCreate()


def get_api_response(api_url: str):
    """
    Fetch the latest api response from the api
    Returns:
        Pandas DataFrame
    """
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            print(f"data fetched from api, total records fetched: {len(data)}")
            # convert the json data to pandas dataframe
            df = pd.DataFrame(data)
            return df
    except Exception as e:
        print(f"error occured while fetching data, status_code:{response.status_code}")
        exit()


def store_data_in_gcs(local_file_name: str, bucket_name: str, target_path: str):
    """
    stores the latest reviews in gcs bucket in parquet format
    Returns:
        None
    """

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(target_path)
    # upload the parquet file to gcs
    blob.upload_from_filename(local_file_name)
    print(f"data successfully written to gs://{bucket_name}/{target_path}")


def api_start_process():
    # review api url
    url = "https://6879045063f24f1fdca07d19.mockapi.io/api/v1/retailer/reviews"
    df = get_api_response(url)
    # current data for file name
    today = datetime.datetime.now().strftime("%Y%m%d")  # format: YYYYMMDD
    # define File Paths with Date
    local_parquet_file = f"/tmp/customer_reviews_{today}.parquet"
    GCS_BUCKET = "retailer-datalake"
    GCS_PATH = f"landing/customer_reviews/customer_reviews_{today}.parquet"

    # save parquet file to local path
    df.to_parquet(local_parquet_file, index=False)
    store_data_in_gcs(local_parquet_file, GCS_BUCKET, GCS_PATH)


api_start_process()
