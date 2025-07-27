import os
import boto3

sagemaker = boto3.client("sagemaker")
ROLE = os.environ["SAGEMAKER_ROLE"]


def handler(event, context):
    arn = event["ModelPackageArn"]
    model_name = event["ModelName"]
    config_name = event["EndpointConfigName"]
    endpoint_name = event["EndpointName"]

    sagemaker.create_model(
        ModelName=model_name,
        ExecutionRoleArn=ROLE,
        Containers=[{"ModelPackageName": arn}]
    )

    sagemaker.create_endpoint_config(
        EndpointConfigName=config_name,
        ProductionVariants=[{
            "ModelName": model_name,
            "InitialInstanceCount": 1,
            "InstanceType": "ml.m5.large",
            "VariantName": "AllTraffic",
        }]
    )

    try:
        sagemaker.create_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=config_name,
        )
    except sagemaker.exceptions.ClientError as e:
        if "Endpoint already exists" in str(e):
            sagemaker.update_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=config_name,
            )
        else:
            raise

    return {"EndpointName": endpoint_name}
