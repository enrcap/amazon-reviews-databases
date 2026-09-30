# Estudiantes: Belén Cao
# Estudiantes: Enrique Capella
from neo4j import GraphDatabase
import pymysql
import math
import configuracion
import random


NEO4J_URI = configuracion.NEO4J_URI
NEO4J_USER = configuracion.NEO4J_USER
NEO4J_PASS = configuracion.NEO4J_PASS


def conectar_mysql():
    """
    Crea la conexion a MySQL con la base de datos configurada.
    """
    return pymysql.connect(
        host=configuracion.MYSQL_HOST,
        port=configuracion.MYSQL_PORT,
        user=configuracion.MYSQL_USER,
        password=configuracion.MYSQL_PASS,
        database=configuracion.MYSQL_DB,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def conectar_neo4j():
    """
    Crea la conexion con Neo4J
    """
    return GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASS)
    )


def pearson_correlation(reviews1, reviews2):
    """
    Calcula la correlacion de Pearson entre dos usuarios.
    reviews1 y reviews2 son diccionarios: {product_id: rating}
    """
    common_products = set(reviews1.keys()) & set(reviews2.keys())
    n = len(common_products)

    if n == 0:
        return None

    sum1 = sum(reviews1[p] for p in common_products)
    sum2 = sum(reviews2[p] for p in common_products)

    sum1_sq = sum(reviews1[p] ** 2 for p in common_products)
    sum2_sq = sum(reviews2[p] ** 2 for p in common_products)

    product_sum = sum(reviews1[p] * reviews2[p] for p in common_products)

    num = product_sum - (sum1 * sum2 / n)
    den = math.sqrt((sum1_sq - (sum1 ** 2) / n) * (sum2_sq - (sum2 ** 2) / n))

    if den == 0:
        return None

    return num / den


def get_top_users(n, connection):
    """
    Obtiene los n usuarios con mas reviews.
    """
    with connection.cursor() as cursor:
        sql = """
            SELECT reviewer_id, COUNT(*) AS total_reviews
            FROM Reviews
            GROUP BY reviewer_id
            ORDER BY total_reviews DESC
            LIMIT %s
        """
        cursor.execute(sql, (n,))
        return cursor.fetchall()


def get_reviews_by_user(reviewer_id, connection):
    """
    Devuelve las reviews de un usuario en formato: {product_id: overall}
    """
    reviews = {}

    with connection.cursor() as cursor:
        sql = """
            SELECT product_id, overall
            FROM Reviews
            WHERE reviewer_id = %s
        """
        cursor.execute(sql, (reviewer_id,))
        resultados = cursor.fetchall()

        for fila in resultados:
            reviews[fila["product_id"]] = float(fila["overall"])

    return reviews


def matriz_similaritud(users, connection):
    """
    Calcula la similitud entre cada pareja de usuarios.
    Solo guarda similitudes entre usuarios con articulos en comun.
    """
    user_reviews = {}

    for user in users:
        reviewer_id = user["reviewer_id"]
        user_reviews[reviewer_id] = get_reviews_by_user(reviewer_id, connection)

    similarities = {}

    for i in range(len(users)):
        for j in range(i + 1, len(users)):
            u1 = users[i]["reviewer_id"]
            u2 = users[j]["reviewer_id"]

            sim = pearson_correlation(user_reviews[u1], user_reviews[u2])

            if sim is not None:
                similarities[(u1, u2)] = sim

    return similarities


def clear_neo4j_graph(driver):
    """
    Elimina únicamente los nodos etiquetados AmazonReviewsProject y sus relaciones.
    """
    with driver.session(database=configuracion.NEO4J_DATABASE) as session:
        session.run("MATCH (n:AmazonReviewsProject) DETACH DELETE n")
    print("Neo4J: nodos del proyecto eliminados")


