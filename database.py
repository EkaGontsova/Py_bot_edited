import os
from contextlib import contextmanager
import sqlalchemy as sq
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()
DSN = os.getenv('DATABASE_URL')
engine = create_engine(DSN)
Session = sessionmaker(bind=engine)


@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        print(f"Ошибка: {e}")
        session.rollback()
        raise
    finally:
        session.close()


class User(Base):
    __tablename__ = 'users'
    id = sq.Column(sq.Integer, primary_key=True)
    telegram_id = sq.Column(sq.Integer, unique=True)
    user_words = sq.orm.relationship('UserWord', back_populates='user')


class Word(Base):
    __tablename__ = 'words'
    id = sq.Column(sq.Integer, primary_key=True)
    word = sq.Column(sq.String, unique=True)
    translate = sq.Column(sq.String)


class UserWord(Base):
    __tablename__ = 'user_words'
    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('users.id'))
    word = sq.Column(sq.String)
    translate = sq.Column(sq.String)
    user = sq.orm.relationship('User', back_populates='user_words')


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def get_user_by_telegram_id(telegram_id, session):
    user = session.query(User).filter_by(telegram_id=int(telegram_id)).first()
    if not user:
        user = User(telegram_id=int(telegram_id))
        session.add(user)
        session.commit()
    return user


def link_user_with_base_words(session, user_id):
    base_words = session.query(Word).all()
    for word in base_words:
        if not session.query(UserWord).filter_by(user_id=user_id, word=word.word).first():
            session.add(UserWord(user_id=user_id, word=word.word, translate=word.translate))
    session.commit()


def create_session():
    Session = sessionmaker(bind=engine)
    return Session()


def add_word(session, word, translate):
    new_word = session.query(Word).filter_by(word=word).first()
    if not new_word:
        new_word = Word(word=word, translate=translate)
        session.add(new_word)
        session.commit()


def copy_words_to_user_words(session, user_id):
    base_words = session.query(Word).all()
    for word in base_words:
        session.add(UserWord(user_id=user_id, word=word.word, translate=word.translate))
    session.commit()


def add_word_for_user(session, telegram_id, word, translate):
    user = get_user_by_telegram_id(telegram_id, session)
    if not session.query(UserWord).filter_by(user_id=user.id, word=word).first():
        session.add(UserWord(user_id=user.id, word=word, translate=translate))
        session.commit()
        return True
    else:
        return False


def delete_word_for_user(session, telegram_id, word):
    user = get_user_by_telegram_id(telegram_id, session)
    user_word_to_delete = session.query(UserWord).filter(
        UserWord.user_id == user.id,
        UserWord.word == word
    ).first()
    if user_word_to_delete:
        session.delete(user_word_to_delete)
        session.commit()
        return True
    return False


def get_random_pair(user_telegram_id):
    with session_scope() as session:
        user = get_user_by_telegram_id(user_telegram_id, session)
        if not user:
            print(f"Пользователь с telegram_id {user_telegram_id} не найден.")
            return None
        pair = session.query(UserWord).filter(UserWord.user_id == user.id).order_by(func.random()).first()
        if not pair:
            print(f"Слова для пользователя с id {user.id} не найдены.")
            return None
        return pair.word, pair.translate


if __name__ == "__main__":
    create_tables(engine)
    with session_scope() as session:
        add_word(session, "Лес", "Forest")
        add_word(session, "Утро", "Morning")
        add_word(session, "Вечер", "Evening")
        add_word(session, "Небо", "Sky")
        add_word(session, "Солнце", "Sun")
        add_word(session, "Ночь", "Night")
        add_word(session, "Река", "River")
        add_word(session, "Гора", "Mountain")
        add_word(session, "Луна", "Moon")
        add_word(session, "Море", "Sea")
