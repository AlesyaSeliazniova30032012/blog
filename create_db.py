import configparser
from sqlalchemy import create_engine, inspect
from sqlalchemy.sql import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys      

# print(sys.getdefaultencoding())

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
# sections = config.sections()
# print(sections)
database_user = config['database']['user']
database_password = config['database']['password']
connection = f"postgresql+psycopg2://{database_user}:{database_password}@localhost:5432/postgres?client_encoding=utf8"
engine = create_engine(connection, echo=True, pool_size=10, max_overflow=10)
# session = Session(bind=engine)
session = sessionmaker(bind=engine)
session = Session()
try:
    engine.connect()
    print(engine)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    print(f"table_names: {table_names}")   #['posts', 'posts_categories', 'categories', 'posts_tags', 'tags', 'posts_authors', 'authors']
    # columns = inspector.get_columns('posts')
    # print(columns) #[{'name': 'id', 'type': INTEGER(), 'nullable': False, 'default': "nextval('posts_id_seq'::regclass)", 'autoincrement': True, 'comment': None}, {'name': 'title', 'type': VARCHAR(length=100), 'nullable': False, 'default': None, 'autoincrement': False, 'comment': None}, {'name': 'content', 'type': TEXT(), 'nullable': False, 'default': None, 'autoincrement': False, 'comment': None}, {'name': 'published_at', 'type': TIMESTAMP(), 'nullable': False, 'default': None, 'autoincrement': False, 'comment': None}, {'name': 'updated_on', 'type': TIMESTAMP(), 'nullable': False, 'default': None, 'autoincrement': False, 'comment': None}]
    columns = inspector.get_columns('posts_categories')
    # print(columns)  #[{'name': 'post_id', 'type': INTEGER(), 'nullable': False, 'default': None, 'autoincrement': False, 'comment': None}, {'name': 'category_id', 'type': INTEGER(), 'nullable': False, 'default': None, 'autoincrement': False, 'comment': None}]

except UnicodeDecodeError as e:
    print(e)

# connection = psycopg2.connect(user=user, password=password)
# connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
# cursor = connection.cursor()
# sql_create_database = cursor.execute('create database postgres')
# cursor.close()
# connection.close()

