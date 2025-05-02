import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine.url import URL
from flask_login import LoginManager
from app.db_utils import wait_for_db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'

def create_app():
    app = Flask(__name__)

    # Build PostgreSQL URI if possible
    postgres_user = os.getenv('POSTGRES_USER')
    postgres_password = os.getenv('POSTGRES_PASSWORD')
    postgres_host = os.getenv('POSTGRES_HOST', 'postgres')
    postgres_db = os.getenv('POSTGRES_DB', 'photoalbum')

    if postgres_user and postgres_password:
        postgres_uri = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:5432/{postgres_db}"
    else:
        postgres_uri = None

    # Default to SQLite
    sqlite_uri = 'sqlite:////tmp/photos.db'

    # Try to connect to Postgres
    app.config['SQLALCHEMY_DATABASE_URI'] = postgres_uri or sqlite_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', os.path.join(app.root_path, 'static/uploads'))
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    @app.before_first_request
    def initialize_database():
        if wait_for_db(db):
            db.create_all()
            logger.info("Database tables created successfully")
        else:
            logger.error("Failed to connect to PostgreSQL, falling back to SQLite...")
            # Switch to SQLite
            app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_uri
            db.engine.dispose()  # Close previous engine
            db.init_app(app)
            with app.app_context():
                db.create_all()
            logger.info("SQLite database tables created successfully")

    return app
