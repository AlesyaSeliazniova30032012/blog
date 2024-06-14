from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api, Resource
from flask_apispec.extension import FlaskApiSpec
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_marshmallow import Marshmallow
from datetime import datetime
from flask_apispec.views import MethodResource
from flask_restx import fields
from sqlalchemy import Table, Integer, String, Column, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship, declarative_base
import logging
from create_db import connection, engine

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s : %(message)s"
)
logger = logging.getLogger(__name__)

SWAGGER_URL = '/api'
# API_URL = '/static/swagger.json'

Base = declarative_base()

# Flask Config
class Config:
    APISPEC_SPEC = APISpec(
        title="My blog",
        version="v1.0",
        plugins=[MarshmallowPlugin()],
        openapi_version="2.0.0",
    )
    RESTX_VALIDATE = True
    APISPEC_SWAGGER_URL = SWAGGER_URL  # Corresponds to Documentation
    APISPEC_SWAGGER_UI_URL = "/Blog/"  # Corresponds to MainSwagger UI
    SQLALCHEMY_DATABASE_URI = connection

# Flask App
app = Flask(__name__)
app.config.from_object(Config)

blueprint = Blueprint('api', __name__, url_prefix='/api')
api = Api(blueprint, doc='/doc/')

app.register_blueprint(blueprint, url_prefix=SWAGGER_URL)

db = SQLAlchemy(app)
# docs = FlaskApiSpec(app)
ma = Marshmallow(app)


# Models
posts_categories = Table('posts_categories', Base.metadata,
    Column('post_id', Integer(), ForeignKey('posts.id'), primary_key=True),
    Column('category_id', Integer(), ForeignKey('categories.id'), primary_key=True)
)

posts_tags = Table('posts_tags', Base.metadata, 
    Column('post_id', Integer(), ForeignKey('posts.id'), primary_key=True),
    Column('tag_id', Integer(), ForeignKey('tags.id'), primary_key=True)
)

posts_authors = Table('posts_authors', Base.metadata,
    Column('post_id', Integer(), ForeignKey('posts.id'), primary_key=True),
    Column('author_id', Integer(), ForeignKey('authors.id'), primary_key=True)
)


class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)


class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)


