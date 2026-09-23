# Laboratorio VotaNet - Arquitectura Serverless & CI/CD Nativo

Documentación paso a paso de la construcción de una arquitectura Serverless modular y automatizada en AWS, ejecutada desde Windows PowerShell.

---

## Información del Entorno y Credenciales

* **Región de Despliegue:** `us-east-2` (Ohio)
* **ID de Cuenta AWS:** `841702867308`
* **Identidad Local (CLI):** `arn:aws:iam::841702867308:user/MyPc-admin`
* **Entorno de Terminal:** Windows PowerShell (`pwsh`)

---

## Paso 0: Configuración de Identidad en AWS CLI (Completado)

Para permitir que la terminal despliegue recursos en la cuenta correcta:
1. Se creó el usuario IAM `MyPc-admin` con permisos de administrador en la consola de AWS.
2. Se generaron las credenciales de acceso tipo CLI (**Access Key ID** y **Secret Access Key**).
3. Se configuró la terminal local ejecutando el comando interactivo:
   ```powershell
   aws configure
   ```
   * *AWS Access Key ID:* `AKIA...`
   * *AWS Secret Access Key:* `****`
   * *Default region name:* `us-east-2`
   * *Default output format:* `json`
4. **Comprobación de identidad:**
   ```powershell
   aws sts get-caller-identity
   ```

---

## Hoja de Ruta de Despliegue (4 Fases Modulares)

```
[ Fase 1: Base de Datos ]       --> dynamo/    (Tabla 'lablambda' para votantes)
[ Fase 2: Seguridad y CI/CD ]   --> prereq/    (Bucket S3 y Roles IAM del Pipeline)
[ Fase 3: Backend Serverless ]  --> app/       (AWS SAM: Lambda Python 3.12 + API Gateway)
[ Fase 4: Pipeline Automatizado]--> ci-cd/     (GitHub + AWS CodePipeline + AWS CodeBuild)
```

---

## Fase 1: Base de Datos DynamoDB (Completado)

* **Carpeta:** `dynamo/`
* **Plantilla:** `dynamodb-votanet.yml`
* **Script de Despliegue:** `dynamodb.sh`
* **Nombre del Stack:** `votanet-dev-dynamodb-stack`
* **Nombre Físico de la Tabla:** `votanet-dev-voters`
* **Partition Key:** `cc` (Tipo: String `S`)
* **Modo de Facturación:** `PAY_PER_REQUEST` (On-Demand / Bajo demanda)
* **Cifrado en reposo:** `SSESpecification: SSEEnabled: true`

### Conceptos Clave Aprendidos

1. **Convención Profesional de Nombres:**
   * Fórmula estándar: `[proyecto]-[entorno]-[entidad]` (ejemplo: `votanet-dev-voters`).
   * Desacoplamiento: El código de la aplicación no depende del nombre físico gracias al enchufe `Export: Name: DynamoLab`.
2. **Seguridad e Identidad (IAM en DynamoDB):**
   * DynamoDB es un **recurso pasivo de almacenamiento**: NO requiere un rol de IAM para existir.
   * El rol de IAM se le asigna a los **actores activos** (como la función Lambda o usuarios) que necesitan leer o escribir en la tabla.
3. **Comandos de Terminal en Linux / Git Bash:**
   * `cd infra_own/dynamo`: Desplaza la terminal a la carpeta donde vive la plantilla para resolver rutas relativas (`./`).
   * `chmod +x dynamodb.sh`: Otorga permiso de ejecución explícito (`+x`) al archivo de texto en sistemas Unix.
   * `./dynamodb.sh`: El prefijo `./` indica explícitamente ejecutar desde el directorio actual, evitando riesgos de colisión en el `$PATH` del sistema.

### Comandos de Verificación e Inserción de Datos

Para verificar que la tabla existe en Ohio (`us-east-2`):
```bash
aws dynamodb describe-table \
  --table-name votanet-dev-voters \
  --region us-east-2 \
  --query "Table.{Name:TableName, Status:TableStatus, Key:KeySchema[0].AttributeName, Billing:BillingModeSummary.BillingMode}"
```

