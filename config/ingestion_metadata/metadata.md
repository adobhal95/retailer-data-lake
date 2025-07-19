### what tables are in the scope for ingestion

### what is the load type of the table

1. incremental table
   a. if incremental table, then what is the watermark(updated_at field). Most recent data stored timestamp, it will help us in storing only latest data. As data in this table grow expontiatily at large rate, we don't want to ingest whole table at every ingestion time. Only the latest data.
2. full load table
   a. As this table are small can or updated less frequently or not they can be fully loaded.

### Metdata field types

```
database: database name
datasource: cloudsql instance name
tablename: name of the table
loadtype: incremental or full load table
watermark: field which denotes the watermark
is_active: is table active or not
targetpath: final landing path in gcs after pyspark transformation
```
