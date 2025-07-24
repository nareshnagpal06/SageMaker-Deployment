#!/usr/bin/env python3
import aws_cdk as cdk
from model_deployment_stack import ModelDeploymentStack

app = cdk.App()
ModelDeploymentStack(app, "ModelDeploymentStack")
app.synth()