Para insertar dos votantes de prueba (Pedro y María):
```bash
aws dynamodb put-item \
  --table-name votanet-dev-voters \
  --region us-east-2 \
  --item '{
    "cc": {"S": "123456789"},
    "nombre": {"S": "Pedro"},
    "apellido": {"S": "Gomez"},
    "direccion": {"S": "Cra 1 1-1"},
    "puesto": {"S": "mesa 50"}
  }'

aws dynamodb put-item \
  --table-name votanet-dev-voters \
  --region us-east-2 \
  --item '{
    "cc": {"S": "987654321"},
    "nombre": {"S": "Maria"},
    "apellido": {"S": "Lopez"},
    "direccion": {"S": "Calle 10 5-20"},
    "puesto": {"S": "mesa 12"}
  }'
```

Consultar los votantes insertados:
```bash
aws dynamodb scan \
  --table-name votanet-dev-voters \
  --region us-east-2 \
  --query "Items[*].{CC:cc.S, Nombre:nombre.S, Apellido:apellido.S}" \
  --output table
```

---

## Fase 2: Capa de Seguridad y Cimientos de CI/CD (En Progreso)

* **Carpeta:** `prereq/`

### 2.1 Almacenamiento de Artefactos (Completado)
* **Plantilla:** `bucket-s3.yml`
* **Script de Despliegue:** `deploy-s3.sh`
* **Nombre del Stack:** `votanet-dev-s3-stack`
* **Nombre Físico del Bucket:** `votanet-artefacts-841702867308-us-east-2`
* **Estado:** `CREATE_COMPLETE`
* **Configuraciones Enterprise:**
  * Cifrado en reposo `AES256`.
  * `PublicAccessBlockConfiguration` total (las 4 directivas en `true`).
  * `VersioningConfiguration: Status: Enabled` (historial de versiones para zips).
  * `LifecycleConfiguration`: Expiración y borrado automático a los 30 días para optimizar costos.
* **Exports Disponibles:**
  * `S3ArtifactsBucket`: `votanet-artefacts-841702867308-us-east-2`
  * `S3ArtifactsBucketArn`: `arn:aws:s3:::votanet-artefacts-841702867308-us-east-2`

### 2.2 Roles y Políticas de IAM (Siguiente Paso)
### 2.2 Roles y Políticas de IAM (Completado)
* **Plantilla:** `iam-roles.yml`
* **Script de Despliegue:** `deploy-iam.sh`
* **Recursos a crear:**
  1. `CodeBuildRole`: Permisos para compilar, generar logs y subir a S3 (importando `S3ArtifactsBucket`).
  2. `CodePipelineRole`: Permisos para orquestar y llamar a CloudFormation.
  3. `CloudFormationDeployRole`: Permisos para que CloudFormation cree la Lambda y sus roles.
  4. `LambdaPolicyDynamo`: Permiso para consultar DynamoDB (`dynamodb:Query`, `dynamodb:GetItem`).
  5. `LambdaPolicyCW`: Permiso para escribir logs en CloudWatch.
* **Script de Despliegue:** `deploy-iam-roles.sh`
* **Nombre del Stack:** `votanet-dev-prereq-stack`
* **Estado:** `CREATE_COMPLETE`
* **Capacidades Requeridas:** `--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM`

#### Recursos Creados y Nombres Físicos en AWS:
1. **`CodeBuildRole`:** Rol para compilación y empaquetado de código.
   * *ARN:* `arn:aws:iam::841702867308:role/service-role/votanet-dev-prereq-stack-CodeBuildRole-4qMdshJ78SHy`
   * *Nombre físico:* Generado dinámicamente por CloudFormation (`[Stack]-[LogicalId]-[Hash]`) para evitar colisiones.
   * *Permisos:* Logs en CloudWatch, descarga y subida al bucket de artefactos S3 (usando `!ImportValue S3ArtifactsBucketArn`), y validación de templates CloudFormation.
2. **`CodePipelineRole`:** Rol del orquestador del CI/CD.
   * *ARN:* `arn:aws:iam::841702867308:role/votanet-dev-prereq-stack-CodePipelineRole-kytXr6hYljJc`
   * *Nombre físico:* Generado dinámicamente por CloudFormation.
   * *Permisos:* Lectura y versionado en S3, disparo de builds en CodeBuild (`codebuild:StartBuild`), CRUD y ChangeSets de CloudFormation, y permiso `iam:PassRole` para delegar ejecución.
