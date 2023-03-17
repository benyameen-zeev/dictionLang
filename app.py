from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

if __name__ == '__main__':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///language_learning.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.run()

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

class TextResource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('text_resources', lazy=True))

    def __repr__(self):
        return f'<TextResource {self.title}>'

class Sentence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    text_resource_id = db.Column(db.Integer, db.ForeignKey('text_resource.id'), nullable=False)
    text_resource = db.relationship('TextResource', backref=db.backref('sentences', lazy=True))

    def __repr__(self):
        return f'<Sentence {self.id}>'

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255), nullable=False)
    translation = db.Column(db.String(255), nullable=False)
    sentence_id = db.Column(db.Integer, db.ForeignKey('sentence.id'), nullable=False)
    sentence = db.relationship('Sentence', backref=db.backref('words', lazy=True))

    def __repr__(self):
        return f'<Word {self.content}>'

class UserWord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'), nullable=False)
    proficiency_level = db.Column(db.Integer, nullable=False, default=0)

    user = db.relationship('User', backref=db.backref('user_words', lazy=True))
    word = db.relationship('Word', backref=db.backref('user_words', lazy=True))

    def __repr__(self):
        return f'<UserWord {self.id}>'

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text_resource_id = db.Column(db.Integer, db.ForeignKey('text_resource.id'))
