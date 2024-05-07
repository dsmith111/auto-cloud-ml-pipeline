#!/bin/bash

AIRFLOW_DIRECTORY="$INFRASTRUCTURE_DIRECTORY/airflow"

helm repo add apache-airflow https://airflow.apache.org
helm upgrade --install airflow apache-airflow/airflow --namespace airflow --create-namespace --values "$AIRFLOW_DIRECTORY/values.yaml"
kubectl apply -f "$AIRFLOW_DIRECTORY/airflow-volume.yaml"
