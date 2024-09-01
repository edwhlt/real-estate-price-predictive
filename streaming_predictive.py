import logging

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.pandas.functions import pandas_udf, PandasUDFType
from pyspark.sql.types import StructType, StructField, DoubleType, StringType, FloatType, IntegerType
from pyspark.ml import PipelineModel
import googlemaps
import math
from pyspark.sql.functions import from_json, col, udf, struct, to_json


# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Spark session
spark = SparkSession.builder \
    .appName("RealEstatePricePredictionStreaming") \
    .getOrCreate()

# Load the pre-trained model
model = PipelineModel.load("model")

# Initialize Google Maps API client
gmaps = googlemaps.Client(key='AIzaSyC5edf5dvJKCXqbNVtBmyKviVZvfaHRRDY')

def degrees_to_radians(degrees):
    return degrees * math.pi / 180

def get_lat_long(address):
    geocode_result = gmaps.geocode(address)
    if geocode_result:
        location = geocode_result[0]['geometry']['location']
        return location['lat'], location['lng']
    else:
        return None, None

# Define the schema for incoming data
schema = StructType([
    StructField("surface_reelle_bati", DoubleType(), True),
    StructField("type_local", StringType(), True),
    StructField("adresse", StringType(), True)
])

# Create a streaming DataFrame from Kafka
streaming_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "real_estate_topic") \
    .option("startingOffsets", "latest") \
    .load()

# Parse the JSON data from Kafka
json_df  = streaming_df.selectExpr("CAST(value AS STRING) as json_string") \
    .withColumn("data", from_json(col("json_string"), schema)).select("data.*")

# Preprocess the addresses outside the UDF
def preprocess_data(surface_reelle_bati, type_local, adresse):
    latitude, longitude = get_lat_long(adresse)
    if latitude is None or longitude is None:
        logging.error(f"Could not geocode address: {adresse}")
        return surface_reelle_bati, type_local, None, None

    latitude_r = degrees_to_radians(latitude)
    longitude_r = degrees_to_radians(longitude)
    return surface_reelle_bati, type_local, latitude_r, longitude_r

# Register the preprocessing function as a UDF
@udf(returnType=StructType([
    StructField("surface_reelle_bati", DoubleType(), True),
    StructField("type_local", StringType(), True),
    StructField("latitude_r", DoubleType(), True),
    StructField("longitude_r", DoubleType(), True)
]))
def preprocess_data_udf(surface_reelle_bati, type_local, adresse):
    return preprocess_data(surface_reelle_bati, type_local, adresse)

def process_batch(batch_df, batch_id):

    logging.info(f"Processing batch {batch_id}")
    batch_df.show()

    preprocessed_df = batch_df.withColumn("preprocessed", preprocess_data_udf(
        col("surface_reelle_bati"),
        col("type_local"),
        col("adresse")
    ))

    # Extract preprocessed columns
    preprocessed_df = preprocessed_df.select(
        col("preprocessed.surface_reelle_bati").alias("surface_reelle_bati"),
        col("preprocessed.type_local").alias("type_local"),
        col("preprocessed.latitude_r").alias("latitude_r"),
        col("preprocessed.longitude_r").alias("longitude_r")
    )

    # Perform prediction
    new_test_data = preprocessed_df
    predictions_df = model.transform(new_test_data)
    # Convert prediction to struct before applying to_json
    result_df = predictions_df.withColumn("prediction_struct", struct(col("prediction").alias("prediction")))

    logging.info("Predictions:")
    result_df.show()

    # Optionally, write the results back to Kafka or another sink
    result_df.select(to_json(col("prediction_struct")).alias("value")) \
        .write \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("topic", "real_estate_response_topic") \
        .save()

# Apply the foreachBatch function
query = json_df.writeStream \
    .foreachBatch(process_batch) \
    .start()

query.awaitTermination()