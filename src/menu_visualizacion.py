# Estudiantes: Belén Cao
# Estudiantes: Enrique Capella
import re
import matplotlib.pyplot as plt
import pymongo
import pymysql
import configuracion
from wordcloud import WordCloud

 
def conectar_mysql():
    """
    Crea la conexion a MySQL con la base de datos del script de configuracion
    """
    return pymysql.connect(
        host=configuracion.MYSQL_HOST,
        port=configuracion.MYSQL_PORT,
        user=configuracion.MYSQL_USER,
        password=configuracion.MYSQL_PASS,
        database=configuracion.MYSQL_DB,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.Cursor,
    )
 
 
def conectar_mongo():
    """
    Devuelve el cliente, la base de datos y la coleccion usada de MongoDB.
    """
    mongo_client = pymongo.MongoClient(configuracion.MONGO_HOST, configuracion.MONGO_PORT)
    database = mongo_client[configuracion.MONGO_DB]
    collection = database[configuracion.MONGO_COLLECTION]
    return mongo_client, database, collection
 
 
def obtener_categorias(cursor):
    """
    Devuelve las categoias disponibles de la base de datos usada
    """
    cursor.execute(
        """
        SELECT category_name
        FROM Categories
        ORDER BY category_name
        """
    )
    return [fila[0] for fila in cursor.fetchall()]

 
def pedir_categoria(cursor):
    """
    Muestra las categorias obtenidas y le pide al usuario que seleccione una
    """
    categorias = obtener_categorias(cursor)

    print("\nCategorias disponibles:")
    print("0. Todas")
    for i in range(len(categorias)):
        print(f"{i+1}. {categorias[i]}")

    opcion = input("Introduzca la categoría de la que desee ver sus reviews: ").strip()

    if opcion == "0":
        return "Todas"

    try:
        indice = int(opcion) - 1
        if 0 <= indice < len(categorias):
            return categorias[indice]
    except ValueError:
        print("Opción no válida")
        return None
    

def mostrar_reviews_por_anos(categoria):
    """
    Muestra un histograma con el numero de reviews por anio.
    """
    conexion = conectar_mysql() 
    cursor = conexion.cursor() 
    if categoria == "Todas": 
        query = """ 
            SELECT YEAR(review_date) AS ano, COUNT(*) AS total 
            FROM Reviews 
            WHERE review_date IS NOT NULL 
            GROUP BY YEAR(review_date) 
            ORDER BY ano 
        """ 
        cursor.execute(query) 
    else: 
        query = """ 
            SELECT YEAR(r.review_date) AS ano, COUNT(*) AS total 
            FROM Reviews r 
            JOIN Products p ON r.product_id = p.product_id 
            JOIN Categories c ON p.category_id = c.category_id 
            WHERE r.review_date IS NOT NULL AND c.category_name = %s 
            GROUP BY YEAR(r.review_date) 
            ORDER BY ano 
        """ 
        cursor.execute(query, (categoria,)) 
    
    resultados = cursor.fetchall() 
    cursor.close() 
    conexion.close()

    if not resultados: 
        print("No hay datos") 
        return 
    
    anos = [fila[0] for fila in resultados] 
    total = [fila[1] for fila in resultados] 

    plt.bar(anos, total) 
    plt.xlabel("Años") 
    plt.ylabel("Número de reviews") 
    if categoria == "Todas": 
        plt.title("Reviews por año de todos los productos") 
    else: 
        plt.title(f"Reviews por año de los productos de {categoria}") 
    plt.xticks(anos, rotation=45) 
    plt.show()
 
 
def mostrar_popularidad_articulos(categoria):
    """
    Muestra la curva de popularidad de articulos ordenados de mayor a menor.
    """
    conexion = conectar_mysql()
    cursor = conexion.cursor()

    if categoria == "Todas":
        query = """
            SELECT r.product_id, COUNT(*) AS total_reviews
            FROM Reviews r
            GROUP BY r.product_id
            ORDER BY total_reviews DESC
        """
        cursor.execute(query)
    else:
        query = """
            SELECT r.product_id, COUNT(*) AS total_reviews
            FROM Reviews r
            JOIN Products p ON r.product_id = p.product_id
            JOIN Categories c ON p.category_id = c.category_id
            WHERE c.category_name = %s
            GROUP BY r.product_id
            ORDER BY total_reviews DESC
        """
        cursor.execute(query, (categoria,))

    resultados = cursor.fetchall()
    cursor.close()
    conexion.close()

    if not resultados:
        print("No hay datos")
        return

    reviews_por_articulo = [fila[1] for fila in resultados]
    posiciones = list(range(1, len(reviews_por_articulo) + 1))

    plt.plot(posiciones, reviews_por_articulo)
    plt.xlabel("Artículos")
    plt.ylabel("Número de reviews")
    if categoria == "Todas":
        plt.title("Evolucion de popularidad de todos los productos")
    else:
        plt.title(f"Evolucion de popularidad de los productos de {categoria}")
    plt.show()


