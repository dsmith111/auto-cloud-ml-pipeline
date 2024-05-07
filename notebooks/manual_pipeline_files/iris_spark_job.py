from pyspark.sql import SparkSession
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient
import os

# Load the Iris dataset from the IRIS_CSV_PATH passed in by the docker container
data = pd.read_csv(os.environ["IRIS_CSV_PATH"], header='infer')
data['species'] = data['species'].astype('category')
data['species'] = data['species'].cat.codes
full_dataset = data.rename(columns={'species': 'target'}, inplace=False)

# Spark session configuration
spark = SparkSession.builder \
    .appName("spark-dist-training") \
    .getOrCreate()

# Create the file system if it does not exist
# account_url = "https://<spark.account.name>.dfs.core.windows.net" get from spark config
account_name = spark.conf.get("spark.account.name")
data_filesystem = spark.conf.get("spark.account.datafilesystem")
account_url = f"https://{account_name}.dfs.core.windows.net"
default_credential = DefaultAzureCredential()
datalake_service_client = DataLakeServiceClient(account_url, credential=default_credential)
try:
    datalake_service_client.create_file_system(data_filesystem)
except Exception as e:
    if e.__class__.__name__ == "ResourceExistsError":
        print("Resource already exists")
    else:
        raise e

# Write the dataset to Azure Data Lake
spark_dataset = spark.createDataFrame(full_dataset)
path = f"abfss://{data_filesystem}@{account_name}.dfs.core.windows.net/iris-data/raw/iris"
spark_dataset.write.mode("overwrite").parquet(path)

spark.stop()
