import airflow
from airflow import DAG
from datetime import (
    timedelta,
)  # Imports timedelta for defining time durations (e.g., for retry delays).
from airflow.utils.dates import (
    days_ago,
)  # Imports days_ago for setting the start_date dynamically.
from airflow.operators.dagrun_operator import (
    TriggerDagRunOperator,
)  # Imports the operator used to trigger other DAGs.

# Define default arguments for the DAG. These arguments will be applied to all tasks within this DAG
# unless explicitly overridden at the task level.
ARGS = {
    "owner": "abhishek",
    "start_date": days_ago(
        1
    ),  # Sets the DAG's start date to 1 day ago from when the DAG file is parsed.
    # This ensures the DAG can be scheduled immediately upon deployment.
    "depends_on_past": False,  # If True, a DAG run will only start if the previous DAG run completed successfully.
    # Set to False here, meaning each run is independent.
    "retries": 1,  # Number of times a task will retry if it fails.
    "retry_delay": timedelta(
        minutes=5
    ),  # The time interval to wait before retrying a failed task.
}

# Define the parent DAG using a context manager.
with DAG(
    dag_id="parent_dag",
    schedule_interval="0 5 * * *",  # Defines the schedule using a cron expression.
    # "0 5 * * *" means the DAG will run daily at 05:00 AM UTC.
    description="Parent DAG to trigger PySpark and BigQuery DAGs",  # A human-readable description of the DAG.
    default_args=ARGS,  # Applies the previously defined default arguments to this DAG and its tasks.
    tags=[
        "parent",
        "orchestration",
        "etl",
    ],  # Tags help in organizing and filtering DAGs in the Airflow UI.
) as dag:

    # Task to trigger the PySpark DAG.
    # TriggerDagRunOperator is used to programmatically trigger another DAG run.
    trigger_pyspark_dag = TriggerDagRunOperator(
        task_id="trigger_pyspark_dag",  # A unique identifier for this specific task within the parent_dag.
        trigger_dag_id="pyspark_dag",  # The dag_id of the child DAG to be triggered.
        # Airflow will look for a DAG with this ID.
        wait_for_completion=True,  # If True, this task will wait for the triggered child DAG (pyspark_dag)
        # to complete (successfully or failed) before proceeding.
        # If False, it would fire and forget.
    )

    # Task to trigger the BigQuery DAG.
    # This task is similar to the PySpark trigger but targets a different child DAG.
    trigger_bigquery_dag = TriggerDagRunOperator(
        task_id="trigger_bigquery_dag",  # Unique identifier for this task.
        trigger_dag_id="bigquery_dag",  # The dag_id of the child DAG to be triggered.
        wait_for_completion=True,  # Waits for the 'bigquery_dag' to complete before this task is marked as finished.
    )

# Define dependencies between tasks.
# This line sets up a sequential dependency:
# 'trigger_pyspark_dag' must complete successfully before 'trigger_bigquery_dag' can start.
trigger_pyspark_dag >> trigger_bigquery_dag
