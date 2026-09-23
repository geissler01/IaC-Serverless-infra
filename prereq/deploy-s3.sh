#!/bin/bash

aws cloudformation deploy \
    --region us-east-2 \
    --stack-name votanet-dev-s3-stack \
    --template-file ./bucket-s3.yml