# Import statements
from flask_sqlalchemy import *

# Creation of database linker with SQLAlchemy
db = SQLAlchemy()

# Creation of the table
# This includes the detail related to the column names, and the datatype of the columns which will be created.
class requestdetails(db.Model):
    # Table name
    __tablename__ = "requestdetails"
    # Column Names :
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    problem = db.Column(db.String, nullable=False)
    language = db.Column(db.String, nullable=False)
    updatedate = db.Column(db.String, nullable=False)
    deadline = db.Column(db.String, nullable=False)
    secretkey = db.Column(db.String, nullable=False)
    solution = db.Column(db.String, nullable=False)

class users(db.Model):
    # Table name
    __tablename__ = 'users'
    # Column name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)

class message(db.Model):
    # Table name
    __tablename__ = "message"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email =  db.Column(db.String, nullable=False)
    message = db.Column(db.String, nullable=False)

class images(db.Model):
    # Table Name
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    img= db.Column(db.LargeBinary, nullable=False)
    filename = db.Column(db.String, nullable=False)