3. **`CloudFormationDeployRole`:** Rol obrero que asume CloudFormation para crear la infraestructura serverless.
   * *ARN:* `arn:aws:iam::841702867308:role/CloudFormationDeployRole`
   * *Nombre físico:* Fijo mediante `RoleName: CloudFormationDeployRole`.
   * *Permisos:* `AdministratorAccess` (requerido para crear funciones Lambda, API Gateway y recursos asociados dinámicamente).
4. **`LambdaPolicyDynamoDB`:** Política gestionada para la función Lambda.
   * *ARN:* `arn:aws:iam::841702867308:policy/LambdaPolicyDynamoDB`
   * *Permisos:* Lectura y consulta en la tabla DynamoDB importando su ARN con `!ImportValue DynamoLabArn`.
5. **`LambdaPolicyCW`:** Política gestionada para logs de Lambda.
   * *ARN:* `arn:aws:iam::841702867308:policy/LambdaPolicyCW`
   * *Permisos:* Creación de streams y escritura de eventos en log groups bajo `/aws/lambda/*`.

#### Tabla de Outputs Exportados:
| Clave (OutputKey) | Nombre de Exportación (ExportName) | ARN Físico en AWS |
| :--- | :--- | :--- |
| `CodeBuildRoleArn` | `CodeBuildRoleArn` | `arn:aws:iam::841702867308:role/service-role/votanet-dev-prereq-stack-CodeBuildRole-4qMdshJ78SHy` |
| `CodePipelineRoleArn` | `CodePipelineRoleArn` | `arn:aws:iam::841702867308:role/votanet-dev-prereq-stack-CodePipelineRole-kytXr6hYljJc` |
| `CloudFormationDeployRoleArn` | `CloudFormationDeployRoleArn` | `arn:aws:iam::841702867308:role/CloudFormationDeployRole` |
| `LambdaPolicyDynamoDBArn` | `LambdaPolicyDynamoDBArn` | `arn:aws:iam::841702867308:policy/LambdaPolicyDynamoDB` |
| `LambdaPolicyCWArn` | `LambdaPolicyCWArn` | `arn:aws:iam::841702867308:policy/LambdaPolicyCW` |

#### Conceptos Clave y Hallazgos Técnicos:

1. **Capabilities de CloudFormation (`CAPABILITY_IAM` vs `CAPABILITY_NAMED_IAM`):**
   * AWS exige consentimiento explícito mediante *capabilities* antes de alterar la seguridad de una cuenta.
   * `CAPABILITY_IAM` se requiere cuando los nombres de los roles son automáticos.
   * `CAPABILITY_NAMED_IAM` es obligatoria cuando se especifica `RoleName:` o `ManagedPolicyName:`. Esto protege contra colisiones de nombres y escaladas de privilegios accidentales.
2. **Los 3 Tipos de Identificadores en CloudFormation:**
   * **Logical ID:** Identificador interno en el YAML (ej: `CodeBuildRole:`).
   * **Physical ID / Name:** Nombre real visible en la consola de IAM (`RoleName`, `ManagedPolicyName`).
   * **Export Name:** Clave pública dentro de `Outputs:` consumible por otros stacks con `!ImportValue`.
3. **Resolución de Referencias y Dependencias Implícitas (DAG):**
   * CloudFormation no lee de forma secuencial de arriba a abajo; construye un Grafo Acíclico Dirigido (DAG) en memoria para resolver automáticamente referencias hacia adelante (*Forward References*) como `!GetAtt CloudFormationDeployRole.Arn`.
4. **Portabilidad de Particiones con `${AWS::Partition}`:**
   * La estructura de un ARN es `arn:<partición>:<servicio>:<region>:<cuenta>:<recurso>`.
   * Para evitar advertencias de portabilidad en nubes gubernamentales (`aws-us-gov`) o regionales (`aws-cn`), la buena práctica es parametrizar la partición como `arn:${AWS::Partition}:logs:...`.
5. **Convenciones de Verbos en la API de AWS:**
   * Las operaciones de **escritura/mutación** son en **singular** (`CreateStack`, `UpdateStack`, `DeleteStack`) porque operan sobre un único recurso a la vez.
   * Las operaciones de **lectura/consulta** son en **plural** (`DescribeStacks`, `ListStacks`) porque consultan colecciones.
6. **Comportamiento Intrínseco de `!Ref` en Managed Policies:**
   * Para recursos `AWS::IAM::ManagedPolicy`, la función `!Ref` devuelve directamente el **ARN completo** de la política, no su nombre simple.