def create_users_nodes(driver, users):
    """
    Crea los nodos de usuarios en Neo4J.
    """
    with driver.session(database=configuracion.NEO4J_DATABASE) as session:
        for user in users:
            session.run(
                """
                CREATE (u:User:AmazonReviewsProject {
                    reviewer_id: $reviewer_id,
                    total_reviews: $total_reviews
                })
                """,
                reviewer_id=user["reviewer_id"],
                total_reviews=int(user["total_reviews"])
            )

    print("Neo4J: nodos de usuarios creados.")


def create_similarity_relationships(driver, similarities):
    """
    Crea las relaciones de similitud entre usuarios.
    """
    with driver.session(database=configuracion.NEO4J_DATABASE) as session:
        for (u1, u2), sim in similarities.items():
            session.run(
                """
                MATCH (a:User:AmazonReviewsProject {reviewer_id: $u1}), (b:User:AmazonReviewsProject {reviewer_id: $u2})
                CREATE (a)-[:SIMILAR {similarity: $sim}]->(b)
                CREATE (b)-[:SIMILAR {similarity: $sim}]->(a)
                """,
                u1=u1,
                u2=u2,
                sim=float(sim)
            )

    print("Neo4J: relaciones de similitud creadas.")


def mostrar_usuario_con_mas_vecinos(driver):
    """
    Muestra por pantalla el usuario con mas vecinos en Neo4J.
    """
    with driver.session(database=configuracion.NEO4J_DATABASE) as session:
        result = session.run(
            """
            MATCH (u:User:AmazonReviewsProject)-[:SIMILAR]->(v:User:AmazonReviewsProject)
            RETURN u.reviewer_id AS reviewer_id, COUNT(v) AS vecinos
            ORDER BY vecinos DESC
            LIMIT 1
            """
        )

        fila = result.single()

        if fila is None:
            print("No hay usuarios con vecinos.")
        else:
            print("Usuario con más vecinos:")
            print("Reviewer ID:", fila["reviewer_id"])
            print("Número de vecinos:", fila["vecinos"])




# PARTE 2

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
    return [fila["category_name"] for fila in cursor.fetchall()]


def pedir_categoria(cursor):
    """
    Muestra las categorias obtenidas y le pide al usuario que seleccione una
    """
    categorias = obtener_categorias(cursor)

    print("\nCategorias disponibles:")
    for i in range(len(categorias)):
        print(f"{i+1}. {categorias[i]}")

    opcion = input("Introduzca la categoría de la que desee ver sus reviews: ").strip()

    try:
        indice = int(opcion) - 1
        if 0 <= indice < len(categorias):
            return categorias[indice]
    except ValueError:
        print("Opción no válida")
        return None
    

def pedir_numero_articulos():
    """
    Pide al usuario el numero de articulos aleatorios que quiere seleccionar
    """
    opcion = input("Introduzca el número de artículos aleatorios que quiere mostrar: ").strip()

    try:
        numero = int(opcion)
        if numero > 0:
            return numero
    except ValueError:
        print("Número no válido")
        return None


def obtener_articulos_categoria(categoria, cursor):
    """
    Obtiene todos los articulos de una categoria dada
    """
    query = """
        SELECT p.product_id
        FROM Products p
        JOIN Categories c ON p.category_id = c.category_id
        WHERE c.category_name = %s
    """
    cursor.execute(query, (categoria,))
    resultados = cursor.fetchall()

    return [fila["product_id"] for fila in resultados]
 

def seleccionar_articulos_aleatorios(categoria, numero_articulos):
    """
    Selecciona un numero de articulos aleatorios de la categoria indicada
    """
    conexion = conectar_mysql()
    cursor = conexion.cursor()

    articulos = obtener_articulos_categoria(categoria, cursor)

    cursor.close()
    conexion.close()

    if not articulos:
        print("No hay artículos en esa categoría.")
        return []

    if numero_articulos > len(articulos):
        numero_articulos = len(articulos)

    return random.sample(articulos, numero_articulos)


