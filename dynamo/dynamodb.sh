#!/bin/bash

aws cloudformation deploy \
    --region us-east-2 \
    --stack-name votanet-dev-dynamodb-stack \
    --template-file ./dynamodb-votanet.yml \
    --parameter-overrides DynamoName="votanet-dev-voters" DynamoKey="cc"