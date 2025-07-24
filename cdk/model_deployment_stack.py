from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_sagemaker as sagemaker,
)
from constructs import Construct


class ModelDeploymentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        check_model_lambda = _lambda.Function(
            self,
            "CheckModelLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="check_model_approved.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "MODEL_PACKAGE_GROUP_NAME": self.node.try_get_context(
                    "model_package_group_name"
                )
                or "MyModelGroup",
                "SAGEMAKER_REGION": self.node.try_get_context("model_region")
                or Stack.of(self).region,
            },
        )

        check_model_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["sagemaker:ListModelPackages"], resources=["*"]
            )
        )

        check_model_step = tasks.LambdaInvoke(
            self,
            "CheckApprovedModel",
            lambda_function=check_model_lambda,
            output_path="$.Payload",
        )

        create_model = tasks.CallAwsService(
            self,
            "CreateModel",
            service="sagemaker",
            action="createModel",
            parameters={
                "ModelName.$": "$.ModelName",
                "ExecutionRoleArn": check_model_lambda.role.role_arn,
                "Containers": [{"ModelPackageName.$": "$.ModelPackageArn"}],
            },
            iam_resources=["*"],
        )

        create_config = tasks.CallAwsService(
            self,
            "CreateEndpointConfig",
            service="sagemaker",
            action="createEndpointConfig",
            parameters={
                "EndpointConfigName.$": "$.EndpointConfigName",
                "ProductionVariants": [
                    {
                        "ModelName.$": "$.ModelName",
                        "InitialInstanceCount": 1,
                        "InstanceType": "ml.m5.large",
                        "VariantName": "AllTraffic",
                    }
                ],
            },
            iam_resources=["*"],
        )

        create_endpoint = tasks.CallAwsService(
            self,
            "CreateEndpoint",
            service="sagemaker",
            action="createEndpoint",
            parameters={
                "EndpointName.$": "$.EndpointName",
                "EndpointConfigName.$": "$.EndpointConfigName",
            },
            iam_resources=["*"],
        )

        definition = (
            check_model_step.next(create_model)
            .next(create_config)
            .next(create_endpoint)
        )

        sfn.StateMachine(
            self,
            "ModelDeploymentStateMachine",
            definition=definition,
            timeout=Duration.minutes(30),
        )

        # Example domain for unified Studio
        sagemaker.CfnDomain(
            self,
            "SageMakerDomain",
            auth_mode="IAM",
            default_user_settings=sagemaker.CfnDomain.UserSettingsProperty(
                execution_role=check_model_lambda.role.role_arn
            ),
            domain_name="ml-domain",
        )
