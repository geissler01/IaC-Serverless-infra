# Módulo 1: Base de Datos NoSQL (Amazon DynamoDB)

Este módulo contiene la definición como código y el script de despliegue para la base de datos no relacional de **VotaNet**.

---

## Archivos del Módulo

| Archivo | Propósito |
| :--- | :--- |
| `dynamodb-votanet.yml` | Plantilla de CloudFormation con la definición de la tabla y sus outputs exportados. |
| `dynamodb.sh` | Script bash de despliegue automatizado con AWS CLI. |

---

## Especificaciones de la Tabla

* **Nombre del Stack:** `votanet-dev-dynamodb-stack`
* **Nombre Físico de la Tabla:** `votanet-dev-voters`
* **Partition Key (Clave Primaria):** `cc` (Tipo: String `S`)
* **Modo de Facturación:** `PAY_PER_REQUEST` (On-Demand / Bajo Demanda).
  * *Ventaja:* Cero costos fijos mientras no haya tráfico; escala automáticamente a miles de lecturas/escrituras concurrentes sin necesidad de provisionar capacidad previamente.
* **Cifrado en Reposo:** Cifrado transparente administrado por AWS mediante `SSESpecification: SSEEnabled: true`.

---

## Exports Generados (Enchufes para otros Stacks)

CloudFormation expone estas dos claves para ser consumidas por los stacks de aplicación y seguridad:

| Export Name | Valor Real | Consumido por |
| :--- | :--- | :--- |
| `DynamoLab` | `votanet-dev-voters` | Inyectado como variable de entorno `DYNAMO_TABLE` en la Lambda (`app/template.yml`). |
| `DynamoLabArn` | `arn:aws:dynamodb:us-east-2:841702867308:table/votanet-dev-voters` | Utilizado en la política de IAM `LambdaPolicyDynamoDB` (`prereq/iam-roles.yml`). |

---

## Conceptos Clave y Filosofía de Diseño

1. **DynamoDB es un Recurso Pasivo:**
   A diferencia de Lambda o CodeBuild, DynamoDB **no necesita un rol de IAM para existir**. Los roles de IAM se asignan a los *actores activos* (como la función Lambda o usuarios) que necesitan interactuar con la tabla.
2. **Convención Profesional de Nombres:**
   Fórmula estándar: `[proyecto]-[entorno]-[entidad]` (`votanet-dev-voters`).
3. **Desacoplamiento Total:**
   El código de la aplicación nunca conoce el nombre físico directo; siempre se conecta consumiendo el export `DynamoLab`.

---

## Comandos Útiles de Verificación y Carga de Datos

### Verificar estado de la tabla:
```bash
aws dynamodb describe-table \
  --table-name votanet-dev-voters \
  --region us-east-2 \
  --query "Table.{Name:TableName, Status:TableStatus, Key:KeySchema[0].AttributeName, Billing:BillingModeSummary.BillingMode}"
```

### Insertar registros de votantes de prueba:
```bash
# Votante 1: Pedro Gomez
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

# Votante 2: Maria Lopez
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

### Escaneo de verificación:
```bash
aws dynamodb scan \
  --table-name votanet-dev-voters \
  --region us-east-2 \
  --query "Items[*].{CC:cc.S, Nombre:nombre.S, Puesto:puesto.S}" \
  --output table
```

---

[Volver a la Guía Principal](../README.md) | [Bitácora Técnica](../BITACORA_TECNICA.md)


