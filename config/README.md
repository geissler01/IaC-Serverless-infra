# Módulo 4A: Configuración de Compilación (AWS CodeBuild)

Este módulo contiene la receta de compilación y empaquetado continuo (`buildspec.yml`) ejecutada por el agente de **AWS CodeBuild** en la nube.

---

## Archivo: `buildspec.yml`

```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.12
    commands:
      - echo "=== FASE 1 -> Verificando herramientas en CodeBuild ==="
      - python --version
      - sam --version

  build:
    commands:
      - echo "=== FASE 2 -> Entrando a la carpeta app y compilando con SAM ==="
      - cd app
      - sam build

  post_build:
    commands:
      - echo "=== FASE 3 -> Empaquetando y subiendo zip a S3 ==="
      - sam package --s3-bucket ${S3_BUCKET} --output-template-file packaged.yaml
      - echo "=== Empaquetado finalizado con exito ==="

artifacts:
  base-directory: app
  files:
    - packaged.yaml
```

---

## Anatomía del Ciclo de Compilación

1. **`version: 0.2`:** Versión estándar recomendada por AWS para entornos Linux.
2. **Fase `install`:** Especifica el runtime de Python 3.12. La imagen oficial de CodeBuild (`standard:5.0`) ya incluye el CLI de AWS SAM preinstalado.
3. **Fase `build`:** Navega a la subcarpeta `cd app` y ejecuta `sam build`.
4. **Fase `post_build`:** Ejecuta `sam package`. Utiliza la variable de entorno `${S3_BUCKET}` inyectada desde el proyecto de CodeBuild, sube el archivo `.zip` resultante al bucket y genera la plantilla de salida **`packaged.yaml`**.
5. **Sección `artifacts`:**
   * `base-directory: app`: Le indica a CodeBuild que busque los archivos resultantes dentro del directorio `app/`.
   * `files: [packaged.yaml]`: Es el artefacto que se entrega a la siguiente etapa (CloudFormation Deploy).

---

## Hallazgos Técnicos y Lecciones de Ingeniería

### 1. El Analizador Estricto de YAML en Go
El agente de AWS CodeBuild está programado en **Go (Golang)**. A diferencia del parser de CloudFormation, el parser de Go tiene particularidades estrictas:
* **No usar dos puntos con espacio (`: `) dentro de los comandos:** Si un comando de shell tiene `echo "Fase 1: ..."` sin que toda la línea esté entrecomillada, el parser interpreta `Fase 1:` como una clave de diccionario y falla con `Expected Commands[0] to be of string type: found subkeys instead`. Por ello, se usan flechas `->` o guiones en los mensajes.
* **Comentarios en su propia línea:** Los comentarios deben colocarse en su propia línea arriba de la directiva, evitando comentarios inline pegados a claves que abren listas (`commands:`).

### 2. Persistencia del Directorio de Trabajo (Working Directory)
En AWS CodeBuild, la sesión de la terminal de bash **persiste entre fases**:
* Como en la fase `build` se ejecutó `cd app`, la terminal permaneció dentro de `/src/app/`.
* Intentar ejecutar `cd app` nuevamente en `post_build` provocaba el error `cd: app: No such file or directory`.

---

[Volver a la Guía Principal](../README.md) | [Bitácora Técnica](../BITACORA_TECNICA.md)


