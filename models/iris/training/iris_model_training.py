import pyarrow.parquet as pq
import pandas as pd
import os
import glob
import torch.distributed as dist
import argparse
from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient
import iris_model_class
import iris_dataset_class


def print_header(phrase: str):
    print(f"\n\n{'*'*10} {phrase} {'*'*10}\n\n")


def loadDataLake(account_name: str):
    print_header("Loading Data Lake")
    account_url = f"https://{account_name}.dfs.core.windows.net"
    default_credential = DefaultAzureCredential()
    datalake_service_client = DataLakeServiceClient(account_url, credential=default_credential)
    return datalake_service_client


def createModel(input_size, output_size):
    model = iris_model_class.Classifier(input_size, output_size)
    return model


def loadModel(datalake_service_client: DataLakeServiceClient, input_size: int, output_size: int, use_pretrained: bool = False):
    import torch

    print_header("Loading Model")

    model = createModel(input_size, output_size)

    if use_pretrained:
        # Load model from azure data lake
        file_system_name = 'distributed-test-models'
        file_path = 'iris-models/model.pt'

        file_system_client = datalake_service_client.get_file_system_client(file_system_name)
        file_client = file_system_client.get_file_client(file_path)

        with open("model_weights.pt", "wb") as download_file:
            download_file.write(file_client.download_file().readall())

        # Load model into memory
        model.load_state_dict(torch.load("model_weights.pt"))

    return model


def downloadDataset(local_directory_path, datalake_service_client: DataLakeServiceClient):
    print_header("Downloading Dataset")
    try:
        # Load dataset from azure data lake
        file_system_name = 'distributed-test-tabular'
        file_path = 'iris-data/raw/iris'

        print(f"Downloading dataset from {file_system_name}/{file_path}")
        file_system_client = datalake_service_client.get_file_system_client(file_system=file_system_name)
        paths = file_system_client.get_paths(path=file_path)
        
        # Create the local directory if it doesn't exist
        os.makedirs(local_directory_path, exist_ok=True)

        for path in paths:
            if path["name"].endswith('.parquet'):
                print(f"Downloading file: {path['name']}")
                file_client = file_system_client.get_file_client(path["name"])
                local_file_path = os.path.join(local_directory_path, os.path.basename(path["name"]))
                with open(local_file_path, "wb") as f:
                    download = file_client.download_file()
                    f.write(download.readall())
                print(f"Downloaded file: {local_file_path}")

    except Exception as e:
        print(f"Error downloading file: {e}")
        raise e


def loadDataset(local_directory_path):
    print_header("Loading Dataset")
    try:
        files = glob.glob(os.path.join(local_directory_path, '*.parquet'))
        df = pd.concat([pq.read_table(file).to_pandas() for file in files], ignore_index=True)
        return df

    except Exception as e:
        print(f"Error loading file: {e}")


def run_training_epoch(model, loader, optimizer, criterion, device, epoch):
    for batch_idx, (features, target) in enumerate(loader):
        features = features.to(device)
        target = target.to(device)

        optimizer.zero_grad()
        output = model(features)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()
    # losses.append(loss.item())
    # if epoch % 100 == 0:
    #     print(f"Epoch {epoch} Loss: {losses[-1]}")


def train_model(model, loader, device, learning_rate: float):
    import torch

    print_header("Training Model")
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = torch.nn.CrossEntropyLoss()
    model.train()

    # losses = []
    max_epochs = 100
    for epoch in range(max_epochs):
        print(f"Epoch {epoch}/{max_epochs}")
        run_training_epoch(model, loader, optimizer, criterion, device, epoch)


