from flask import Flask
from pymongo import MongoClient
from typing import Optional

# The application factory. Avoid importing app.routes.main at the top-level
# to prevent circular imports when routes import the app or db.
def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # attach db to app object instead of a module-level global to avoid
    # circular import issues when routes import `app`.
    app.db = None

    try:
        client = MongoClient(app.config['MONGO_URI'])
        app.db = client.get_default_database()
    except Exception as error:
        print(f"Erro ao conectar com o Mongo: {error}")

    # Import and register blueprints here (after app and app.db exist)
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)

    return app