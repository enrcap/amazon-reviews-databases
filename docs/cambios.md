# Preparación para el portfolio

Se conservan los seis módulos y la lógica principal de la entrega. La memoria y el póster se copian sin modificar su contenido.

Cambios realizados para publicar el repositorio:

- Credenciales extraídas de `configuracion.py` a variables de entorno y `.env`, con una plantilla pública sin secretos.
- Rutas de datos resueltas desde la raíz del proyecto para poder ejecutar los scripts desde distintos directorios.
- Validación del nombre de la base MySQL antes de interpolarlo en las instrucciones de creación y selección.
- Base de Neo4j seleccionable mediante `NEO4J_DATABASE`.
- Creación, consultas y borrado de nodos de Neo4j limitados mediante `AmazonReviewsProject`.
- Captura de errores de fechas limitada a tipos de error esperados.
- README, esquema relacional, instrucciones de datos, dependencias, pruebas de lógica y Compose opcional.
- Exclusión de cachés, credenciales y archivos grandes de datos.

No se han añadido resultados experimentales, un modelo KNN ni métricas de recomendación. Las capturas proceden de la entrega académica original. El enunciado se ha usado como referencia para la revisión y no se redistribuye.
