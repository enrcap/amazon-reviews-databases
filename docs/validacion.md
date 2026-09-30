# Validación de la preparación del repositorio

Fecha: 30 de septiembre de 2026.

## Comprobaciones realizadas

- Análisis de sintaxis de los seis módulos Python: correcto.
- Ocho pruebas unitarias: correctas. Cubren fechas válidas e inválidas, Pearson positivo/negativo y casos indefinidos, productos comunes, rutas absolutas, alcance del borrado del grafo y exclusión de productos ya valorados en la recomendación.
- Validación de Compose con `docker compose --env-file .env.example -f compose.yaml config --quiet`: correcta.
- Revisión del alcance de las consultas del grafo: todas las etiquetas de nodos del módulo incluyen `AmazonReviewsProject`.
- Revisión visual de los documentos y de la captura utilizada en el README.

Las pruebas se ejecutaron con Python 3.12.14 y las librerías PyMySQL 1.1.2, pymongo 4.15.1, neo4j 5.28.2 y python-dotenv 1.1.1. La instalación estándar con pip encontró un problema de permisos del entorno de revisión; para estas pruebas se cargaron sus distribuciones oficiales, verificadas por SHA-256, en una carpeta aislada. Esa carpeta no forma parte del repositorio.

## Qué no se ha verificado

No se ha ejecutado la carga completa ni una prueba de integración con los tres servidores durante esta preparación. Docker Desktop no estaba iniciado y los JSON originales no estaban incluidos en el ZIP. La validación de Compose comprueba la configuración, no la descarga de imágenes ni el arranque de contenedores.

La consulta del recomendador se ha probado con datos sintéticos en SQLite y un adaptador de marcadores de parámetros. Esto verifica filtrado y ordenación, pero no certifica el comportamiento operativo ni el rendimiento de MySQL. El reseteo de Neo4j se ha comprobado con un driver simulado; no se ha conectado a una base real ni borrado datos existentes.

Las gráficas y capturas conservadas son resultados documentados en la entrega académica original. No son pruebas de una nueva ejecución en el entorno de revisión.