7. **Secretos vs Variables:**
   * Las variables de script (`STACK_NAME`) facilitan la reutilización.
   * Los datos confidenciales (como el Personal Access Token de GitHub para la Fase 4) NUNCA se escriben en YAML ni en Git; se resuelven en tiempo de ejecución con **AWS Secrets Manager** o **SSM Parameter Store** (`{{resolve:secretsmanager:...}}`).

---

## Fase 3: Backend Serverless con AWS SAM (Completado)

* **Carpeta:** `app/`
* **Plantilla SAM:** `template.yml` (`Transform: AWS::Serverless-2016-10-31`)
* **Código Fuente:** `lambda_function.py` (Python 3.12, Tipado con `@dataclass`, sin dependencias externas)
* **Configuración SAM:** `samconfig.toml`
* **Nombre del Stack:** `votanet-dev-app-stack`
* **Estado:** `CREATE_COMPLETE`
* **Capacidades Requeridas:** `CAPABILITY_IAM CAPABILITY_NAMED_IAM`

### Recursos Creados y Nombres Físicos en AWS:
1. **`VotaNetLambdaFunction`:**
   * *ARN:* `arn:aws:lambda:us-east-2:841702867308:function:votanet-dev-query-voter`
   * *Runtime:* Python 3.12 | Memoria: 128 MB | Timeout: 10s.
   * *Variables de Entorno inyectadas:* `DYNAMO_TABLE: votanet-dev-voters` (importada de DynamoLab), `DYNAMO_KEY: cc`, `LOG_LEVEL: INFO`.
2. **`VotaNetLambdaRole`:**
   * *Nombre físico:* `votanet-dev-lambda-execution-role`
   * *Trust Policy:* Permite asumir rol a `lambda.amazonaws.com`.
   * *Políticas asociadas:* Importadas de Fase 2 (`LambdaPolicyDynamoDBArn` y `LambdaPolicyCWArn`).
3. **`VotaNetApi`:**
   * *Tipo:* API Gateway REST (Stage: `dev`).
   * *Soporte CORS:* Configurado para métodos `GET, POST, OPTIONS` con cabeceras estándar.
   * *Rutas expuestas:*
     * `GET /voters/{id}` (Path Parameter)
     * `GET /voters` (Query String `?cc=...`)
     * `POST /voters` (Payload Body JSON)

### Outputs y Endpoints Verificados en Vivo:
* **`ApiEndpoint`:** `https://nk1hgicsmf.execute-api.us-east-2.amazonaws.com/dev/voters`
* **`LambdaFunctionArn`:** `arn:aws:lambda:us-east-2:841702867308:function:votanet-dev-query-voter`

### Comandos de Prueba y Resultados:
```bash
# Prueba 1: Consulta por Path Parameter (Pedro)
curl -s https://nk1hgicsmf.execute-api.us-east-2.amazonaws.com/dev/voters/123456789
# Respuesta: {"message": "Votante encontrado", "data": {"cc": "123456789", "nombre": "Pedro", "puesto": "mesa 50", "direccion": "Cra 1 1-1", "apellido": "Gomez"}}

# Prueba 2: Consulta por Query String (María)
curl -s "https://nk1hgicsmf.execute-api.us-east-2.amazonaws.com/dev/voters?cc=987654321"
# Respuesta: {"message": "Votante encontrado", "data": {"cc": "987654321", "nombre": "Maria", "puesto": "mesa 12", "direccion": "Calle 10 5-20", "apellido": "Lopez"}}

# Prueba 3: Votante inexistente (Control 404)
curl -s https://nk1hgicsmf.execute-api.us-east-2.amazonaws.com/dev/voters/000000
# Respuesta: {"error": "Votante con cédula 000000 no existe en el padrón electoral"}
```

---

## Fase 4: Pipeline Automatizado de CI/CD (Última Fase)

* **Carpeta:** `pipeline/` (o `ci-cd/`)
* **Objetivo:** Automatizar el ciclo completo de integración y despliegue continuo mediante GitHub y AWS.
* **Componentes:**
  * `buildspec.yml`: Instrucciones de empaquetado para CodeBuild (`sam build`, `sam package`).
  * Conexión con GitHub (CodeStarSourceConnection).
  * Orquestador CodePipeline V2 consumiendo los roles IAM creados en Fase 2.
  * Despliegue automático desatendido en cada `git push`.