def mostrar_histograma_por_nota(categoria):
    """
    Muestra un histograma con el numero de reviews por nota (overall).
    Puede hacerse para todas las categorias o una categoria concreta.
    """
    conexion = conectar_mysql()
    cursor = conexion.cursor()

    if categoria == "Todas":
        query = """
            SELECT overall, COUNT(*) AS total
            FROM Reviews
            GROUP BY overall
            ORDER BY overall
        """
        cursor.execute(query)
    else:
        query = """
            SELECT r.overall, COUNT(*) AS total
            FROM Reviews r
            JOIN Products p ON r.product_id = p.product_id
            JOIN Categories c ON p.category_id = c.category_id
            WHERE c.category_name = %s
            GROUP BY r.overall
            ORDER BY r.overall
        """
        cursor.execute(query, (categoria,))

    resultados = cursor.fetchall()
    cursor.close()
    conexion.close()

    if not resultados:
        print("No hay datos")
        return

    notas_dict = {int(fila[0]): fila[1] for fila in resultados}
    notas = [1, 2, 3, 4, 5]
    totales = [notas_dict.get(nota, 0) for nota in notas]

    plt.bar(notas, totales)
    plt.xlabel("Nota")
    plt.ylabel("Número de reviews")

    if categoria == "Todas":
        plt.title("Reviews por nota de todos los productos")
    else:
        plt.title(f"Reviews por nota de los productos de {categoria}")

    plt.xticks(notas)
    plt.tight_layout()
    plt.show()


def mostrar_evolucion_reviews_tiempo():
    """
    Muestra la evolucion acumulada del numero de reviews a lo largo del tiempo
    para todas las categorias.
    """
    conexion = conectar_mysql()
    cursor = conexion.cursor()

    query = """
        SELECT c.category_name, r.unixReviewTime
        FROM Reviews r
        JOIN Products p ON r.product_id = p.product_id
        JOIN Categories c ON p.category_id = c.category_id
        WHERE r.unixReviewTime IS NOT NULL
        ORDER BY c.category_name, r.unixReviewTime
    """
    cursor.execute(query)
    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    if not resultados:
        print("No hay datos")
        return

    datos_categoria = {}

    for categoria, tiempo in resultados:
        if categoria not in datos_categoria:
            datos_categoria[categoria] = []
        datos_categoria[categoria].append(tiempo)

    for categoria, tiempos in datos_categoria.items():
        acumuladas = list(range(1, len(tiempos) + 1))
        plt.plot(tiempos, acumuladas, label=categoria)

    plt.xlabel("Tiempo")
    plt.ylabel("Número de reviews hasta el momento")
    plt.title("Evolucion de las reviews a lo largo del tiempo para todas las categorias")
    plt.legend()
    plt.show()


def mostrar_histograma_reviews_por_usuario():
    """
    Muestra un histograma donde el eje x indica el numero de reviews
    y el eje y indica el numero de usuarios que han hecho esa cantidad de reviews.
    No distingue por categoria.
    """
    conexion = conectar_mysql()
    cursor = conexion.cursor()

    query = """
        SELECT reviews_por_usuario, COUNT(*) AS numero_usuarios
        FROM (
            SELECT reviewer_id, COUNT(*) AS reviews_por_usuario
            FROM Reviews
            GROUP BY reviewer_id
        ) AS subconsulta
        GROUP BY reviews_por_usuario
        ORDER BY reviews_por_usuario
    """
    cursor.execute(query)
    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    if not resultados:
        print("No hay datos")
        return

    numero_reviews = [fila[0] for fila in resultados]
    numero_usuarios = [fila[1] for fila in resultados]

    plt.bar(numero_reviews, numero_usuarios)
    plt.xlabel("Numero de reviews")
    plt.ylabel("Número de usuarios")
    plt.title("Reviews por usuario")
    plt.show()


