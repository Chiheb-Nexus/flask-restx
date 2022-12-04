"""Test Auto generate SQLAlchemy API model"""
import pytest
from flask_sqlalchemy import SQLAlchemy
from flask_restx import marshal, marshal_with, Api, Resource
from flask_restx.tools import gen_api_model_from_db


class FixtureTestCase(object):

    @pytest.fixture
    def db(self, app):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        db = SQLAlchemy(app)
        yield db

    @pytest.fixture
    def api(self, app):
        yield Api(app)
    
    @pytest.fixture
    def ns(self, api):
        yield api.namespace('todos', description='TODO operations')
    
    @pytest.fixture
    def user_model(self, db):
        class User(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String(80), unique=True, nullable=False)
            email = db.Column(db.String(120), unique=True, nullable=False)

            def __repr__(self):
               return '<User %r>' % self.username
            
            class Meta:
                fields = '__all__'

        return User

    @pytest.fixture
    def simple_payload(self):
        return {'id': 1, 'username': 'toto', 'email': 'toto@tata.tt'}


class AutoGenAPIModelTest(FixtureTestCase):

    def test_user_model(self, user_model, api, simple_payload):
        
        schema = gen_api_model_from_db(api, user_model)
        marshaled = marshal(simple_payload, schema)
        assert marshaled == simple_payload
    
    def test_model_as_flat_dict_with_marchal_decorator_list(self, api, client, user_model):
        fields = api.model(
            'Person',
            gen_api_model_from_db(api, user_model)
        )

        @api.route("/model-as-dict/")
        class ModelAsDict(Resource):
            @api.marshal_list_with(fields)
            def get(self):
                return {}

        data = client.get_specs()

        assert "definitions" in data
        assert "Person" in data["definitions"]
        assert data["definitions"]["Person"] == {
            "properties": {
                "id": {"type": "integer"},
                "username": {"type": "string"},
                "email": {"type": "string"},
            },
            "type": "object",
        }

        path = data["paths"]["/model-as-dict/"]
        assert path["get"]["responses"]["200"]["schema"] == {
            "type": 'array',
            "items": {"$ref": "#/definitions/Person"}
        }
    
    def test_model_as_flat_dict_with_marchal_decorator_list_kwargs(self, api, client, user_model):
        fields = api.model(
            'Person',
            gen_api_model_from_db(api, user_model)
        )

        @api.route("/model-as-dict/")
        class ModelAsDict(Resource):
            @api.marshal_list_with(fields, code=201, description="Some details")
            def get(self):
                return {}

        data = client.get_specs()

        assert "definitions" in data
        assert "Person" in data["definitions"]

        path = data["paths"]["/model-as-dict/"]
        assert path["get"]["responses"] == {
            "201": {
                "description": "Some details",
                "schema": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/Person"},
                },
            }
        }

    def test_model_as_dict_with_list(self, api, client, db):
        from sqlalchemy import String, ARRAY
        class User(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String(80), unique=True, nullable=False)
            tags = db.Column(ARRAY(String))

            def __repr__(self):
               return '<User %r>' % self.username
            
            class Meta:
                fields = '__all__'
        fields = api.model(
            "Person",
            gen_api_model_from_db(api, User)
        )

        @api.route("/model-with-list/")
        class ModelAsDict(Resource):
            @api.doc(model=fields)
            def get(self):
                return {}

        data = client.get_specs()

        assert "definitions" in data
        assert "Person" in data["definitions"]
        assert data["definitions"]["Person"] == {
            "properties": {
                "id": {"type": "integer"},
                "username": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "type": "object",
        }

        path = data["paths"]["/model-with-list/"]
        assert path["get"]["responses"]["200"]["schema"] == {
            "$ref": "#/definitions/Person"
        }