class Author(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    email = Column(String(120), nullable=False, unique=True)


class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    published_at = Column(DateTime(), nullable=False, default=datetime.now)
    updated_on = Column(DateTime(), nullable=False, default=datetime.now, onupdate=datetime.now)
    categories = relationship('Category', secondary=posts_categories, backref=db.backref('posts', lazy='dynamic', uselist=True))
    authors = relationship('Author', secondary=posts_authors, backref=db.backref('posts', lazy='dynamic', uselist=True))
    tags = relationship('Tag', secondary=posts_tags, backref=db.backref('posts', lazy='dynamic', uselist=True))


Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

for t in Base.metadata.tables:
    logger.info(Base.metadata.tables[t])
logger.info('-------------')  
for t in Base.metadata.sorted_tables:
    logger.info(t.name)


api = Api(app, version='1.0', title='Blog API', description='A simple Blog API')
ns = api.namespace('api', description='Blog operations')

#Schemas
category_model = api.model('Category', {
    'id': fields.Integer(readonly=True, description='The category unique identifier'),
    'name': fields.String(required=True, description='The category name')
})

tag_model = api.model('Tag', {
    'id': fields.Integer(readonly=True, description='The tag unique identifier'),
    'name': fields.String(required=True, description='The tag name')
})

author_model = api.model('Author', {
    'id': fields.Integer(readonly=True, description='The author unique identifier'),
    'name': fields.String(required=True, description='The author name'),
    'email': fields.String(required=True, description='The author email address')
})

post_model = api.model('Post', {
    'id': fields.Integer(readonly=True, description='The post unique identifier'),
    'title': fields.String(required=True, description='The post title'),
    'content': fields.String(required=True, description='The post content'),
    'published_at': fields.DateTime(required=True, description='The post publication date'),
    'updated_on': fields.DateTime(required=True, description='The post updating date'),
    'categories': fields.List(fields.Nested(category_model)),
    'authors': fields.List(fields.Nested(author_model)),
    'tags': fields.List(fields.Nested(tag_model))
})


# Resources
@ns.route('/posts')
class PostsResource(MethodResource, Resource):
    @ns.doc('list_of_posts')
    @ns.marshal_list_with(post_model, code=200, description='List of posts')
    def get(self):
        """Get all posts"""
        posts = Post.query.all()
        return posts

    @ns.expect(post_model, validate=True, code=201, description='Create a new post')
    @ns.marshal_with(post_model, code=201, description='The new post')
    def post(self):
        """Create a new post"""
        data = api.payload
        post = Post(title=data['title'], 
                    content=data['content'], 
                    published_at=data['published_at'],
                    updated_on=data['updated_on'],
        )

        for category_id in data['categories']:
            category = Category.query.get(category_id)
            if category:
                post.categories.append(category)

        for tag_id in data['tags']:
            tag = Tag.query.get(tag_id)
            if tag:
                post.tags.append(tag)

        for author_id in data['authors']:
            author = Author.query.get(author_id)
            if author:
                post.authors.append(author)

        db.session.add(post)
        db.session.commit()
        return post, 201
    

@ns.route('/posts/<int:id>')
@ns.response(404, 'Post not found')
@ns.param('id', 'The post identifier')
class PostResource(MethodResource, Resource):
    @ns.doc('get_post')
    @ns.marshal_with(post_model, code=200, description='The post')
    def get(self, post_id):
        """Get a post by id"""
        post = Post.query.get_or_404(post_id)
        return post

    @ns.expect(post_model, validate=True, code=200, description='Update a post')
    @ns.marshal_with(post_model, code=200, description='The updated post')
    def put(self, post_id):
        """Update a post by id"""
        post = Post.query.get_or_404(id)
        data = api.payload
        post.title = data['title']
        post.content = data['content']
        post.published_at = data['published_at']
        post.updated_on=data['updated_on']

        post.categories = []
        for category_id in data['categories']:
            category = Category.query.get(category_id)
            if category:
                post.categories.append(category)

        post.tags = []
        for tag_id in data['tags']:
            tag = Tag.query.get(tag_id)
            if tag:
                post.tags.append(tag)

        post.authors = []
        for author_id in data['authors']:
            author = Author.query.get(author_id)
            if author:
                post.authors.append(author)
        db.session.commit()
        return post, 200
    

    @ns.response(204, 'Post deleted')
    @ns.marshal_with(post_model)
    def delete(self, post_id):
        """Delete a post by id"""
        post = Post.query.get_or_404(post_id)
        db.session.delete(post)
        db.session.commit()
        return '', 204


@ns.route('/categories')
@ns.response(404, 'Category not found')
@ns.param('id', 'The category identifier')
class CategoryResource(MethodResource, Resource):
    @ns.doc('list_of_categories')
    @ns.marshal_list_with(category_model, code=200, description='List of categories')
    def get(self):
        """Get all categories"""
        categories = Category.query.all()
        return categories
    
    @ns.expect(category_model, validate=True, code=201, description='Create a new category')
    @ns.marshal_with(category_model, code=201, description='The new category')
    def post(self):
        """Create a new category"""
        data = api.payload
        category = Category(name=data['name'])
        db.session.add(category)
        db.session.commit()
        return category, 201

    @ns.expect(category_model, validate=True, code=200, description='Update a category')
    @ns.marshal_with(category_model, code=200, description='The updated category')
    def put(self, category_id):
        """Update a category by id"""
        data = api.payload
        category = Category.query.get_or_404(category_id)
        category.name = data['name']
        db.session.commit()
        return category, 200

    @ns.response(204, 'Category deleted')
    @ns.marshal_with(category_model)
    def delete(self, category_id):
        """Delete a category"""
        category = Category.query.get_or_404(category_id)
        db.session.delete(category)
        db.session.commit()
        return '', 204
    

@ns.route('/tags')
@ns.response(404, 'Tag not found')
@ns.param('id', 'The tag identifier')
class TagResource(MethodResource, Resource):
    @ns.doc('list_of_tags')
    @ns.marshal_list_with(tag_model, code=200, description='List of tags')
    def get(self):
        """Get all tags"""
        tags = Tag.query.all()
        return tags
    
    @ns.expect(tag_model, validate=True, code=201, description='Create a new tag')
    @ns.marshal_with(tag_model, code=201, description='The new tag')
    def post(self):
        """Create a new tag"""
        data = api.payload
        tag = Tag(name=data['name'])
        db.session.add(tag)
        db.session.commit()
        return tag, 201

    @ns.expect(tag_model, validate=True, code=200, description='Update a tag')
    @ns.marshal_with(tag_model, code=200, description='The updated tag')
    def put(self, tag_id):
        """Update a tag by id"""
        data = api.payload
        tag = Tag.query.get_or_404(tag_id)
        tag.name = data['name']
        db.session.commit()
        return tag, 200

    @ns.response(204, 'Tag deleted')
    @ns.marshal_with(tag_model)
    def delete(self, tag_id):
        """Delete a tag"""
        tag = Tag.query.get_or_404(tag_id)
        db.session.delete(tag)
        db.session.commit()
        return '', 204


@ns.route('/authors')
@ns.response(404, 'Author not found')
@ns.param('id', 'The author identifier')
class AuthorResource(MethodResource, Resource):
    @ns.doc('list_of_authors')
    @ns.marshal_list_with(author_model, code=200, description='List of authors')
    def get(self):
        """Get all authors"""
        authors = Author.query.all()
        return authors

    @ns.expect(author_model, validate=True, code=201, description='Create a new author')
    @ns.marshal_with(author_model, code=201, description='The new author')
    def post(self):
        """Create a new author"""
        data = api.payload
        author = Author(name=data['name'], 
                        email=data['email']
        )
        db.session.add(author)
        db.session.commit()
        return author, 201

    @ns.expect(author_model, validate=True, code=200, description='Update an author')
    @ns.marshal_with(author_model, code=200, description='The updated author')
    def put(self, author_id):
        """Update an author by id"""
        data = api.payload
        author = Author.query.get_or_404(author_id)
        author.name = data['name']
        author.email = data['email']
        db.session.commit()
        return author, 200

    @ns.response(204, 'Author deleted')
    @ns.marshal_with(author_model)
    def delete(self, author_id):
        """Delete an author by id"""
        author = Author.query.get_or_404(author_id)
        db.session.delete(author)
        db.session.commit()
        return '', 204
    

if __name__ == '__main__':
    app.run(debug=True)

