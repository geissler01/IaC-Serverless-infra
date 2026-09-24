#!/usr/bin/env bash

set -e

STACK_NAME="votanet-dev-pipeline-stack"
TEMPLATE_FILE="pipeline.yml"
REGION="us-east-2"

echo "=== Desplegando Pipeline CI/CD VotaNet en CloudFormation ==="

aws cloudformation deploy \
    --stack-name "$STACK_NAME" \
    --template-file "$TEMPLATE_FILE" \
    --region "$REGION" \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

echo "=== Pipeline desplegado exitosamente ==="

aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs" \
    --output table