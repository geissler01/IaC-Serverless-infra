# VotaNet Serverless Backend & Native CI/CD Pipeline en AWS

Arquitectura Serverless y Pipeline de Integración y Entrega Continua (CI/CD) completamente automatizado y construido como código (IaC) en **Amazon Web Services (AWS)**.

Este proyecto moderniza un diseño tradicional serverless (Platzi 2017) hacia los **estándares Cloud-Native de 2024-2026**: reemplazo de CodeCommit y Cloud9 por **GitHub + AWS CodeConnections**, Python 3.12 con tipado estricto, empaquetado con **AWS SAM**, y orquestación desatendida con **CodePipeline V2**.

---

## Diagrama de Arquitectura

```mermaid
flowchart TD
    subgraph VCS ["Control de Versiones"]
        Dev["Desarrollador"] -->|git push| GH["GitHub (main)"]
    end

    subgraph CICD ["Tuberia de CI/CD (AWS CodePipeline V2)"]
        GH -->|Webhook OAuth| Conn["CodeStar Connection"]
        Conn -->|Source| S3Artifacts["S3 Bucket (Artefactos Versionados)"]
        S3Artifacts -->|Build| CB["AWS CodeBuild (Amazon Linux 2023)"]
        CB -->|sam build & sam package| S3Artifacts
        S3Artifacts -->|Deploy| CF["AWS CloudFormation (ChangeSet Replace & Execute)"]
    end

    subgraph APP ["Backend Serverless (AWS SAM)"]
        CF -->|Despliega| APIGW["Amazon API Gateway (REST - dev)"]
        CF -->|Despliega| Lambda["AWS Lambda (Python 3.12)"]
        APIGW -->|Proxy Integration| Lambda
        Lambda -->|get_item O(1)| Dynamo["Amazon DynamoDB (votanet-dev-voters)"]
        Lambda -->|Logs| CW["Amazon CloudWatch Logs"]
    end

    classDef aws fill:#232F3E,stroke:#FF9900,stroke-width:2px,color:#fff;
    classDef git fill:#24292e,stroke:#fff,stroke-width:1px,color:#fff;
    class APIGW,Lambda,Dynamo,CW,S3Artifacts,CB,CF,Conn aws;
    class GH,Dev git;
```

---

## Principales Decisiones de Ingeniería y Buenas Prácticas

1. **Desacoplamiento Total mediante Infraestructura Modular:**
   Cada capa es un stack independiente de CloudFormation que exporta salidas (`Outputs`) consumibles por otros stacks con `!ImportValue`:
   * `DynamoLab` -> Importado por la Lambda.
   * `S3ArtifactsBucket` -> Importado por CodeBuild y CodePipeline.
   * `LambdaPolicyDynamoDBArn` y `LambdaPolicyCWArn` -> Importados por el rol de ejecución de la Lambda.
2. **Principio de Mínimo Privilegio (Least Privilege IAM):**
   * Separación explícita entre **Trust Policies** (`AssumeRolePolicyDocument`) y **Permission Policies**.
   * CloudFormation ejecuta con un rol delegado específico (`CloudFormationDeployRole`), evitando el uso de credenciales de usuario raíz o administradores en el CI/CD.
3. **Backend Tipado sin Dependencias Externas:**
   * La función Lambda utiliza `@dataclass` y el patrón *Factory* (`from_dynamo`), logrando tipado estricto estilo FastAPI pero con **cero librerías externas** pesadas.
   * Paquete de despliegue ultra ligero (< 15 KB) y *Cold Starts* inferiores a **50 milisegundos**.
4. **Despliegues Seguros con ChangeSets en CloudFormation:**
   * La etapa de despliegue en CodePipeline no sobreescribe recursos a ciegas.
   * Ejecuta en 2 tiempos: `RunOrder: 1` (`CHANGE_SET_REPLACE`) calcula el plano de diferencias, y `RunOrder: 2` (`CHANGE_SET_EXECUTE`) aplica el cambio en vivo sin tiempo de inactividad (*Zero Downtime*).

---

## Estructura del Repositorio

| Módulo / Directorio | Descripción | Documentación Dedicada |
| :--- | :--- | :--- |
| **`dynamo/`** | Definición CloudFormation de la tabla NoSQL DynamoDB | [dynamo/README.md](dynamo/README.md) |
| **`prereq/`** | Bucket S3 de artefactos y políticas/roles IAM | [prereq/README.md](prereq/README.md) |
| **`app/`** | Backend Serverless SAM, Lambda Python 3.12 y API Gateway | [app/README.md](app/README.md) |
| **`config/`** | Receta de compilación y empaquetado para CodeBuild (`buildspec.yml`) | [config/README.md](config/README.md) |
| **`pipeline/`** | Pipeline V2, conexión GitHub y despliegue con ChangeSets | [pipeline/README.md](pipeline/README.md) |
| **Raíz** | Bitácora técnica profunda de arquitectura y física de ejecución | [BITACORA_TECNICA.md](BITACORA_TECNICA.md) |

