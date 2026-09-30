"""Configuración local mediante variables de entorno y un archivo .env no publicado.

Proyecto académico original: Enrique Capella y Belén Cao.
Preparación del repositorio: Enrique Capella Magallón.
"""
import os
import re
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / '.env', override=False)

def ruta_datos(variable, filename):
    """Resuelve rutas relativas desde la raíz, independientemente del directorio actual."""
    path = Path(os.getenv(variable, f'data/{filename}')).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path

MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
MYSQL_USER = os.getenv('MYSQL_USER', 'amazon_app')
MYSQL_PASS = os.getenv('MYSQL_PASS', '')
MYSQL_DB = os.getenv('MYSQL_DB', 'amazon_reviews')
# Este identificador se interpola en CREATE DATABASE y USE.
if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,63}', MYSQL_DB):
    raise ValueError('MYSQL_DB debe ser un identificador SQL simple de hasta 64 caracteres.')

MONGO_HOST = os.getenv('MONGO_HOST', '127.0.0.1')
MONGO_PORT = int(os.getenv('MONGO_PORT', '27017'))
MONGO_DB = os.getenv('MONGO_DB', 'amazon_reviews_mongo')
MONGO_COLLECTION = os.getenv('MONGO_COLLECTION', 'reviews_texto')

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://127.0.0.1:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASS = os.getenv('NEO4J_PASS', '')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE', 'neo4j')

TOYS_FILE = ruta_datos('TOYS_FILE', 'Toys_and_Games_5.json')
VIDEOGAMES_FILE = ruta_datos('VIDEOGAMES_FILE', 'Video_Games_5.json')
MUSIC_FILE = ruta_datos('MUSIC_FILE', 'Digital_Music_5.json')
INSTRUMENTS_FILE = ruta_datos('INSTRUMENTS_FILE', 'Musical_Instruments_5.json')
SPORTS_FILE = ruta_datos('SPORTS_FILE', 'Sports_and_Outdoors_5.json')

TOP_USUARIOS = int(os.getenv('TOP_USUARIOS', '30'))
FICHERO_SIMILITUDES = PROJECT_ROOT / 'similitudes_usuarios.csv'
