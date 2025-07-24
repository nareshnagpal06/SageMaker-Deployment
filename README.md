# SageMaker Model Deployment CDK Example

This repository contains an example AWS CDK stack that demonstrates how to
retrieve an approved model from the SageMaker Model Registry and deploy it to a
SageMaker endpoint on the new unified Studio platform.

The stack performs the following actions:

1. Uses a Lambda function to list the latest approved model package from a model
   package group.
2. Deploys the model by creating the SageMaker model, endpoint configuration and
   endpoint through AWS Step Functions.
3. Creates a new SageMaker Domain configured for the unified Studio experience.

## Getting Started

Install the Python dependencies:

```bash
pip install -r cdk/requirements.txt
```

Synthesize the CloudFormation templates:

```bash
cdk synth -a cdk/app.py
```

Deploy the stack (make sure you have configured your AWS credentials):

```bash
cdk deploy -a cdk/app.py
```

The model package group name can be provided via CDK context:

```bash
cdk deploy -a cdk/app.py -c model_package_group_name=MyModelGroup
```
