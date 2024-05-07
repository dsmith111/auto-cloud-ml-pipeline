from pyspark.sql import SparkSession
from pyspark.sql import DataFrame as SparkDataFrame
from pyspark.sql.functions import col

def extract_data(spark: SparkSession):
    # Database connection details from Spark configuration
    database_url = spark.conf.get("spark.job.databaseUrl")
    database_name = spark.conf.get("spark.job.databaseName")
    table_name = spark.conf.get("spark.job.tableName")
    username = spark.conf.get("spark.job.username")
    password = spark.conf.get("spark.job.password")

    # Read the data from the Azure SQL Database table
    spark_df = spark.read \
        .format("jdbc") \
        .option("url", f"{database_url};databaseName={database_name}") \
        .option("dbtable", table_name) \
        .option("user", username) \
        .option("password", password) \
        .option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver") \
        .load()

    return spark_df

def transform_data(spark_df: SparkDataFrame):
    # Drop the timestamp column
    spark_df = spark_df.drop("timestamp")

    # Handle null values in features
    for column in spark_df.columns:
        spark_df = spark_df.filter(col(column).isNotNull())

    return spark_df

def load_data(spark: SparkSession, spark_df: SparkDataFrame):
    # Data Lake storage details and partitioning information from Spark configuration
    data_lake_path = spark.conf.get("spark.job.dataLakePath")
    num_partitions = int(spark.conf.get("spark.job.numPartitions", "4"))  # Default to 4 partitions if not specified

    # Repartition the DataFrame into the specified number of partitions
    partitioned_df = spark_df.repartition(num_partitions)

    # Write the partitioned data to Azure Data Lake Gen2 as a parquet file
    partitioned_df.write.mode("overwrite").parquet(data_lake_path)

def main():
    # Create a Spark session
    spark = SparkSession.builder.appName("SparkSklearnIrisProcessing").getOrCreate()

    # Extract data from SQL, transform it, and load it into Azure Data Lake Gen2
    data = extract_data(spark)
    transformed_data = transform_data(data)
    load_data(spark, transformed_data)

    # Stop the Spark session
    spark.stop()

if __name__ == "__main__":
    main()
