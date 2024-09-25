from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Index
from sqlalchemy.orm import declarative_base

# Configurando SQLAlchemy
Base = declarative_base()


# Definindo o modelo Reminder
class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True)
    userId = Column(Integer, nullable=False)
    message = Column(String(255), nullable=False)
    startAt = Column(DateTime, default=datetime.now)
    gap = Column(Float, nullable=False)
    frequency = Column(Integer, nullable=False)
    duration = Column(DateTime, nullable=False)
    done = Column(Boolean, default=False)

    # Adicionando índice ao campo 'startAt'
    __table_args__ = (Index("idx_startAt", "startAt"),)  # Definição do índice


# Definindo o modelo User
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), nullable=False)
