# real-estate-price-predictive

## Project Description

```bash
docker cp streaming_predictive.py spark-notebook:/home/jovyan

docker cp files/model spark-notebook:/home/jovyan

spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.2 streaming_predictive.py
```