def upload_model(datalake_client: DataLakeServiceClient, local_file_path: str, lake_directory_path: str, config_path: str):
    print_header("Uploading Model")
    file_system_name = 'distributed-test-models'
    lake_file_path = os.path.join(lake_directory_path, "model-store", os.path.basename(local_file_path))

    # Create the file system if it doesn't exist
    try:
        datalake_client.create_file_system(file_system_name)
    except Exception as e:
        print(f"File system {file_system_name} already exists")
    
    file_system_client = datalake_client.get_file_system_client(file_system_name)
    file_client = file_system_client.get_file_client(lake_file_path)

    with open(local_file_path, "rb") as f:
        file_client.upload_data(f, overwrite=True)
        print(f"Uploaded model: {lake_file_path}")

    if config_path:
        # Upload the config.properties file to the ./config directory
        config_file_path = os.path.join(lake_directory_path, "config", "config.properties")
        config_file_client = file_system_client.get_file_client(config_file_path)

        with open(config_path, "rb") as f:
            config_file_client.upload_data(f, overwrite=True)
            print(f"Uploaded config: {config_file_path}")
    


def export_model(datalake_client: DataLakeServiceClient, model: iris_model_class.Classifier, handler_file_path: str, config_path: str, lake_directory_path: str):
    import torch
    import subprocess

    print_header("Exporting Model")

    # Extract the underlying model from DDP wrapper
    model = model.module

    # Save model weights for future experiments
    weights_name = "iris_model_weights.pt"
    torch.save(model.state_dict(), weights_name)

    # Convert the model to TorchScript
    scripted_model = torch.jit.script(model)
    scripted_model.save("iris_model_scripted.pt")

    # Create a Torch model archive (.mar file) for the TorchScript file
    model_archive_name = "iris_model.mar"

    # Create the TorchServe expected directory structure ./model-store and ./config
    os.makedirs("model-store", exist_ok=True)
    os.makedirs("config", exist_ok=True)

    archive_output = subprocess.run([
        "torch-model-archiver",
        "--model-name", "iris_model",
        "--version", "1.0",
        "--serialized-file", "iris_model_scripted.pt",
        "--handler", handler_file_path,
        "--export-path", "./model-store",
        "--force"
    ], capture_output=True)

    # Copy the config.properties file to the ./config directory
    subprocess.run(["cp", config_path, "config"])

    # Raise an exception if the model archiver fails
    archive_output.check_returncode()

    # Upload the model archive and weights to Azure Data Lake
    upload_model(datalake_client, model_archive_name, lake_directory_path + "/mar", config_path)
    upload_model(datalake_client, weights_name, lake_directory_path + "/weights")


def distributed_train(learning_rate, use_gpu, account_name):
    import torch
    from torch.nn.parallel import DistributedDataParallel as DDP
    from torch.utils.data import DistributedSampler, DataLoader

    print_header("Distributed Training")

    datalake_client = loadDataLake(account_name)

    device = torch.device(f"cuda:{os.environ['LOCAL_RANK']}" if use_gpu else "cpu")

    # Download, load and prepare dataset
    downloadDataset("./dataset", datalake_client)
    dataset = loadDataset("./dataset")
    iris_dataset = iris_dataset_class.IrisDataset(dataset, "target")

    sampler = DistributedSampler(iris_dataset)
    loader = DataLoader(iris_dataset, sampler=sampler, batch_size=64)
    
    # Load untrained or pretrained model
    model = loadModel(datalake_client, dataset.columns.shape[0] - 1, 3, use_pretrained=False).to(device)
    model = DDP(model, device_ids=[device] if use_gpu else None)

    train_model(model, loader, device, learning_rate)


    current_directory = os.path.curdir
    handler_path = os.path.join(current_directory, "iris_model_serve_handler.py")
    config_path = os.path.join(current_directory, "config.properties")

    export_model(datalake_client, model, handler_path, config_path, "iris_models")

    dist.destroy_process_group()


def main():
    print_header("Configuring Distributed Training")
    parser = argparse.ArgumentParser()
    parser.add_argument("--learning_rate", type=float, default=0.001)
    parser.add_argument("--use_gpu", action='store_true', default=False)
    parser.add_argument("--account_name", type=str, required=True)
    args = parser.parse_args()

    backend = "nccl" if args.use_gpu else "gloo"
    dist.init_process_group(backend)

    distributed_train(args.learning_rate, args.use_gpu, args.account_name)
    

if __name__ == "__main__":
    main()