def obtener_reviews_articulos(articulos):
    """
    Obtiene todas las reviews de los articulos indicados
    """
    if not articulos:
        return []

    conexion = conectar_mysql()
    cursor = conexion.cursor()

    marcadores = ", ".join(["%s"] * len(articulos))
    query = f"""
        SELECT reviewer_id, product_id, overall, review_date, unixReviewTime
        FROM Reviews
        WHERE product_id IN ({marcadores})
    """
    cursor.execute(query, articulos)
    resultados = cursor.fetchall()
    cursor.close()
    conexion.close()
    return resultados


def clear_grafo(driver):
    """
    Elimina todos los nodos y relaciones previos del grafo
    """
    with driver.session(database=configuracion.NEO4J_DATABASE) as session:
        session.run("MATCH (n:AmazonReviewsProject) DETACH DELETE n")


def crear_nodos_articulos(driver, articulos):
    """
    Crea en Neo4J los nodos de los articulos seleccionados
    """
    with driver.session(database=configuracion.NEO4J_DATABASE) as session:
        for articulo in articulos:
            session.run("MERGE (a:Articulo:AmazonReviewsProject {product_id: $product_id})", product_id=articulo)


def crear_nodos_usuarios(driver, reviews):
    """
    Crea en Neo4J los nodos de los usuarios que han puntuado los articulos
    """
    usuarios = set()

    for review in reviews:
        usuarios.add(review["reviewer_id"])

    with driver.session(database=configuracion.NEO4J_DATABASE) as session:
        for usuario in usuarios:
            session.run("MERGE (u:Usuario:AmazonReviewsProject {reviewer_id: $reviewer_id})", reviewer_id=usuario)


def crear_relaciones_usuario_articulo(driver, reviews):
    """
    Crea las relaciones entre usuarios y articulos con las propiedades
    de nota y tiempo de la review
    """
    with driver.session(database=configuracion.NEO4J_DATABASE) as session:
        for review in reviews:
            review_date = review["review_date"]
            if review_date is not None:
                review_date = str(review_date)

            session.run(
                """
                MATCH (u:Usuario:AmazonReviewsProject {reviewer_id: $reviewer_id})
                MATCH (a:Articulo:AmazonReviewsProject {product_id: $product_id})
                CREATE (u)-[:PUNTUO {
                    overall: $overall,
                    review_date: $review_date,
                    unixReviewTime: $unixReviewTime
                }]->(a)
                """,
                reviewer_id=review["reviewer_id"],
                product_id=review["product_id"],
                overall=float(review["overall"]),
                review_date=review_date,
                unixReviewTime=int(review["unixReviewTime"]) if review["unixReviewTime"] is not None else None
            )


def mostrar_articulos_seleccionados(articulos):
    """
    Muestra por pantalla los articulos aleatorios seleccionados
    """
    print("\nArtículos seleccionados:")
    for articulo in articulos:
        print(articulo)


def obtener_primeros_400_usuarios(connection):
    """
    Obtiene los primeros 400 usuarios ordenados por nombre.
    """
    with connection.cursor() as cursor:
        query = """
            SELECT reviewerID, reviewerName
            FROM Users
            ORDER BY reviewerName
            LIMIT 400
        """
        cursor.execute(query)
        return cursor.fetchall()
    

