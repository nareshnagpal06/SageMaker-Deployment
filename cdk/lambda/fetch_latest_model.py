import os
import boto3

sagemaker = boto3.client("sagemaker")
GROUP = os.environ["MODEL_PACKAGE_GROUP_NAME"]


def handler(event, context):
    resp = sagemaker.list_model_packages(
        ModelPackageGroupName=GROUP,
        ModelApprovalStatus="Approved",
        SortBy="CreationTime",
        SortOrder="Descending",
        MaxResults=1,
    )
    packages = resp.get("ModelPackageSummaryList", [])
    if not packages:
        raise Exception("No approved models found")

    arn = packages[0]["ModelPackageArn"]
    name = arn.split("/")[-1]
    return {
        "ModelPackageArn": arn,
        "ModelName": f"{name}-model",
        "EndpointConfigName": f"{name}-config",
        "EndpointName": f"{name}-endpoint",
    }
