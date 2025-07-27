from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_sagemaker as sagemaker,
)
from constructs import Construct

from sagemaker.lambda_helper import Lambda
from sagemaker.workflow.lambda_step import LambdaStep, LambdaOutput, LambdaOutputTypeEnum
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.pipeline_context import PipelineSession


class ModelPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        pipeline_role = iam.Role(
            self,
            "PipelineRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess")],
        )

        fetch_lambda = _lambda.Function(
            self,
            "FetchLatestModel",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="fetch_latest_model.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "MODEL_PACKAGE_GROUP_NAME": self.node.try_get_context("model_package_group_name") or "MyModelGroup"
            },
        )
        fetch_lambda.add_to_role_policy(
            iam.PolicyStatement(actions=["sagemaker:ListModelPackages"], resources=["*"])
        )

        deploy_lambda = _lambda.Function(
            self,
            "DeployModel",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="deploy_model.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={"SAGEMAKER_ROLE": pipeline_role.role_arn},
        )
        deploy_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "sagemaker:CreateModel",
                    "sagemaker:CreateEndpointConfig",
                    "sagemaker:CreateEndpoint",
                    "sagemaker:UpdateEndpoint",
                ],
                resources=["*"],
            )
        )

        sm_session = PipelineSession()

        fetch_lambda_sdk = Lambda(
            function_name=fetch_lambda.function_name,
            execution_role_arn=fetch_lambda.role.role_arn,
            session=sm_session,
            handler="fetch_latest_model.handler",
        )

        fetch_step = LambdaStep(
            name="FetchApprovedModel",
            lambda_func=fetch_lambda_sdk,
            outputs=[
                LambdaOutput("ModelPackageArn", LambdaOutputTypeEnum.String),
                LambdaOutput("ModelName", LambdaOutputTypeEnum.String),
                LambdaOutput("EndpointConfigName", LambdaOutputTypeEnum.String),
                LambdaOutput("EndpointName", LambdaOutputTypeEnum.String),
            ],
        )

        deploy_lambda_sdk = Lambda(
            function_name=deploy_lambda.function_name,
            execution_role_arn=deploy_lambda.role.role_arn,
            session=sm_session,
            handler="deploy_model.handler",
        )

        deploy_step = LambdaStep(
            name="DeployModel",
            lambda_func=deploy_lambda_sdk,
            inputs={
                "ModelPackageArn": fetch_step.properties.Outputs["ModelPackageArn"],
                "ModelName": fetch_step.properties.Outputs["ModelName"],
                "EndpointConfigName": fetch_step.properties.Outputs["EndpointConfigName"],
                "EndpointName": fetch_step.properties.Outputs["EndpointName"],
            },
        )

        pipeline = Pipeline(
            name="ModelDeploymentPipeline",
            steps=[fetch_step, deploy_step],
            sagemaker_session=sm_session,
            role=pipeline_role,
        )

        sagemaker.CfnPipeline(
            self,
            "ModelDeploymentPipeline",
            pipeline_name="ModelDeploymentPipeline",
            role_arn=pipeline_role.role_arn,
            pipeline_definition=pipeline.definition(),
        )
