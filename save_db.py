import os
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.db import User, Reminder
from datetime import datetime, timedelta


# Carregar variáveis do .env
load_dotenv()

db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
port = int(os.getenv("DB_PORT"))
DESTINATION_QUEUE_URL = os.getenv("DESTINATION_QUEUE_URL")

engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")
Session = sessionmaker(bind=engine)
session = Session()


# Função para salvar lembretes no banco de dados
def lambda_save_db(event):
    # Parâmetros recebidos no evento
    data = json.loads(event["body"])

    # Iniciar a sessão do SQLAlchemy
    session = Session()

    try:
        # Recupera os parâmetros da requisição
        phone_number = data["phone_number"]
        message = data["message"]
        gap = data.get("gap")  # Em quantas horas o lembrete deve ser enviado
        frequency = data.get("frequency", 1)  # Número de lembretes

        # Verifica se 'duration' foi passado, caso contrário calcula
        if "duration" in data:
            duration = datetime.strptime(data["duration"], "%Y-%m-%d %H:%M:%S")
        else:
            # Calcular 'duration' caso não seja fornecido
            duration = datetime.now() + timedelta(hours=frequency * gap)

        # Consulta o usuário pelo número de telefone
        user = session.query(User).filter_by(phone_number=phone_number).first()

        if not user:
            return {
                "statusCode": 404,
                "body": json.dumps("Usuário não encontrado."),
            }

        # Cria um novo lembrete
        reminder = Reminder(
            userId=user.id,
            message=message,
            gap=gap,
            frequency=frequency,
            startAt=datetime.now(),  # Supondo que o startAt é agora
            duration=duration,
            done=False,  # Por padrão, o lembrete ainda não foi concluído
        )

        # Adiciona e salva o lembrete no banco de dados
        session.add(reminder)
        session.commit()

        return {"statusCode": 200, "body": json.dumps("Dados inseridos com sucesso!")}

    except Exception as e:
        session.rollback()
        return {
            "statusCode": 500,
            "body": json.dumps(f"Erro ao inserir dados: {str(e)}"),
        }

    finally:
        # Fechar a sessão do SQLAlchemy
        session.close()
