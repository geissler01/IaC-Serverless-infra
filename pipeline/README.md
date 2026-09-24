# Módulo 4B: Orquestador CI/CD (AWS CodePipeline V2 & GitHub)

Este módulo automatiza la integración y entrega continua (CI/CD) de la aplicación, conectando el repositorio de GitHub con AWS mediante **AWS CodeConnections**, compilando con **CodeBuild** y desplegando con **CloudFormation**.

---

## Archivos del Módulo

| Archivo | Propósito |
| :--- | :--- |
| `pipeline.yml` | Plantilla CloudFormation del Pipeline V2, proyecto CodeBuild y conexión GitHub. |
| `deploy-pipeline.sh` | Script bash para desplegar o actualizar el stack del pipeline. |

---

## Recursos Declarados en `pipeline.yml`

```text
[ GitHub Repository ] 
        │ (CodeStar Connection: votanet-github-connection)
        ▼
[ AWS CodePipeline V2: votanet-dev-pipeline ]
        ├── ETAPA 1: Source (Descarga zip a S3 -> SourceArtifacts)
        ├── ETAPA 2: Build  (CodeBuild votanet-dev-build -> BuildArtifacts)
        └── ETAPA 3: Deploy (CloudFormation ChangeSets -> votanet-dev-app-stack)
```

### 1. `GitHubConnection` (`AWS::CodeStarConnections::Connection`)
* **Nombre:** `votanet-github-connection` | **Proveedor:** `GitHub`.
* Conector seguro OAuth 2.0. Al crearse con CloudFormation queda en estado **`PENDING`**; requiere autorización manual de una sola vez en la consola de AWS ("Update pending connection") para enlazar con la cuenta de GitHub.

### 2. `CodePipelineConnectionPolicy` (`AWS::IAM::Policy`)
* Concede el permiso `codestar-connections:UseConnection` al rol `CodePipelineRole` creado en la Fase 2, utilizando la función intrínseca:
  ```yaml
  Roles:
    - !Select [1, !Split ["role/", !ImportValue CodePipelineRoleArn]]
  ```

### 3. `CodeBuildProject` (`AWS::CodeBuild::Project`)
* **Nombre:** `votanet-dev-build`.
* **Imagen:** `aws/codebuild/amazonlinux2-x86_64-standard:5.0` (2 vCPUs, 4 GB RAM).
* **Rol:** `!ImportValue CodeBuildRoleArn`.
* **Variable Inyectada:** `S3_BUCKET: !ImportValue S3ArtifactsBucket`.
* **Ruta de BuildSpec:** `config/buildspec.yml`.

### 4. `VotaNetPipeline` (`AWS::CodePipeline::Pipeline`)
* **Tipo:** `V2` (versión moderna con mejor rendimiento y reintentos).
* **Almacén de Artefactos:** Bucket S3 de la Fase 2 (`!ImportValue S3ArtifactsBucket`).
* **Etapas y Acciones:**
  * **Etapa 1 (Source):** Descarga el repositorio `geissler01/IaC-Serverless-infra` en la rama `main` con `DetectChanges: true` (disparador automático por Webhook).
  * **Etapa 2 (Build):** Ejecuta el proyecto CodeBuild y produce `BuildArtifacts` (que contiene `packaged.yaml`).
  * **Etapa 3 (Deploy):** Dividida en dos subfases ordenadas:
    1. `CreateChangeSet` (`RunOrder: 1`, `CHANGE_SET_REPLACE`): Genera la propuesta de cambios sobre `votanet-dev-app-stack`.
    2. `ExecuteChangeSet` (`RunOrder: 2`, `CHANGE_SET_EXECUTE`): Aplica los cambios en caliente sin intervención humana.

---

## Comandos de Despliegue

```bash
cd infra_own/pipeline

# Desplegar el pipeline
chmod +x deploy-pipeline.sh
./deploy-pipeline.sh
```

---

## Verificación del Flujo End-to-End

1. Realizar cualquier cambio en `app/lambda_function.py`.
2. Ejecutar `git commit -am "feat: update"` y `git push origin main`.
3. CodePipeline detecta el commit en < 1 segundo, avanza por las 3 etapas y en ~90 segundos la API Gateway responde con el nuevo código en vivo.

---

[Volver a la Guía Principal](../README.md) | [Bitácora Técnica](../BITACORA_TECNICA.md)


