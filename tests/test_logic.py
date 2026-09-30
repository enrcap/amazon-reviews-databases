"""Unit tests using synthetic inputs; no external databases are contacted."""
import sys
import sqlite3
import unittest
from pathlib import Path
from datetime import date
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import configuracion
import load_data
import inserta_dataset
import neo4JProyecto as graph
import recomendador


class SQLiteCursorAdapter:
    """Translate only parameter placeholders for isolated recommendation query tests."""
    def __init__(self, connection):
        self.cursor = connection.cursor()
    def execute(self, sql, parameters=()):
        return self.cursor.execute(sql.replace('%s', '?'), parameters)
    def fetchall(self):
        return self.cursor.fetchall()
    def fetchone(self):
        return self.cursor.fetchone()


class LogicTests(unittest.TestCase):
    def test_valid_dates(self):
        for module in [load_data, inserta_dataset]:
            self.assertEqual(module.parsear_review_time('02 29, 2024'), date(2024, 2, 29))

    def test_invalid_dates(self):
        for module in [load_data, inserta_dataset]:
            for value in ['02 29, 2023', '', '13 1, 2024', 'invalid', None]:
                self.assertIsNone(module.parsear_review_time(value))

    def test_pearson_positive_and_negative(self):
        a = {'p1': 1, 'p2': 3, 'p3': 5, 'only_a': 4}
        self.assertAlmostEqual(graph.pearson_correlation(a, {'p1': 2, 'p2': 3, 'p3': 4}), 1)
        self.assertAlmostEqual(graph.pearson_correlation(a, {'p1': 5, 'p2': 3, 'p3': 1}), -1)

    def test_pearson_undefined(self):
        self.assertIsNone(graph.pearson_correlation({'a': 1}, {'b': 2}))
        self.assertIsNone(graph.pearson_correlation({'a': 1}, {'a': 2}))
        self.assertIsNone(graph.pearson_correlation({'a': 2, 'b': 2}, {'a': 3, 'b': 5}))

    def test_common_products_are_distinct(self):
        rows = [{'reviewer_id': u, 'product_id': p} for u,p in
                [('a','x'),('a','x'),('a','y'),('b','x'),('b','y'),('c','z')]]
        self.assertEqual(graph.calcular_articulos_en_comun(rows), {('a', 'b'): 2})

    def test_graph_reset_is_scoped(self):
        for reset in [graph.clear_neo4j_graph, graph.clear_grafo]:
            driver = MagicMock()
            reset(driver)
            driver.session.assert_called_once_with(database=configuracion.NEO4J_DATABASE)
            session = driver.session.return_value.__enter__.return_value
            session.run.assert_called_once_with('MATCH (n:AmazonReviewsProject) DETACH DELETE n')

    def test_config_paths_are_absolute(self):
        self.assertTrue(configuracion.TOYS_FILE.is_absolute())
        self.assertEqual(configuracion.TOYS_FILE.name, 'Toys_and_Games_5.json')

    def test_recommendations_exclude_seen_products_and_other_categories(self):
        with sqlite3.connect(':memory:') as db:
            db.executescript('''
                CREATE TABLE Users (reviewerID TEXT PRIMARY KEY);
                CREATE TABLE Categories (category_id INTEGER PRIMARY KEY, category_name TEXT);
                CREATE TABLE Products (product_id TEXT PRIMARY KEY, category_id INTEGER);
                CREATE TABLE Reviews (review_id INTEGER PRIMARY KEY, reviewer_id TEXT, product_id TEXT);
                INSERT INTO Users VALUES ('demo-user');
                INSERT INTO Categories VALUES (1, 'Games'), (2, 'Music');
                INSERT INTO Products VALUES ('seen',1), ('first',1), ('second',1), ('music',2);
                INSERT INTO Reviews VALUES (1,'demo-user','seen'), (2,'other','seen'),
                    (3,'other','first'), (4,'another','first'), (5,'other','second'), (6,'other','music');
            ''')
            cursor = SQLiteCursorAdapter(db)
            self.assertTrue(recomendador.usuario_existe('demo-user', cursor))
            self.assertFalse(recomendador.usuario_existe("' OR 1=1 --", cursor))
            self.assertEqual(recomendador.obtener_recomendaciones('demo-user', 'Games', cursor), [('first', 2), ('second', 1)])
            self.assertEqual(recomendador.obtener_recomendaciones('demo-user', 'unknown', cursor), [])

if __name__ == '__main__':
    unittest.main()
