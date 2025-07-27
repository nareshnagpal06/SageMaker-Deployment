#!/usr/bin/env python3
import aws_cdk as cdk
from model_pipeline_stack import ModelPipelineStack

app = cdk.App()
ModelPipelineStack(app, "ModelPipelineStack")
app.synth()
