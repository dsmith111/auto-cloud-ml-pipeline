# End to End AI Management Infrastructure

This project aims to provide a comprehensive infrastructure for managing end-to-end AI workflows, leveraging technologies like Airflow, Kubeflow, PyTorch, and Azure services. The directory structure is organized as follows:

## Directory Structure

- `notebooks`: Contains Jupyter notebooks for exploratory data analysis and experimentation.
  - `manual_pipeline_triggers.ipynb`: Notebook to cover the DAG that will be handled by Airflow
- `infrastructure`:
  - `dashboard`: Configuration files for monitoring and dashboard tools.
  - `debugging`: Tools and configurations for debugging cluster issues.
  - `deployment`:
    - `airflow`: Helm chart value file and script for deploying Airflow.
    - `azure`: Azure Bicep files for provisioning cloud resources.
    - `kubeflow`: Kustomization setup with a bash script for deploying Kubeflow components.
      - `general`: General Kubeflow configurations.
      - `manifests`: Kubeflow manifests for various components.
      - `serve`: Configurations for serving models with Kubeflow.
      - `train`: Configurations for training models with Kubeflow.
    - `pod-identity`: Kustomization setup with a bash script for syncing deployment with Pod Identity Helm charts.
      - `base`: Base configurations for pod identity.
      - `spark`: Configurations for Spark integration with pod identity.
      - `train`: Configurations for training jobs with pod identity.
      - `serve`: Configurations for serving models with pod identity.
    - `spark`: Network, RBAC and service resources for preparing our cluster for Spark jobs.
- `jobs`:
  - `data-collection`: Python files for pulling data from various sources, structuring them and storing them in our data storage.
  - `data-processing`: Python files for Spark implementations of data processing tasks.
- `models`: Python files for PyTorch model training and serving. Models will be training (pulled from Azure storage if we're using saved weights), the weights and model script will be saved separately and both uploaded to an Azure Data Lake. We will also have the Dockerfile here for containerizing the model if it's valid.
  - `iris`: Dataset and Model class, Model serving handler for TorchServe/KFServe, Training file for distributed PyTorch training.
- `pipeline`:
  - `airflow`: Airflow DAGs for orchestrating the end-to-end workflow.
  - `kubeflow`:
    - `pytorchjobs`: YAML files for PyTorch training jobs.
    - `kserve`: YAML files for inferencing services using KServe.

## ML End-to-End Architecture

The workflow is orchestrated using Airflow and consists of the following steps:

1. **Data Ingestion**: Check for "new" data from sources. If there is new data, proceed to the next step.
2. **Data Processing**: Submit a Spark job to process and add structure to the new data, and store it in Azure Data Lake Gen2 as a Parquet file.
3. **Model Training**: Use a PyTorchJob to pull data and either create a model or load a pretrained model, and train the distributed Torch model. Store the trained model's weights and torch script form in the data lake and record model metadata (e.g., accuracy) in an Azure table.
4. **Model Validation/Build**: Validate the trained model. If there is significant drift, fire an alert for human intervention. If the model is valid, build and push the model, then proceed to the next step.
5. **Model Deployment**: Deploy the validated model using Kubeflow Serve for inferencing.

The infrastructure is deployed across three distinct AKS clusters to isolate resources and allow distinct updates:
- **Data Processing Cluster**: Uses weaker machines for initial data processing.
- **Training Cluster**: Equipped with a GPU node pool, set to scale to 0 nodes when not in use to save costs.
- **Serving Cluster**: Utilizes weak to medium nodes depending on the inferencing requirements.

Relevant Kubeflow components are deployed only to the clusters where they are needed, ensuring a clean separation of concerns.

## Usage

To set up and deploy the infrastructure, follow these steps:

1. **Deploy Infrastructure**: Run the `deploy-infrastructure.sh` script located in the `infrastructure/deployment` directory. This script will create and deploy all necessary resources for the AI infrastructure. It requires a subscription ID as an input parameter.

    ```bash
    cd infrastructure/deployment
    ./deploy-infrastructure.sh <subscription-id>
    ```

    The script will create resource groups, deploy Azure Bicep resources (including AKS clusters and storage resources), and configure pod identities and access permissions for each cluster.

2. **Configure Airflow, Kubeflow, and Spark**: Follow the additional setup instructions for Airflow, Kubeflow, and Spark resources as outlined in their respective directories.

(TODO: Add more detailed usage instructions.)
