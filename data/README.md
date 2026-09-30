# Datos de entrada

Se utilizan los subconjuntos **5-core de Amazon Reviews 2014** publicados por el grupo de Julian McAuley (UC San Diego):

[Página oficial y descargas](https://cseweb.ucsd.edu/~jmcauley/datasets/amazon/links.html).

| Archivo esperado | Reviews en el subconjunto publicado | Uso |
| --- | ---: | --- |
| `Toys_and_Games_5.json` | 167.597 | Carga inicial |
| `Video_Games_5.json` | 231.780 | Carga inicial |
| `Digital_Music_5.json` | 64.706 | Carga inicial |
| `Musical_Instruments_5.json` | 10.261 | Carga inicial |
| `Sports_and_Outdoors_5.json` | 296.337 | Ampliación |

Las cifras describen los subconjuntos de origen, no una carga verificada en esta preparación del repositorio. Los cuatro iniciales suman 474.344 reviews; los cinco, 770.681.

Descargar los archivos de reviews 5-core, descomprimir los `.gz` y colocarlos en esta carpeta, o cambiar sus rutas en `.env`. El código espera un objeto JSON por línea, sin un array exterior. No utiliza los archivos de metadatos ni los de “ratings only”.

Campos esperados: `reviewerID`, `asin`, `reviewerName`, `helpful`, `reviewText`, `overall`, `summary`, `unixReviewTime` y `reviewTime`. La página de origen recoge las publicaciones y condiciones de uso que deben consultarse antes de redistribuir los datos.

Los JSON y los volcados de bases de datos no se incluyen en este repositorio. El enlace privado o docente facilitado en el enunciado tampoco se publica.
