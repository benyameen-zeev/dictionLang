from app import db
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    text_resources = db.relationship('TextResource', back_populates='user', lazy='dynamic')
    proficiencies = db.relationship('Proficiency', back_populates='user', lazy='dynamic')
    word_banks = db.relationship('WordBank', back_populates='user')
    

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

class TextResource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='text_resources')
    language = db.Column(db.String(50), nullable=True)
    private = db.Column(db.Boolean, nullable=False, default=False)
    rating = db.Column(db.Integer, nullable=False, default=0)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    votes = db.relationship('Vote', backref='text_resource', lazy='dynamic')
    words = db.relationship('Word', back_populates='text_resource', lazy='dynamic')
    sentences = db.relationship('Sentence', back_populates='text_resource', lazy='dynamic')
    word_banks = db.relationship('WordBank', back_populates='collection')

    @property
    def formatted_timestamp(self):
        if not self.timestamp:
            current_app.logger.warning(f"Timestamp missing for TextResource with id {self.id}")
            return "N/A"
        return self.timestamp.strftime('%Y-%m-%d')

    def __repr__(self):
        return f'<TextResource {self.title}>'


class Sentence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sentence = db.Column(db.Text, nullable=False)
    translation = db.Column(db.Text, nullable=True)
    text_resource_id = db.Column(db.Integer, db.ForeignKey('text_resource.id'), nullable=False)
    text_resource = db.relationship('TextResource', back_populates='sentences')

    def __repr__(self):
        return f'<Sentence {self.id}>'

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(255), nullable=False)
    translation = db.Column(db.String(255), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    frequency = db.Column(db.Integer, nullable=False, default=0)
    definition = db.Column(db.String(255), nullable=True)
    text_resource_id = db.Column(db.Integer, db.ForeignKey('text_resource.id'), nullable=False)
    text_resource = db.relationship('TextResource', back_populates='words')

    def __repr__(self):
        return f'<Word {self.word}>'


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

    def __repr__(self):
        return f'<Quiz {self.id}>'

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text_resource_id = db.Column(db.Integer, db.ForeignKey('text_resource.id'), nullable=False)
    vote_value = db.Column(db.Integer, nullable=False)

    user = db.relationship('User', backref=db.backref('votes', lazy=True))

    def __repr__(self):
        return f'<Vote {self.id}>'



class Proficiency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'), nullable=False)
    strength = db.Column(db.Float, nullable=False, default=0)

    user = db.relationship('User', back_populates='proficiencies')
    word = db.relationship('Word', backref=db.backref('proficiencies', lazy=True))

    def __repr__(self):
        return f'<Proficiency {self.id}>'
    
class TranslationVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sentence_id = db.Column(db.Integer, db.ForeignKey('sentence.id'), nullable=False)
    vote_value = db.Column(db.Integer, nullable=False)

    user = db.relationship('User', backref=db.backref('translation_votes', lazy=True))
    sentence = db.relationship('Sentence', backref=db.backref('translation_votes', lazy=True))

    def __repr__(self):
        return f'<TranslationVote {self.id}>'
    
class WordBank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    translation = db.Column(db.String(100), nullable=True)
    strength = db.Column(db.Float, default=0)
    collection_id = db.Column(db.Integer, db.ForeignKey('text_resource.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='word_banks')
    collection = db.relationship('TextResource', back_populates='word_banks')