def mostrar_nube_palabras_categoria(categoria):
    """
    Muestra una nube de palabras usando el campo summary
    para una categoria concreta.
    No permite 'Todas'.
    """
    if categoria == "Todas" or categoria is None:
        print("Debes elegir una categoria concreta.")
        return

    conexion = conectar_mysql()
    cursor = conexion.cursor()

    query = """
        SELECT r.review_id
        FROM Reviews r
        JOIN Products p ON r.product_id = p.product_id
        JOIN Categories c ON p.category_id = c.category_id
        WHERE c.category_name = %s
    """
    cursor.execute(query, (categoria,))
    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    if not resultados:
        print("No hay datos para esa categoria.")
        return

    review_ids = [fila[0] for fila in resultados]
    mongo_client, database, collection = conectar_mongo()
    documentos = collection.find(
        {"review_id": {"$in": review_ids}},
        {"summary": 1, "_id": 0}
    )

    textos = []
    for doc in documentos:
        summary = doc.get("summary", "")
        if summary:
            textos.append(summary)

    mongo_client.close()
    if not textos:
        print("No hay summaries para esa categoria.")
        return
    texto_completo = " ".join(textos)

    palabras = re.findall(r"\b\w+\b", texto_completo.lower())
    palabras_filtradas = [palabra for palabra in palabras if len(palabra) > 3]

    if not palabras_filtradas:
        print("No hay suficientes palabras para generar la nube.")
        return

    texto_final = " ".join(palabras_filtradas)
    nube = WordCloud(width=1000, height=500, background_color="white").generate(texto_final)

    plt.imshow(nube, interpolation="bilinear")
    plt.axis("off")
    plt.title(f"Nube de palabras - {categoria}")
    plt.show()


def mostrar_nota_media_por_categoria():
    """
    Muestra una grafica de barras con la nota media (overall)
    de cada categoria.
    """
    conexion = conectar_mysql()
    cursor = conexion.cursor()

    query = """
        SELECT c.category_name, AVG(r.overall) AS media_nota
        FROM Reviews r
        JOIN Products p ON r.product_id = p.product_id
        JOIN Categories c ON p.category_id = c.category_id
        GROUP BY c.category_name
        ORDER BY c.category_name
    """
    cursor.execute(query)
    resultados = cursor.fetchall()
    cursor.close()
    conexion.close()

    if not resultados:
        print("No hay datos")
        return

    categorias = [fila[0] for fila in resultados]
    medias = [float(fila[1]) for fila in resultados]

    plt.bar(categorias, medias)
    plt.xlabel("Categoria")
    plt.ylabel("Nota media")
    plt.title("Nota media por categoria")
    plt.xticks(rotation=45)
    plt.show()


def mostrar_menu():
    print("\n MENU DE VISUALIZACION")
    print("1. Evolucion de reviews por años")
    print("2. Evolucion de la popularidad de los articulos")
    print("3. Histograma por nota")
    print("4. Evolucion de las reviews a lo largo del tiempo")
    print("5. Histograma de reviews por usuario")
    print("6. Nube de palabras por categoria")
    print("7. Nota media por categoria")
    print("0. Salir")


def main():
    seguir = True

    while seguir:
        mostrar_menu()
        opcion = input("Seleccione una opcion: ").strip()

        if opcion == "1":
            conexion = conectar_mysql()
            cursor = conexion.cursor()
            categoria = pedir_categoria(cursor)
            cursor.close()
            conexion.close()

            if categoria is not None:
                mostrar_reviews_por_anos(categoria)

        elif opcion == "2":
            conexion = conectar_mysql()
            cursor = conexion.cursor()
            categoria = pedir_categoria(cursor)
            cursor.close()
            conexion.close()
            if categoria is not None:
                mostrar_popularidad_articulos(categoria)
    
        elif opcion == "3":
            conexion = conectar_mysql()
            cursor = conexion.cursor()
            categoria = pedir_categoria(cursor)
            cursor.close()
            conexion.close()

            if categoria is not None:
                mostrar_histograma_por_nota(categoria)

        elif opcion == "4":
            mostrar_evolucion_reviews_tiempo()

        elif opcion == "5":
            mostrar_histograma_reviews_por_usuario()

        elif opcion == "6":
            conexion = conectar_mysql()
            cursor = conexion.cursor()
            categoria = pedir_categoria(cursor)
            cursor.close()
            conexion.close()

            if categoria is not None and categoria != "Todas":
                mostrar_nube_palabras_categoria(categoria)
            else:
                print("Para la nube de palabras debes elegir una categoria concreta.")

        elif opcion == "7":
            mostrar_nota_media_por_categoria()

        elif opcion == "0":
            print("Saliendo del programa...")
            seguir = False

        else:
            print("Opción no valida. Inténtelo de nuevo.")


if __name__ == "__main__":
    main()