```text
infra_own/
├── README.md                 # Guia publica de arquitectura
├── BITACORA_TECNICA.md       # Bitacora tecnica profunda con detalles fisicos y errores
│
├── dynamo/                   # [Fase 1] Base de Datos NoSQL DynamoDB
│   ├── dynamodb-votanet.yml  # Definicion CloudFormation de la tabla
│   ├── dynamodb.sh           # Script de despliegue
│   └── README.md             # Guia del modulo DynamoDB
│
├── prereq/                   # [Fase 2] Almacenamiento S3 y Seguridad IAM
│   ├── bucket-s3.yml         # Bucket S3 versionado, cifrado y con ciclo de vida
│   ├── deploy-s3.sh          # Script de despliegue S3
│   ├── iam-roles.yml         # Roles de CodeBuild, CodePipeline y politicas de Lambda
│   ├── deploy-iam-roles.sh   # Script de despliegue IAM
│   └── README.md             # Guia del modulo de Prerrequisitos
│
├── app/                      # [Fase 3] Backend Serverless (AWS SAM)
│   ├── lambda_function.py    # Codigo Python 3.12 con tipado y manejo de errores
│   ├── template.yml          # Plantilla SAM con API Gateway y Lambda
│   ├── samconfig.toml        # Configuracion persistente del CLI de SAM
│   └── README.md             # Guia del modulo de Aplicacion
│
├── config/                   # [Fase 4A] Instrucciones de Compilacion (CodeBuild)
│   ├── buildspec.yml         # Fases de install, build y empaquetado SAM
│   └── README.md             # Guia del modulo de Compilacion
│
└── pipeline/                 # [Fase 4B] Orquestador de Entrega Continua (CodePipeline)
    ├── pipeline.yml          # Conexion GitHub, CodeBuild y CloudFormation V2
    ├── deploy-pipeline.sh    # Script de despliegue del Pipeline
    └── README.md             # Guia del modulo del Pipeline
```

---

## Guía de Despliegue Paso a Paso (Replicabilidad)

### Prerrequisitos
* Cuenta de AWS con credenciales de administrador configuradas en AWS CLI (`aws configure`).
* Región por defecto: `us-east-2` (Ohio).
* AWS SAM CLI instalado (`sam --version` >= 1.100).
* Git instalado y cuenta en GitHub.

---

### Paso 1: Base de Datos DynamoDB
```bash
cd infra_own/dynamo
chmod +x dynamodb.sh
./dynamodb.sh
```

---

### Paso 2: Bucket de Artefactos y Roles IAM
```bash
cd ../prereq
chmod +x deploy-s3.sh deploy-iam-roles.sh

# 1. Crear el bucket S3 versionado
./deploy-s3.sh

# 2. Crear los roles y políticas IAM
./deploy-iam-roles.sh
```

---

### Paso 3: Backend Serverless con AWS SAM
```bash
cd ../app

# Compilar
sam build

# Desplegar interactivamente
sam deploy --guided --s3-bucket <nombre-del-bucket-creado-en-paso-2>
# Configurar: Stack Name = votanet-dev-app-stack, Region = us-east-2
```

---

### Paso 4: Pipeline Automatizado de CI/CD
```bash
cd ../pipeline
chmod +x deploy-pipeline.sh
./deploy-pipeline.sh
```

> **Nota - Activación de GitHub (Paso de 30 segundos):**
> 1. Ve a la consola web de AWS -> **CodePipeline** -> **Settings** -> **Connections**.
> 2. Selecciona `votanet-github-connection` (estado `Pending`).
> 3. Clic en **"Update pending connection"** y autoriza el enlace con tu cuenta de GitHub.
> 4. El estado pasará a **`Available`** y el pipeline empezará a compilar y desplegar automáticamente.

---

## Referencia de la API y Pruebas en Vivo

* **Endpoint Base:** `https://nk1hgicsmf.execute-api.us-east-2.amazonaws.com/dev/voters`

### 1. Consulta por Path Parameter (`GET /voters/{id}`)
```bash
curl -s https://nk1hgicsmf.execute-api.us-east-2.amazonaws.com/dev/voters/123456789
```
**Respuesta (200 OK):**
```json
{
  "message": "Votante encontrado exitosamente (Deploy automatico CI/CD v2.0)",
  "data": {
    "cc": "123456789",
    "nombre": "Pedro",
    "apellido": "Gomez",
    "puesto": "mesa 50",
    "direccion": "Cra 1 1-1"
  }
}
```

### 2. Consulta por Query String (`GET /voters?cc={numero}`)
```bash
curl -s "https://nk1hgicsmf.execute-api.us-east-2.amazonaws.com/dev/voters?cc=987654321"
```
**Respuesta (200 OK):**
```json
{
  "message": "Votante encontrado exitosamente (Deploy automatico CI/CD v2.0)",
  "data": {
    "cc": "987654321",
    "nombre": "Maria",
    "apellido": "Lopez",
    "puesto": "mesa 12",
    "direccion": "Calle 10 5-20"
  }
}
```

### 3. Votante No Encontrado (404 Not Found)
```bash
curl -s https://nk1hgicsmf.execute-api.us-east-2.amazonaws.com/dev/voters/000000
```
**Respuesta (404 Not Found):**
```json
{
  "error": "Votante con cédula 000000 no existe en el padrón electoral"
}
```

---

## Documentación Interna para Desarrolladores

Para una inmersión técnica profunda en el comportamiento interno de los contenedores de CodeBuild, el sistema de archivos de Lambda (`/var/task`), el funcionamiento de las microVMs Firecracker y el catálogo forense de errores resueltos en vivo, consulta la:

**[Bitácora Técnica de Ingeniería (BITACORA_TECNICA.md)](BITACORA_TECNICA.md)**

---

## Autor
* **Desarrollador / Cloud DevOps:** [Geissler](https://github.com/geissler01)
* **Entorno:** AWS `us-east-2` | Arquitectura Cloud-Native Serverless