def obtener_tipos_por_usuario(usuarios, connection):
    """
    Obtiene, para cada usuario, los tipos de articulo que ha puntuado
    y cuántos articulos ha puntuado de cada tipo.
    Solo devuelve los usuarios que han puntuado articulos de al menos dos tipos distintos.
    """
    if not usuarios:
        return {}

    reviewer_ids = [usuario["reviewerID"] for usuario in usuarios]
    marcadores = ", ".join(["%s"] * len(reviewer_ids))

    with connection.cursor() as cursor:
        query = f"""
            SELECT r.reviewer_id, c.category_name, COUNT(*) AS cantidad
            FROM Reviews r
            JOIN Products p ON r.product_id = p.product_id
            JOIN Categories c ON p.category_id = c.category_id
            WHERE r.reviewer_id IN ({marcadores})
            GROUP BY r.reviewer_id, c.category_name
            ORDER BY r.reviewer_id, c.category_name
        """
        cursor.execute(query, reviewer_ids)
        resultados = cursor.fetchall()

    datos = {}

    for fila in resultados:
        reviewer_id = fila["reviewer_id"]
        category_name = fila["category_name"]
        cantidad = fila["cantidad"]

        if reviewer_id not in datos:
            datos[reviewer_id] = {}

        datos[reviewer_id][category_name] = cantidad

    final = {}
    for reviewer_id, tipos in datos.items():
        if len(tipos) >= 2:
            final[reviewer_id] = tipos

    return final


def crear_nodos_usuarios_tipos(driver, usuarios, datos_tipos):
    """
    Crea los nodos de usuarios que han puntuado articulos de al menos dos tipos distintos.
    """
    with driver.session(database=configuracion.NEO4J_DATABASE) as session:
        for usuario in usuarios:
            reviewer_id = usuario["reviewerID"]
            reviewer_name = usuario["reviewerName"]

            if reviewer_id in datos_tipos:
                session.run(
                    """
                    MERGE (u:Usuario:AmazonReviewsProject {reviewer_id: $reviewer_id})
                    SET u.reviewer_name = $reviewer_name
                    """,
                    reviewer_id=reviewer_id,
                    reviewer_name=reviewer_name
                )


def crear_nodos_tipos_articulo(driver, datos_tipos):
    """
    Crea los nodos de tipos de articulo.
    """
    tipos = set()

    for reviewer_id in datos_tipos:
        for tipo in datos_tipos[reviewer_id]:
            tipos.add(tipo)

    with driver.session(database=configuracion.NEO4J_DATABASE) as session:
        for tipo in tipos:
            session.run(
                """
                MERGE (t:TipoArticulo:AmazonReviewsProject {nombre: $nombre})
                """,
                nombre=tipo
            )


def crear_relaciones_usuario_tipo(driver, datos_tipos):
    """
    Crea las relaciones entre usuario y tipo de articulo,
    con una propiedad que indica la cantidad de articulos consumidos de ese tipo.
    """
    with driver.session(database=configuracion.NEO4J_DATABASE) as session:
        for reviewer_id in datos_tipos:
            tipos = datos_tipos[reviewer_id]

            for tipo, cantidad in tipos.items():
                session.run(
                    """
                    MATCH (u:Usuario:AmazonReviewsProject {reviewer_id: $reviewer_id})
                    MATCH (t:TipoArticulo:AmazonReviewsProject {nombre: $tipo})
                    CREATE (u)-[:CONSUME {cantidad: $cantidad}]->(t)
                    """,
                    reviewer_id=reviewer_id, tipo=tipo, cantidad=int(cantidad))


def obtener_articulos_populares(connection):
    """
    Obtiene los 5 artículos más populares que tengan menos de 40 reviews.
    """
    with connection.cursor() as cursor:
        query = """
            SELECT product_id, COUNT(*) AS total_reviews
            FROM Reviews
            GROUP BY product_id
            HAVING COUNT(*) < 40
            ORDER BY total_reviews DESC
            LIMIT 5
        """
        cursor.execute(query)
        return cursor.fetchall()
    

def obtener_reviews_articulos_populares(articulos, connection):
    """
    Obtiene todas las reviews de los artículos seleccionados.
    """
    if not articulos:
        return []

    product_ids = [articulo["product_id"] for articulo in articulos]
    marcadores = ", ".join(["%s"] * len(product_ids))

    with connection.cursor() as cursor:
        query = f"""
            SELECT reviewer_id, product_id, overall, review_date, unixReviewTime
            FROM Reviews
            WHERE product_id IN ({marcadores})
        """
        cursor.execute(query, product_ids)
        return cursor.fetchall()


