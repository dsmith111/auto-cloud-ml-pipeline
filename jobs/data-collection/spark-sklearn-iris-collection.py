from pyspark.sql import SparkSession
from sklearn.datasets import load_iris
import pandas as pd
from pyspark.sql.functions import current_timestamp
from pyspark.sql import DataFrame as SparkDataFrame

def extract_data(spark: SparkSession):
    # Pull the Iris dataset from scikit-learn
    data = load_iris()
    data_features = pd.DataFrame(data.data, columns=data.feature_names)
    data_targets = pd.DataFrame(data.target, columns=["target"])
    full_dataset = pd.concat([data_features, data_targets], axis=1)

    # Convert the Pandas DataFrame to a Spark DataFrame
    spark_dataset = spark.createDataFrame(full_dataset)

    return spark_dataset

def transform_data(spark_df: SparkDataFrame):
    # Add a timestamp column to the data
    spark_df = spark_df.withColumn("timestamp", current_timestamp())
    return spark_df

def load_data(spark: SparkSession, spark_df: SparkDataFrame):
    # Database connection details from Spark configuration
    server_url = spark.conf.get("vars.sql.server")
    port = spark.conf.get("vars.sql.port", "1433")
    database_name = spark.conf.get("vars.sql.database")
    table_name = spark.conf.get("vars.sql.tableName", "dbo.iris_data")
    username = spark.conf.get("vars.sql.username")
    password = spark.conf.get("vars.sql.password")

    database_url = f"jdbc:sql://{server_url}:{port};databaseName={database_name}"

    # Write the Spark DataFrame to the Azure SQL Database table
    spark_df.write \
        .format("jdbc") \
        .option("url", database_url) \
        .option("dbtable", table_name) \
        .option("user", username) \
        .option("password", password) \
        .option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver") \
        .mode("overwrite") \
        .save()

def main():
    # Create a Spark session
    spark = SparkSession.builder.appName("SparkSklearnIrisCollection").getOrCreate()

    # Extract the data from scikit-learn and load it into the Azure SQL Database
    data = extract_data(spark)
    transformed_data = transform_data(data)
    load_data(spark, transformed_data)

    # Stop the Spark session
    spark.stop()

if __name__ == "__main__":
    main()
