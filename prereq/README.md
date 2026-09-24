# Módulo 2: Cimientos de CI/CD y Seguridad (Amazon S3 & AWS IAM)

Este módulo establece los cimientos de gobernanza, seguridad y almacenamiento de artefactos para el pipeline y la función serverless.

---

## Estructura de Archivos

```text
prereq/
├── bucket-s3.yml          # Plantilla CloudFormation del Bucket S3 de Artefactos
├── deploy-s3.sh           # Script de despliegue para el Bucket S3
├── iam-roles.yml          # Plantilla CloudFormation de Roles y Políticas IAM
└── deploy-iam-roles.sh    # Script de despliegue de Seguridad IAM
```

---

## 2.1 Almacenamiento de Artefactos: `bucket-s3.yml`

* **Nombre del Stack:** `votanet-dev-s3-stack`
* **Nombre Físico del Bucket:** `votanet-artefacts-841702867308-us-east-2`

### Configuraciones Enterprise de Seguridad y Costos:
1. **Cifrado en Reposo:** `AES256` (Server-Side Encryption).
2. **Bloqueo Público Total:** `PublicAccessBlockConfiguration` con las 4 directivas en `true` (evita filtraciones accidentales a internet).
3. **Control de Versiones (`VersioningConfiguration`):** Estado `Enabled`. Indispensable para que CodePipeline pueda rastrear y revertir artefactos `.zip`.
4. **Ciclo de Vida (`LifecycleConfiguration`):** Expiración automática y borrado de versiones no actuales tras **30 días** para optimizar costos de almacenamiento.

### Exports Generados:
* `S3ArtifactsBucket`: `votanet-artefacts-841702867308-us-east-2`
* `S3ArtifactsBucketArn`: `arn:aws:s3:::votanet-artefacts-841702867308-us-east-2`

---

## 2.2 Roles y Políticas de Seguridad: `iam-roles.yml`

* **Nombre del Stack:** `votanet-dev-prereq-stack`
* **Capacidades Obligatorias:** `--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM`

### Recursos Creados y Principio de Mínimo Privilegio:

| Recurso Lógico | Tipo de Recurso | Nombre / ARN Físico en AWS | Función Principal |
| :--- | :--- | :--- | :--- |
| **`CodeBuildRole`** | `AWS::IAM::Role` | Dinámico (`votanet-dev-prereq-stack-CodeBuildRole-...`) | Permiso para escribir logs en CloudWatch y subir/descargar artefactos de S3. |
| **`CodePipelineRole`** | `AWS::IAM::Role` | Dinámico (`votanet-dev-prereq-stack-CodePipelineRole-...`) | Orquestar el flujo: disparar builds en CodeBuild, gestionar artefactos en S3 y delegar ejecución a CloudFormation con `iam:PassRole`. |
| **`CloudFormationDeployRole`** | `AWS::IAM::Role` | Fijo: `CloudFormationDeployRole` | Rol asumido por CloudFormation con permisos para crear/actualizar recursos serverless (Lambda, API Gateway). |
| **`LambdaPolicyDynamoDB`** | `AWS::IAM::ManagedPolicy` | Fijo: `LambdaPolicyDynamoDB` | Política gestionada que autoriza lectura/escritura únicamente sobre la tabla importada `!ImportValue DynamoLabArn`. |
| **`LambdaPolicyCW`** | `AWS::IAM::ManagedPolicy` | Fijo: `LambdaPolicyCW` | Política gestionada que autoriza a la Lambda a crear log streams y escribir eventos en `/aws/lambda/*`. |

---

## Conceptos Clave de Seguridad Aprendidos

1. **Separación de Responsabilidades:**
   Las políticas de acceso a la base de datos y a logs se declaran de forma centralizada en este módulo. La aplicación (`app/`) no inventa sus propios permisos, simplemente se "enchufa" a las políticas autorizadas mediante `!ImportValue`.
2. **Portabilidad de Partición:**
   Uso de `arn:${AWS::Partition}:logs:...` en lugar de quemar `arn:aws:logs:...` para garantizar compatibilidad con regiones gubernamentales (`aws-us-gov`) o especiales.
3. **Capabilities de CloudFormation:**
   `CAPABILITY_NAMED_IAM` es exigido por AWS siempre que se utilice `RoleName:` o `ManagedPolicyName:` con nombres fijos.

---

[Volver a la Guía Principal](../README.md) | [Bitácora Técnica](../BITACORA_TECNICA.md)


