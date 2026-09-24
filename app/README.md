# Módulo 3: Backend Serverless (AWS SAM & Python 3.12)

Este módulo implementa la lógica de negocio y el enrutamiento HTTP de la aplicación serverless **VotaNet** utilizando el framework oficial **AWS Serverless Application Model (SAM)**.

---

## Archivos del Módulo

```text
app/
├── lambda_function.py     # Código fuente Python 3.12 con tipado estricto
├── template.yml           # Plantilla SAM (Transform: AWS::Serverless-2016-10-31)
└── samconfig.toml         # Configuración persistente del CLI de SAM
```

---

## Arquitectura de Software: `lambda_function.py`

### 1. Tipado Estricto sin Dependencias Externas (Estilo FastAPI)
Para mantener el paquete de despliegue ultra ligero (< 15 KB) y eliminar *cold starts* lentos, se utilizó la librería estándar de Python 3.12:
* `@dataclass`: Define el contrato de salida `VoterResponse` garantizando que las respuestas sean consistentes y predecibles.
* **Patrón Factory (`from_dynamo`):** Método de clase (`@classmethod`) que toma el diccionario crudo de DynamoDB y lo mapea hacia un objeto tipado seguro, protegiendo contra `KeyError` y evitando la exposición de atributos internos no deseados (*Whitelist Pattern*).

### 2. Extractor Multiformato (`extract_voter_id`)
Permite consumir la API de 4 formas diferentes:
1. **Path Parameter:** `GET /voters/123456789`
2. **Query String:** `GET /voters?cc=123456789`
3. **Body JSON:** `POST /voters` con `{ "cc": "123456789" }`
4. **Prueba directa de consola AWS:** `{ "cc": "123456789" }`

### 3. Programación Defensiva y Respuestas HTTP
* `200 OK`: Votante encontrado con payload JSON y cabeceras CORS.
* `400 Bad Request`: Parámetro requerido faltante o JSON mal formado.
* `404 Not Found`: Votante no existe en el padrón electoral.
* `500 Internal Server Error`: Fallo de conexión o error de configuración de variables de entorno.

---

## Infraestructura como Código: `template.yml`

* **Macro de SAM:** `Transform: 'AWS::Serverless-2016-10-31'`
* **Sección `Globals`:** Aplica runtime `python3.12`, memoria `128 MB`, timeout `10s` y variables de entorno (`DYNAMO_TABLE: !ImportValue DynamoLab`) a todas las funciones del proyecto.

### Recursos Creados:
1. **`VotaNetApi` (`AWS::Serverless::Api`):**
   * Stage: `dev`.
   * CORS habilitado para métodos `GET, POST, OPTIONS`.
2. **`VotaNetLambdaRole` (`AWS::IAM::Role`):**
   * Rol de ejecución propio de la aplicación consumiendo las políticas gestionadas creadas en la Fase 2 (`LambdaPolicyDynamoDBArn` y `LambdaPolicyCWArn`).
3. **`VotaNetLambdaFunction` (`AWS::Serverless::Function`):**
   * Nombre físico: `votanet-dev-query-voter`.
   * Handler: `lambda_function.lambda_handler`.
   * Eventos mapeados hacia API Gateway con integración proxy automática.

---

## Física del Entorno de Ejecución en AWS

* **Ubicación del código:** El archivo se descomprime físicamente en `/var/task/lambda_function.py` (directorio de **solo lectura**).
* **Almacenamiento escribible:** Si la función necesitara generar archivos temporales, el único directorio con permisos de escritura es `/tmp/`.
* **Reutilización en Warm Starts:** Las conexiones (`boto3.resource('dynamodb')`) y el logger declarados fuera de `def lambda_handler` permanecen instanciados en memoria RAM entre peticiones consecutivas, permitiendo respuestas en menos de **15 milisegundos**.

---

## Comandos de Despliegue Local con SAM

```bash
# Compilar la aplicación y preparar el directorio .aws-sam/
sam build

# Desplegar en AWS CloudFormation
sam deploy
```
*(Nota: Para el primer despliegue interactivo se usó `sam deploy --guided --s3-bucket votanet-artefacts-...` y se configuró `capabilities = "CAPABILITY_IAM CAPABILITY_NAMED_IAM"` en `samconfig.toml`).*

---

[Volver a la Guía Principal](../README.md) | [Bitácora Técnica](../BITACORA_TECNICA.md)