def crear_nodos_articulos_populares(driver, articulos):
    """
    Crea en Neo4J los nodos de los artículos populares seleccionados.
    """
    with driver.session(database=configuracion.NEO4J_DATABASE) as session:
        for articulo in articulos:
            session.run(
                """
                MERGE (a:Articulo:AmazonReviewsProject {product_id: $product_id})
                SET a.total_reviews = $total_reviews
                """,
                product_id=articulo["product_id"],
                total_reviews=int(articulo["total_reviews"])
            )


def crear_nodos_usuarios_populares(driver, reviews):
    """
    Crea en Neo4J los nodos de los usuarios que han puntuado los artículos populares.
    """
    usuarios = set()

    for review in reviews:
        usuarios.add(review["reviewer_id"])

    with driver.session(database=configuracion.NEO4J_DATABASE) as session:
        for usuario in usuarios:
            session.run("MERGE (u:Usuario:AmazonReviewsProject {reviewer_id: $reviewer_id})", reviewer_id=usuario)


def crear_relaciones_usuario_articulo_populares(driver, reviews):
    """
    Crea relaciones entre usuarios y artículos con las propiedades
    de nota y tiempo de la review.
    """
    with driver.session(database=configuracion.NEO4J_DATABASE) as session:
        for review in reviews:
            review_date = review["review_date"]
            if review_date is not None:
                review_date = str(review_date)

            session.run(
                """
                MATCH (u:Usuario:AmazonReviewsProject {reviewer_id: $reviewer_id})
                MATCH (a:Articulo:AmazonReviewsProject {product_id: $product_id})
                CREATE (u)-[:PUNTUO {
                    overall: $overall,
                    review_date: $review_date,
                    unixReviewTime: $unixReviewTime
                }]->(a)
                """,
                reviewer_id=review["reviewer_id"],
                product_id=review["product_id"],
                overall=float(review["overall"]),
                review_date=review_date,
                unixReviewTime=int(review["unixReviewTime"]) if review["unixReviewTime"] is not None else None
            )


def calcular_articulos_en_comun(reviews):
    """
    Calcula cuántos artículos tienen en común los usuarios.
    Devuelve un diccionario:
    {(usuario1, usuario2): cantidad_en_comun}
    """
    articulos_por_usuario = {}

    for review in reviews:
        reviewer_id = review["reviewer_id"]
        product_id = review["product_id"]

        if reviewer_id not in articulos_por_usuario:
            articulos_por_usuario[reviewer_id] = set()

        articulos_por_usuario[reviewer_id].add(product_id)

    usuarios = list(articulos_por_usuario.keys())
    comunes = {}

    for i in range(len(usuarios)):
        for j in range(i + 1, len(usuarios)):
            u1 = usuarios[i]
            u2 = usuarios[j]

            interseccion = articulos_por_usuario[u1] & articulos_por_usuario[u2]

            if len(interseccion) > 0:
                comunes[(u1, u2)] = len(interseccion)

    return comunes


def crear_relaciones_usuarios_comun(driver, comunes):
    """
    Crea relaciones entre usuarios indicando cuántos artículos han puntuado en común.
    """
    with driver.session(database=configuracion.NEO4J_DATABASE) as session:
        for (u1, u2), cantidad in comunes.items():
            session.run(
                """
                MATCH (a:Usuario:AmazonReviewsProject {reviewer_id: $u1})
                MATCH (b:Usuario:AmazonReviewsProject {reviewer_id: $u2})
                CREATE (a)-[:EN_COMUN {cantidad: $cantidad}]->(b)
                CREATE (b)-[:EN_COMUN {cantidad: $cantidad}]->(a)
                """,
                u1=u1,
                u2=u2,
                cantidad=int(cantidad)
            )


