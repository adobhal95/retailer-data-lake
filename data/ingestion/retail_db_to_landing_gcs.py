from google.cloud import storage, bigquery
import pandas as pd
from pyspark.sql import SparkSession
import datetime
import json


from typing import Optional, Union


# initialize spark session
spark = (
    SparkSession.builder.appName("RetailerDataToGCSLanding")
    .config("spark.jars.packages", "org.postgresql:postgresql:42.7.7")
    .config("spark.sql.adaptive.enabled", "true")
    .getOrCreate()
)


# google cloud storage config variables
GCS_BUCKET = "retailer-datalake"
# path: bucketname/landing/retailer-db/table-name/table_name_DDMMYYYY.json
LANDING_PATH = f"gs://{GCS_BUCKET}/landing/retailer-db/"
# store previous day data in a heirarchical format
# archive/YYYY/MM/DD/table-name/table_name_DDMMYYYY.json
ARCHIVE = f"gs://{GCS_BUCKET}/landing/retailer-db/archive/"
# where metadata about our tables are stored
# whether to load them in incr or full load pattern
CONFIG_FILE_PATH = f"gs://{GCS_BUCKET}/configs/retail_config.csv"


# bigquery configuration
BIGQUERY_PROJECT = "<YOUR-PROJECT-ID>"
BQ_AUDIT_TABLE = f"{BIGQUERY_PROJECT}.temp_dataset.audit_log"
BQ_PIPELINE_LOGS = f"{BIGQUERY_PROJECT}.temp_dataset.pipeline_logs"
BQ_TEMP_PATH = f"{GCS_BUCKET}/temp/"


# PostgreSQL JDBC Configuration
POSTGRES_CONFIG = {
    "url": "jdbc:postgresql://34.131.208.15:5432/retailer_db",
    "driver": "org.postgresql.Driver",
    "user": "retailer_user",
    "password": "pass123",
}


# initialize gcs and bigquery clients
storage_client = storage.Client()
bigquery_client = bigquery.Client()


# logging mechanism
log_entries = []  # stores logs before writing to gcs


def log_event(event_type: str, message: str, table_name: Optional[str] = None):
    """
    Logs an pipeline event to the log list.

    Args:
        event_type (str): The type/category of the event ("INFO", "ERROR", "SUCCESS").
        msg (str): The log message to be recorded.
        table_name (Optional[str], optional): The name of the related table, if applicable.
    Returns:
        None
    """
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "event_type": event_type,
        "message": message,
        "table": table_name,
    }
    log_entries.append(log_entry)
    print(f"[{log_entry['timestamp']}] {event_type} - {message}")


def read_config_file(file_path: str):
    """
    Read config file for metadata about the current table

    Args:
        file_path (str): Location of the file path in gcs bucket
    Returns:
        Spark DataFrame
    """
    try:
        df = (
            spark.read.format("csv")
            .option("header", "true")
            .option("inferSchema", "true")
            .load(file_path)
        )
        log_event("INFO", "successfully read the config file")
        return df
    except Exception as e:
        log_event("ERROR", f"Error reading file: {str(e)}")
        return None


def move_existing_files_to_archive(table_name: str, target_path: str):
    """
    Moves the existing(previous day) files to the archive.
    archive structure:
        archive
        |______YYYY
        |__________MM
        |____________DD
        |______________table_name_DDMMYYY.json
    Args:
        table_name (str): name of the table
    Returns:
        None
    """
    # get the blobs from the gcs landing folder
    bucket = storage_client.bucket(GCS_BUCKET)
    blobs = bucket.list_blobs(prefix=f"{target_path}/")
    existing_files = [blob.name for blob in blobs if blob.name.endswith(".json")]
    if not existing_files:
        log_event("INFO", f"No existing files for table {table_name}")
        return
    for file in existing_files:
        # extract the json file from the folder
        source_blob = bucket.blob(file)

        # extract date from the file name
        date_part = file.split("_")[-1].split(".")[
            0
        ]  # ex: ../../products_12062025.json -> 12062025
        year, month, day = date_part[-4:], date_part[2:4], date_part[:2]

        # move the file in archive folder
        archive_path = f"landing/retailer-db/archive/{table_name}/{year}/{month}/{day}/{file.split('/')[-1]}"
        destination_blob = bucket.blob(archive_path)

        # copy the original blob from the source folder to the destination folder
        bucket.copy_blob(source_blob, bucket, destination_blob.name)
        source_blob.delete()

        log_event("INFO", f"Moved {file} to {archive_path}", table_name=table_name)


def get_latest_watermark(table_name: str):
    """
    Get the latest watermark(updated_at field for a table) frpm the audit_table in bigquery.
    Args:
        table_name (str): name of the table
    Returns:
        Union[datetime.datetime, str]
    """
    query = f"""
    SELECT MAX(load_timestamp) as latest_timestamp
    from `{BQ_AUDIT_TABLE}`
    where tablename = '{table_name}'
    """
    job = bigquery_client.query(query)
    result = job.result()
    for row in result:
        return row.latest_timestamp if row.latest_timestamp else "1900-01-01 00:00:00"
    return "1900-01-01 00:00:00"


