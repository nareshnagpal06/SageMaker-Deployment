import os
import boto3

REGION = os.environ.get("SAGEMAKER_REGION")
sagemaker = (
    boto3.client("sagemaker", region_name=REGION)
    if REGION
    else boto3.client("sagemaker")
)
MODEL_PACKAGE_GROUP_NAME = os.environ["MODEL_PACKAGE_GROUP_NAME"]


def handler(event, context):
    response = sagemaker.list_model_packages(
        ModelPackageGroupName=MODEL_PACKAGE_GROUP_NAME,
        ModelApprovalStatus="Approved",
        SortBy="CreationTime",
        SortOrder="Descending",
        MaxResults=1,
    )
    packages = response.get("ModelPackageSummaryList", [])
    if not packages:
        raise Exception("No approved models found")

    model_package_arn = packages[0]["ModelPackageArn"]
    name_part = model_package_arn.split("/")[-1]
    return {
        "ModelPackageArn": model_package_arn,
        "ModelName": f"{name_part}-model",
        "EndpointConfigName": f"{name_part}-config",
        "EndpointName": f"{name_part}-endpoint",
    }