def mostrar_menu():
    print("\nMENÚ NEO4J")
    print("0. Salir")
    print("1. Similitud entre usuarios")
    print("2. Enlaces entre usuarios y articulos")
    print("3. Usuarios y tipos de articulo")
    print("4. Articulos populares y articulos en comun")


def main():
    seguir = True

    while seguir:
        mostrar_menu()
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            numero_usuarios = configuracion.TOP_USUARIOS

            mysql_connection = conectar_mysql()
            top_users = get_top_users(numero_usuarios, mysql_connection)
            similarities = matriz_similaritud(top_users, mysql_connection)
            mysql_connection.close()

            driver = conectar_neo4j()

            clear_neo4j_graph(driver)
            create_users_nodes(driver, top_users)
            create_similarity_relationships(driver, similarities)
            mostrar_usuario_con_mas_vecinos(driver)

            driver.close()

            print("\nUsuarios con mas vecinos calculados")

        elif opcion == "2":
            mysql_connection = conectar_mysql()
            cursor = mysql_connection.cursor()
            categoria = pedir_categoria(cursor)
            numero_articulos = pedir_numero_articulos()
            cursor.close()
            mysql_connection.close()

            if categoria and numero_articulos:
                articulos = seleccionar_articulos_aleatorios(categoria, numero_articulos)

                if articulos:

                    reviews = obtener_reviews_articulos(articulos)

                    if reviews:
                        driver = conectar_neo4j()
                        clear_neo4j_graph(driver)
                        crear_nodos_articulos(driver, articulos)
                        crear_nodos_usuarios(driver, reviews)
                        crear_relaciones_usuario_articulo(driver, reviews)
                        driver.close()

                        print("\nReviews obtenidas")
                    else:
                        print("No hay reviews para los articulos seleccionados")
                else:
                    print("No se pueden seleccionar articulos")
            else:
                print("Datos incorrectos")

        elif opcion == "3":
            mysql_connection = conectar_mysql()
            primeros_usuarios = obtener_primeros_400_usuarios(mysql_connection)
            datos_tipos = obtener_tipos_por_usuario(primeros_usuarios, mysql_connection)
            mysql_connection.close()

            if datos_tipos:
                driver = conectar_neo4j()
                clear_neo4j_graph(driver)
                crear_nodos_usuarios_tipos(driver, primeros_usuarios, datos_tipos)
                crear_nodos_tipos_articulo(driver, datos_tipos)
                crear_relaciones_usuario_tipo(driver, datos_tipos)
                driver.close()

                print("\nCalculados los usuarios con más de un tipo de artículo")
            else:
                print("No se encontraron usuarios con más de un tipo de artículo.")

        elif opcion == "4":
            mysql_connection = conectar_mysql()
            articulos_populares = obtener_articulos_populares(mysql_connection)

            if articulos_populares:
                reviews_populares = obtener_reviews_articulos_populares(articulos_populares, mysql_connection)
                mysql_connection.close()

                if reviews_populares:
                    comunes = calcular_articulos_en_comun(reviews_populares)

                    driver = conectar_neo4j()
                    clear_neo4j_graph(driver)
                    crear_nodos_articulos_populares(driver, articulos_populares)
                    crear_nodos_usuarios_populares(driver, reviews_populares)
                    crear_relaciones_usuario_articulo_populares(driver, reviews_populares)
                    crear_relaciones_usuarios_comun(driver, comunes)
                    driver.close()

                    print("\nArticulos populares calculados")
                else:
                    print("No hay reviews para los articulos populares seleccionados")
            else:
                mysql_connection.close()
                print("No se encontraron articulos populares con menos de 40 reviews")

        elif opcion == "0":
            print("Saliendo del programa...")
            seguir = False

        else:
            print("Opcion no valida")


if __name__ == "__main__":
    main()
