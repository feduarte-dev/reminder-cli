import os
import json
import boto3
from dotenv import load_dotenv
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.db import Reminder

# Carregar variáveis do .env
load_dotenv()

db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
port = int(os.getenv("DB_PORT"))
DESTINATION_QUEUE_URL = os.getenv("DESTINATION_QUEUE_URL")

# Inicializando o cliente SQS
sqs_client = boto3.client("sqs")

engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")
Session = sessionmaker(bind=engine)
session = Session()


# Função para verificar lembretes e enviar notificações
def lambda_send_queue():
    try:
        reminders = session.query(Reminder).filter_by(done=False).all()
        now = datetime.now()

        for reminder in reminders:
            next_reminder_time = reminder.startAt
            while next_reminder_time <= now:
                next_reminder_time += timedelta(hours=reminder.gap)

            if now <= next_reminder_time <= now + timedelta(minutes=10):
                print(f"Está na hora de: {reminder.message}")

                # Enviar a primeira notificação
                first_message = {
                    "userId": reminder.userId,
                    "message": reminder.message,
                    "reminder_time": str(next_reminder_time),
                }

                response = sqs_client.send_message(
                    QueueUrl=DESTINATION_QUEUE_URL,
                    MessageBody=json.dumps(first_message),
                )

                if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                    print(
                        f"Primeira notificação enviada para a fila SQS: {first_message}"
                    )
                else:
                    print(
                        f"Erro ao enviar a primeira notificação para a fila SQS: {response}"
                    )

                # Enviar segunda notificação após 15 minutos
                second_message = {
                    "userId": reminder.userId,
                    "message": "Já tomou seu remédio?",
                    "reminder_time": str(next_reminder_time + timedelta(minutes=15)),
                }

                response = sqs_client.send_message(
                    QueueUrl=DESTINATION_QUEUE_URL,
                    MessageBody=json.dumps(second_message),
                    DelaySeconds=900,  # 15 minutos de delay (900 segundos)
                )

                # Se deu tudo certo, atualiza o banco de dados
                if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                    print(
                        f"Notificação 'Já tomou seu remédio?' agendada com sucesso: {second_message}"
                    )

                    # Diminui o valor de frequency para os próximos cálculos quando a função rodar novamente
                    if reminder.frequency > 1:
                        reminder.frequency -= 1
                    else:
                        reminder.done = True

                    session.commit()
                else:
                    print(f"Erro ao agendar a segunda notificação: {response}")

            else:
                print(f"Ainda não está na hora de: {reminder.message}")

    except Exception as e:
        session.rollback()
        print(f"Erro ao verificar lembretes: {str(e)}")

    # Fechar a sessão ao final
    finally:
        session.close()
