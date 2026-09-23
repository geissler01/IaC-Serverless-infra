import os
import json
import logging
import boto3
from botocore.exceptions import ClientError
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict

# 1 configutacion de Logging Estructurado
logger = logging.getLogger() # registrador de evento principal. Manda tiempo, ID y severidad a ACW logs
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO')) # setLevel define el filtro, no se envia a CloudWatch los Debugs, solo INFO, Warning, Error y Critical
# os.enviroment es un diccionario de variables de entorno del sistema operativo
# os.enviroment.get elije las llaves indicadas, en este caso busca a LOG_LEVEL si no lo encuentra usa a INFO como respaldo

# 2. Inyeccion de dependiencias desde variables de entorno
# Vienen del templete.yml de SAM, que aws inyecta en la ram del OS linux donde arranca python
TABLE_NAME = os.environ.get('DYNAMO_TABLE')
PRIMARY_KEY = os.environ.get('DYNAMO_KEY', 'cc')

# 3. Inicializacion del cliente DynamoDB fuera del handler ()
dynamodb = boto3.resource('dynamodb') # conecta con el servicio de DynamoDB
table = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None # objeto que representa puntualmnte la tabla fisica
# Este objeto table viene dotado de métodos como:
# table.get_item(...) (leer un registro)
# table.put_item(...) (guardar un registro)
# table.query(...) (buscar con condiciones)
# table.delete_item(...) (borrar)


# 4. Modelo de datos tipado
@dataclass # evita tener que declarar __init__, __repr__ y __eq__, porque lo hace por debajo
class VoterResponse: # nos sirve como un DTO (data transfer object)
    cc: str # esto es estetico, no se hace validacion real del dato
    nombre: str
    puesto: str
    direccion: str
    apellido: str | None = None # un atributo con valor por defecto debe ir despues de los atributos con valores obligatorios, solo para recordar

    @classmethod
    def from_dynamo(cls, item: Dict[str, Any]) -> "VoterResponse": # las comillas me permiten hacer una referencia hacia adelante y evitar el error porque aun no se ha contruido la clase
        """Mapea y valida el diccionario de dynamoDB hacia un ibjeto tipado"""
        return cls( # cls es una abreviacion de class
            cc = str(item.get('cc', '')), # se asegura la consistencia del dato
            nombre = str(item.get('nombre', '')),
            apellido = str(item.get('apellido', '')),
            puesto = str(item.get('puesto', '')),
            direccion = str(item.get('direccion', '')),
        ) 
    # con classmethod y cls no se requiere declarar un objeto que represente la toda la clase. Podmeos usar VoterResponse.from_dynamo(item) directamente. 


def build_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """ Genera respuestas http compatibles con API Gateway Proxy Integration y CORS. """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(body, default=str) # dumps (volcar a texto) convierte el diccionario a texto
    }


def extract_voter_id(event: Dict[str, Any]) -> Optional[str]: # event es lo que entrega la api a la lambda. Optional significa que puede devolver un string (cc) o None
    """ Estra el identificador del votante desde pathParameters, queryString o body. """
    # 1. Path parameter: /voters/{id}
    path_params = event.get('pathParameters') or {}
    if 'id' in path_params:
        return path_params['id']

    # 2. Query string: /voters?cc=123
    query_params = event.get('queryStringParameters') or {}
    if PRIMARY_KEY in query_params:
        return query_params[PRIMARY_KEY]

    # 3. Body json (para invocaciones directas o post)
    body_raw = event.get('body')
    if body_raw:
        try:
            body = json.loads(body_raw) if isinstance(body_raw, str) else body_raw # loads es lo contrario a dumps
            return body.get(PRIMARY_KEY)
        except json.JSONDecodeError:
            return None

    # 4. Invocasion de pruebas directas desde la consola aws
    if PRIMARY_KEY in event:
        return event[PRIMARY_KEY]

    return None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    # event contiene toda la info de la peticion http entregada por la API Gateway
    # context es un ibjeto especial de aws, son metadados, es obligatorio incluirlo
    """ Punto de entrada principal de la lambda invocada por API Gateway. """
    logger.info("Evento recibido: %s", json.dumps(event)) # imprime el evento de CloudWatch, es para debuguear y logs

    if not table: # por si la tabla fue borrada o no existe
        logger.error("DYNAMO_TABLE no está definida en las variables de entorno")
        return build_response(
            500,
            {
                'error': 'Error de configuracion interna del servidor'
            }
        )

    # Extraccion y validacion del ID
    cc = extract_voter_id(event=event)
    if not cc: # nos sirve para validar antes de hacer la consulta en dynamodb
        return build_response(400, {'error': f'Párametro requerido faltante: "{PRIMARY_KEY}". Usa /voters/{{id}} o ?cc={{numero}}'})

    try:
        # Consulta puntual 0(1) en DynamoDB
        logger.info("Buscando votante con %s=%s", PRIMARY_KEY, cc)
        result = table.get_item(Key={PRIMARY_KEY: str(cc)})
        raw_item = result.get('Item')

        if not raw_item:
            logger.warning("Votante %s no encontrado", cc)
            return build_response(404, {'error': f'Votante con cédula {cc} no existe en el padrón electoral'})

        # serializacion tipado uasndo el modelo de datos
        voter = VoterResponse.from_dynamo(raw_item) # pasamos por la clase y quedan organizados
        return build_response(200, {
            'message': 'Votante encontrado',
            'data': asdict(voter) # de objeto tipado a diccionario standar
        })

    except ClientError as e:
        logger.error("Error SDK DynamoDB: %s", e.response['Error']['Message'])
        return build_response(500, {'error': 'Error de comunicacion con la base de datos'})
    except Exception as e:
        logger.error("Error inesperado: %s", str(e))
        return build_response(500, {'error': 'Error interno del servidor'})