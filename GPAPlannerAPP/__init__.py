from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sendgrid import SendGridAPIClient


import os
from os import path, makedirs

db = SQLAlchemy()





GPA_DB = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-default-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = F'sqlite:///{GPA_DB}'

    db.init_app(app)
    
    

    @app.context_processor
    def inject_user():
        return dict(user=current_user)
    
    

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')


    from .models import User, gpa



    create_database(app)

    login_manager =LoginManager()
    login_manager.login_view = 'auth.login' #type: ignore
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

def create_database(app):
    db_path = 'GPAPlanner/' + GPA_DB
    if not path.exists(db_path):
        if not path.exists('GPAPlanner'):
            os.makedirs('GPAPlanner')
    with app.app_context():
        if not path.exists('GPAPlanner/' + GPA_DB):
            db.create_all()
            print('Created database!!')

