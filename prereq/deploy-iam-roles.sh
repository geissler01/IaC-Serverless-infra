#!/bin/bash

# Variables de configuracion
STACK_NAME="votanet-dev-prereq-stack"
REGION="us-east-2"
TEMPLATE_FILE="./iam-roles.yml"

echo "======================================="
echo "Iniciando despliegue de Roles IAM y Politicas de seguridad"
echo "Stack: $STACK_NAME | Region: $REGION"
echo "======================================="

aws cloudformation deploy \
    --region $REGION \
    --stack-name $STACK_NAME \
    --template-file $TEMPLATE_FILE \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

# Si el despliegue fue exitoso ($? == 0), consulta e imprime las salidas exportadas
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================================="
    echo " Despliegue completado con éxito. Outputs exportados:"
    echo "=========================================================="
    aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query "Stacks[0].Outputs[*].{Clave:OutputKey, ARN:OutputValue, ExportName:ExportName}" \
        --output table
else
    echo ""
    echo " Hubo un error al desplegar el stack $STACK_NAME."
fi