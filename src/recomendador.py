# Estudiantes: Belén Cao
# Estudiantes: Enrique Capella
import pymysql
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


def obtener_categorias(cursor):
    """
    Obtiene todas las categorías disponibles.
    """
    cursor.execute(
        """
        SELECT category_name
        FROM Categories
        ORDER BY category_name
        """
    )

    return [fila[0] for fila in cursor.fetchall()]


def usuario_existe(reviewer_id, cursor):
    """
    Comprueba si el usuario existe en la base de datos.
    """
    cursor.execute(
        """
        SELECT reviewerID
        FROM Users
        WHERE reviewerID = %s
        """,
        (reviewer_id,)
    )

    resultado = cursor.fetchone()
    return resultado is not None


def obtener_recomendaciones(reviewer_id, categoria, cursor):
    """
    Obtiene los 10 artículos más populares de una categoría que el usuario aún no ha consumido.
    """
    cursor.execute(
        """
        SELECT
            p.product_id,
            COUNT(r.review_id) AS total_reviews
        FROM Products p
        JOIN Categories c
            ON p.category_id = c.category_id
        JOIN Reviews r
            ON p.product_id = r.product_id
        WHERE c.category_name = %s
          AND p.product_id NOT IN (
                SELECT product_id
                FROM Reviews
                WHERE reviewer_id = %s
          )
        GROUP BY p.product_id
        ORDER BY total_reviews DESC, p.product_id ASC
        LIMIT 10
        """,
        (categoria, reviewer_id)
    )

    return cursor.fetchall()


def main():

    conexion = conectar_mysql()
    cursor = conexion.cursor()

    print("RECOMENDADOR")
    print()

    reviewer_id = input("Introduce el reviewerID: ").strip()

    if not usuario_existe(reviewer_id, cursor):
        print()
        print("El usuario no existe en la base de datos.")
        cursor.close()
        conexion.close()
        return

    print("\nCategorías disponibles:")
    categorias = obtener_categorias(cursor)
    for categoria in categorias:
        print("\t·", categoria)

    print("")
    categoria = input("Introduce la categoría: ").strip()

    if categoria not in categorias:
        print("\nLa categoría no existe.")
        cursor.close()
        conexion.close()
        return

    recomendaciones = obtener_recomendaciones(
        reviewer_id,
        categoria,
        cursor
    )

    print("\nTop 10 artículos recomendados:")

    if not recomendaciones:
        print("No hay recomendaciones disponibles.")
    else:
        for i, recomendacion in enumerate(recomendaciones, start=1):
            print(str(i) + ". " + str(recomendacion[0]) + " (" + str(recomendacion[1]) + " reviews)")

    cursor.close()
    conexion.close()


if __name__ == "__main__":
    main()
