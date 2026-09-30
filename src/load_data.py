# Estudiantes: Belén Cao
# Estudiantes: Enrique Capella
import pymysql
import pymongo
import json
from datetime import date
import configuracion


def conectar_mysql():
    """
    Establece una conexión con la base de datos MySQL utilizando los parámetros de configuración.
    Devuelve el objeto de conexión.
    """
    conexion = pymysql.connect(
        host=configuracion.MYSQL_HOST,
        port=configuracion.MYSQL_PORT,
        user=configuracion.MYSQL_USER,
        password=configuracion.MYSQL_PASS,
        charset='utf8mb4'
    )
    return conexion

def conectar_mongo():
    """
    Establece una conexión con la base de datos MongoDB y devuelve la colección especificada.
    """
    mongo_client = pymongo.MongoClient(configuracion.MONGO_HOST, configuracion.MONGO_PORT)
    db = mongo_client[configuracion.MONGO_DB]
    collection = db[configuracion.MONGO_COLLECTION]
    return mongo_client, db, collection


def crear_database_mysql():
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {configuracion.MYSQL_DB}")
    conexion.commit()
    return conexion, cursor


def crear_tablas_mysql(cursor):
    """
    Users: reviewerID, reviewerName
    Categories: category_id, category_name
    Products: product_id, category_id
    Reviews: review_id, reviewer_id, product_id, overall,
             review_date, unixReviewTime, helpful_yes, helpful_total
    """

    cursor.execute(f"USE {configuracion.MYSQL_DB}")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            reviewerID VARCHAR(50) PRIMARY KEY,
            reviewerName VARCHAR(255)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Categories (
            category_id INT AUTO_INCREMENT PRIMARY KEY,
            category_name VARCHAR(100) NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Products (
            product_id VARCHAR(50) PRIMARY KEY,
            category_id INT NOT NULL,
            FOREIGN KEY (category_id) REFERENCES Categories(category_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Reviews (
            review_id INT AUTO_INCREMENT PRIMARY KEY,
            reviewer_id VARCHAR(50) NOT NULL,
            product_id VARCHAR(50) NOT NULL,
            overall FLOAT NOT NULL,
            review_date DATE,
            unixReviewTime BIGINT,
            helpful_yes INT,
            helpful_total INT,
            FOREIGN KEY (reviewer_id) REFERENCES Users(reviewerID),
            FOREIGN KEY (product_id) REFERENCES Products(product_id)
        )
    """)


def crear_mongo_collection(database):
    """
    Devuelve la colección principal de MongoDB.
    Si no existe, MongoDB la creará automáticamente al insertar documentos.

    Además, se crea un índice único sobre review_id para evitar duplicados
    lógicos en MongoDB.
    """
    collection = database[configuracion.MONGO_COLLECTION]
    collection.create_index("review_id", unique=True)
    return collection


def parsear_review_time(review_time_str):

    try:
        partes = review_time_str.replace(",", "").split()
        if len(partes) != 3:
            return None
        mes, dia, ano = (int(parte) for parte in partes)
        return date(ano, mes, dia)
    
    except (AttributeError, TypeError, ValueError):
        return None
    

def get_insert_category(category_name, cursor):
    cursor.execute("SELECT category_id FROM Categories WHERE category_name = %s", (category_name,))
    fila = cursor.fetchone()
    if fila:
        return fila[0]
    cursor.execute("INSERT INTO Categories (category_name) VALUES (%s)", (category_name,))
    return cursor.lastrowid


def get_insert_product(product_id, category_id, cursor):
    cursor.execute("SELECT product_id FROM Products WHERE product_id = %s", (product_id,))
    fila = cursor.fetchone()
    if fila:
        return fila[0]
    cursor.execute("INSERT INTO Products (product_id, category_id) VALUES (%s, %s)", (product_id, category_id))
    return product_id

    
def get_insert_user(reviewer_id, reviewer_name, cursor):
    cursor.execute("SELECT reviewerID FROM Users WHERE reviewerID = %s", (reviewer_id,))
    fila = cursor.fetchone()
    if fila:
        return fila[0]
    cursor.execute("INSERT INTO Users (reviewerID, reviewerName) VALUES (%s, %s)", (reviewer_id, reviewer_name))
    return reviewer_id

def insert_review_mysql(reviewer_id, product_id, overall, review_date, unix_review_time, helpful_yes, helpful_total, cursor):
    cursor.execute("""
        INSERT INTO Reviews (
            reviewer_id, product_id, overall, review_date,
            unixReviewTime, helpful_yes, helpful_total
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (reviewer_id, product_id, overall, review_date, unix_review_time, helpful_yes, helpful_total))
    return cursor.lastrowid


def insert_review_mongo(review_id, review, mongo_collection):
    documento = {
        "review_id": review_id,
        "summary": review.get("summary", ""),
        "reviewText": review.get("reviewText", ""),
        "helpful": review.get("helpful", [])
    }
    mongo_collection.insert_one(documento)


def procesar_fichero(path, category_name, cursor, connection, collection):
    with open(path, "r", encoding="utf-8") as fichero:
        
        category_id = get_insert_category(category_name, cursor)

        for linea in fichero:
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

            get_insert_user(reviewer_id, reviewer_name, cursor)
            get_insert_product(product_id, category_id, cursor)

            review_id = insert_review_mysql(reviewer_id, product_id, overall, review_date, unix_review_time, helpful_yes, helpful_total, cursor)

            insert_review_mongo(review_id, review, collection)

    connection.commit()


def main():
    connection, cursor = crear_database_mysql()
    crear_tablas_mysql(cursor)
    connection.commit()

    mongo_client, mongo_db, mongo_collection = conectar_mongo()
    mongo_collection = crear_mongo_collection(mongo_db)

    files = [
        (configuracion.TOYS_FILE, "Toys and Games"),
        (configuracion.VIDEOGAMES_FILE, "Video Games"),
        (configuracion.MUSIC_FILE, "Digital Music"),
        (configuracion.INSTRUMENTS_FILE, "Musical Instruments")
    ]

    for ruta, categoria in files:
        procesar_fichero(ruta, categoria, cursor, connection, mongo_collection)
  
    cursor.close()
    connection.close()
    mongo_client.close()


if __name__ == "__main__":
    main()
