import email
from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash


class gpa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    current_gpa = db.Column(db.Float)
    goal_gpa = db.Column(db.Float)
    completed_credits = db.Column(db.Integer)
    remaining_credits = db.Column(db.Integer)
    required_gpa = db.Column(db.Float)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(255))
    first_name =db.Column(db.String(150))
    last_name =db.Column(db.String(150))
    security_question = db.Column(db.String(255))
    security_answer = db.Column(db.String(255))
    gpa = db.relationship('gpa', backref='user', uselist=False)
    notes = db.relationship('Note', backref='user')



    def __init__(self,email, first_name, last_name, password, security_question, security_answer):
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.password =  password
        self.security_question = security_question
        self.security_answer = generate_password_hash(security_answer)



class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(10000))
    datetime = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


    def __init__(self,content, user_id):
        self.content = content
        self.user_id =user_id
       

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, date, user_id):
        self.title = title
        self.date = date
        self.user_id = user_id





   