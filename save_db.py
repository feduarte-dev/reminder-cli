import os
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.db import User, Reminder


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

    try:
        phone_number = data["phone_number"]
        message = data["message"]
        gap = data.get("gap")
        frequency = data.get("frequency", 1)

        # Consulta para obter o userId baseado no número de telefone
        user = session.query(User).filter_by(phone_number=phone_number).first()

        if user:
            # Criar um novo lembrete
            new_reminder = Reminder(
                userId=user.id,
                message=message,
                gap=gap,
                frequency=frequency,
            )

            session.add(new_reminder)
            session.commit()

        else:
            return {"statusCode": 404, "body": json.dumps("Usuário não encontrado.")}

    except Exception as e:
        session.rollback()
        return {
            "statusCode": 500,
            "body": json.dumps(f"Erro ao inserir dados: {str(e)}"),
        }

    return {"statusCode": 200, "body": json.dumps("Dados inseridos com sucesso!")}