def extract_and_save_to_landing_gcs(
    table_name: str, load_type: str, watermark_col: str, target_path: str
):
    """
    Loads the data for the current date in json format to gcs landing folder
    Args:
        table_name (str): name of the table
        load_type (str): whether the table is incremental or full load type
        watermark_col: field which defines the latest load time of the data
    Returns:
        None
    """
    log_event(
        "INFO",
        f"Starting data extraction for table: {table_name} (Load Type: {load_type})",
        table_name=table_name,
    )
    try:
        # get latest watermark
        last_watermark = None
        query = None
        if load_type.lower() == "incremental":
            last_watermark = get_latest_watermark(table_name=table_name)
            log_event(
                "INFO",
                f"Last watermark for {table_name}:{last_watermark}",
                table_name=table_name,
            )
            # query based on load type = incremental
            query = f"(SELECT * FROM {table_name} WHERE {watermark_col} > '{last_watermark}') as t"
        else:
            # query based on load type = full load
            query = f"(SELECT * FROM {table_name}) as t"
        # read data from cloud sql(postgresql) table
        print(query)
        table_df = (
            spark.read.format("jdbc")
            .option("url", POSTGRES_CONFIG["url"])
            .option("dbtable", query)
            .option("user", POSTGRES_CONFIG["user"])
            .option("password", POSTGRES_CONFIG["password"])
            .option("driver", POSTGRES_CONFIG["driver"])
            .load()
        )
        log_event(
            "SUCCESS",
            f"successfully extracted data from {table_name}",
            table_name=table_name,
        )
        # convert spark df -> json type
        pandas_dataframe = table_df.toPandas()
        json_data = pandas_dataframe.to_json(orient="records", lines=True)

        # json file path in gcs
        today = datetime.datetime.today().strftime("%d%m%Y")
        JSON_FILE_PATH = f"{target_path}/{table_name}_{today}.json"

        # upload json data to gcs
        bucket = storage_client.bucket(GCS_BUCKET)
        blob = bucket.blob(JSON_FILE_PATH)
        blob.upload_from_string(json_data, content_type="application/json")
        log_event(
            "SUCCESS",
            f"JSON file successfully written to gs://{GCS_BUCKET}/{JSON_FILE_PATH}",
            table_name=table_name,
        )

        # add entry in audit table
        # add current ingestion timestamp for current table
        audit_df = spark.createDataFrame(
            [
                (
                    table_name,
                    load_type.lower(),
                    table_df.count(),
                    datetime.datetime.now(),
                    "SUCCESS",
                )
            ],
            ["tablename", "load_type", "record_count", "load_timestamp", "status"],
        )
        (
            audit_df.write.format("bigquery")
            .option("table", BQ_AUDIT_TABLE)
            .option("temporaryGcsBucket", GCS_BUCKET)
            .mode("append")
            .save()
        )
        log_event(
            "SUCCESS",
            f"audit log updated for {table_name} at {datetime.datetime.now()}",
            table_name=table_name,
        )
    except Exception as e:
        log_event(
            "ERROR",
            f"fn_extract_and_save_to_landing_gcs error processing {table_name}: {str(e)}",
            table_name=table_name,
        )


def save_logs_to_gcs():
    """
    Save the current pipeline logs to gcs
    Returns:
        None
    """
    log_filename = (
        f"retail_pipeline_log_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    )
    log_file_path = f"temp/pipeline_logs/{log_filename}"
    json_data = json.dumps(log_entries, indent=4)
    # gcs bucket
    bucket = storage_client.bucket(GCS_BUCKET)
    blob = bucket.blob(log_file_path)
    # upload file to bucket
    blob.upload_from_string(json_data, content_type="application/json")
    print(f"logs successfully saved to GCS at gs://{GCS_BUCKET}/{log_file_path}")


def save_logs_to_bigquery():
    """
    Save the current pipeline logs to bigquery
    Returns:
        None
    """
    if log_entries:
        log_df = spark.createDataFrame(log_entries)
        log_df.write.format("bigquery").option("table", BQ_PIPELINE_LOGS).option(
            "temporaryGcsBucket", BQ_TEMP_PATH
        ).mode("append").save()
        print(f"logs stored in BigQuery table: {BQ_PIPELINE_LOGS}")


# main_process execution
def main_process():
    log_event("INFO", "Started data ingestion process")
    config_df = read_config_file(CONFIG_FILE_PATH)
    for row in config_df.collect():
        if row["is_active"] == 1:
            db, db_src, table, load_type, watermark, is_active, target_path = row
            move_existing_files_to_archive(
                table_name=table, target_path=target_path
            )  # shift the existing file to archive folder
            extract_and_save_to_landing_gcs(
                table_name=table,
                load_type=load_type,
                watermark_col=watermark,
                target_path=target_path,
            )
    # save logs in gcs and bigquery
    save_logs_to_gcs()
    save_logs_to_bigquery()
    print("Done")


main_process()
