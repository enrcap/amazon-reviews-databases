# Estudiantes: Belén Cao
# Estudiantes: Enrique Capella
import pymysql
import pymongo
import json
from datetime import date
import configuracion


def conectar_mysql():
    """
    Establece una conexión con la base de datos MySQL
    """
    conexion = pymysql.connect(
        host=configuracion.MYSQL_HOST,
        port=configuracion.MYSQL_PORT,
        user=configuracion.MYSQL_USER,
        password=configuracion.MYSQL_PASS,
        database=configuracion.MYSQL_DB,
        charset="utf8mb4"
    )
    return conexion


def conectar_mongo():
    """
    Establece una conexión con MongoDB
    """
    mongo_client = pymongo.MongoClient(
        configuracion.MONGO_HOST,
        configuracion.MONGO_PORT
    )
    database = mongo_client[configuracion.MONGO_DB]
    collection = database[configuracion.MONGO_COLLECTION]
    return mongo_client, database, collection


def parsear_review_time(review_time_str):
    """
    Convierte el campo reviewTime al tipo date.
    """
    try:
        partes = review_time_str.replace(",", "").split()
        if len(partes) != 3:
            return None

        mes = int(partes[0])
        dia = int(partes[1])
        ano = int(partes[2])

        return date(ano, mes, dia)
    except (AttributeError, TypeError, ValueError):
        return None


def get_insert_category(category_name, cursor):
    """
    Obtiene el id de una categoría si ya existe.
    Si no existe, la inserta.
    """
    cursor.execute(
        "SELECT category_id FROM Categories WHERE category_name = %s",
        (category_name,)
    )
    fila = cursor.fetchone()

    if fila:
        return fila[0]

    cursor.execute(
        "INSERT INTO Categories (category_name) VALUES (%s)",
        (category_name,)
    )
    return cursor.lastrowid


def get_insert_user(reviewer_id, reviewer_name, cursor):
    """
    Inserta el usuario si no existe previamente.
    """
    cursor.execute(
        "SELECT reviewerID FROM Users WHERE reviewerID = %s",
        (reviewer_id,)
    )
    fila = cursor.fetchone()

    if fila:
        return fila[0]

    cursor.execute(
        "INSERT INTO Users (reviewerID, reviewerName) VALUES (%s, %s)",
        (reviewer_id, reviewer_name)
    )
    return reviewer_id


def get_insert_product(product_id, category_id, cursor):
    """
    Inserta el producto si no existe previamente.
    """
    cursor.execute(
        "SELECT product_id FROM Products WHERE product_id = %s",
        (product_id,)
    )
    fila = cursor.fetchone()

    if fila:
        return fila[0]

    cursor.execute(
        "INSERT INTO Products (product_id, category_id) VALUES (%s, %s)",
        (product_id, category_id)
    )
    return product_id


def insert_review_mysql(reviewer_id, product_id, overall, review_date,
                        unix_review_time, helpful_yes, helpful_total, cursor):
    """
    Inserta una review en MySQL.
    """
    cursor.execute(
        """
        INSERT INTO Reviews (
            reviewer_id, product_id, overall, review_date,
            unixReviewTime, helpful_yes, helpful_total
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            reviewer_id,
            product_id,
            overall,
            review_date,
            unix_review_time,
            helpful_yes,
            helpful_total
        )
    )
    return cursor.lastrowid


def insert_review_mongo(review_id, review, mongo_collection):
    """
    Inserta la parte textual de la review en MongoDB.
    """
    documento = {
        "review_id": review_id,
        "summary": review.get("summary", ""),
        "reviewText": review.get("reviewText", ""),
        "helpful": review.get("helpful", [])
    }

    mongo_collection.insert_one(documento)


def review_ya_existe(reviewer_id, product_id, unix_review_time, cursor):
    """
    Comprueba si una review ya existe en MySQL para no duplicarla.
    """
    cursor.execute(
        """
        SELECT review_id
        FROM Reviews
        WHERE reviewer_id = %s
          AND product_id = %s
          AND unixReviewTime = %s
        """,
        (reviewer_id, product_id, unix_review_time)
    )
    fila = cursor.fetchone()

    if fila:
        return fila[0]

    return None


def procesar_fichero(path, category_name, cursor, connection, collection):
    """
    Procesa el fichero nuevo e inserta sus datos en MySQL y MongoDB.
    """
    with open(path, "r", encoding="utf-8") as fichero:
        category_id = get_insert_category(category_name, cursor)
        insertadas = 0
        repetidas = 0
        procesadas = 0

        for linea in fichero:
            procesadas += 1
            review = json.loads(linea)

            reviewer_id = review.get("reviewerID")
            reviewer_name = review.get("reviewerName", "")

            product_id = review.get("asin")
            overall = float(review.get("overall", 0))
            review_date = parsear_review_time(review.get("reviewTime", ""))
            unix_review_time = int(review.get("unixReviewTime", 0))

            helpful = review.get("helpful", [0, 0])
            helpful_yes = helpful[0] if len(helpful) > 0 else 0
            helpful_total = helpful[1] if len(helpful) > 1 else 0

            review_existente = review_ya_existe(
                reviewer_id,
                product_id,
                unix_review_time,
                cursor
            )

            if review_existente is None:
                get_insert_user(reviewer_id, reviewer_name, cursor)
                get_insert_product(product_id, category_id, cursor)

                review_id = insert_review_mysql(
                    reviewer_id,
                    product_id,
                    overall,
                    review_date,
                    unix_review_time,
                    helpful_yes,
                    helpful_total,
                    cursor
                )

                insert_review_mongo(review_id, review, collection)
                insertadas += 1
            else:
                repetidas += 1

            if procesadas % 1000 == 0:
                print(f"Progreso: {procesadas} reviews leidas, {insertadas} insertadas y {repetidas} repetidas")

    connection.commit()
    print("Categoría cargada:", category_name)
    print("Reviews insertadas:", insertadas)
    print("Reviews repetidas:", repetidas)


def main():
    conexion_mysql = conectar_mysql()
    cursor_mysql = conexion_mysql.cursor()

    mongo_client, mongo_db, mongo_collection = conectar_mongo()

    procesar_fichero(
        configuracion.SPORTS_FILE,
        "Sports and Outdoors",
        cursor_mysql,
        conexion_mysql,
        mongo_collection
    )

    cursor_mysql.close()
    conexion_mysql.close()
    mongo_client.close()

    print("Carga del nuevo dataset finalizada.")


if __name__ == "__main__":
    main()
