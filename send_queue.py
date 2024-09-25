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
    # Iniciar a sessão do SQLAlchemy

    try:
        # Recuperar todos os lembretes não concluídos
        reminders = session.query(Reminder).filter_by(done=False).all()

        now = datetime.now()
        print(f"Current time: {now}")

        # Verificar se o lembrete está dentro da janela de 10 minutos
        for reminder in reminders:
            # Calcula o próximo horário do lembrete
            next_reminder_time = reminder.startAt
            while next_reminder_time <= now:
                next_reminder_time += timedelta(hours=reminder.gap)

            # Calcular quanto tempo falta para o próximo lembrete
            time_until_reminder = (
                next_reminder_time - now
            ).total_seconds() / 60.0  # em minutos

            # Envia a notificação se faltar menos de 10 minutos
            if 0 <= time_until_reminder <= 10:
                print(f"Está na hora de: {reminder.message}, em {next_reminder_time}")

                # Envia a primeira notificação
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

                # Envia segunda notificação após 15 minutos
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

                if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                    print(
                        f"Notificação 'Já tomou seu remédio?' agendada com sucesso: {second_message}"
                    )

                    # Atualiza a frequência no banco de dados
                    if reminder.frequency >= 1:
                        reminder.frequency -= 1
                        session.commit()  # Faz o commit da mudança
                        print(
                            f"Frequency decrementado para {reminder.frequency} para o reminder_id {reminder.id}"
                        )
                    else:
                        # Quando frequency for 0, muda o status para done
                        reminder.done = True
                        session.commit()  # Faz o commit da mudança
                        print(f"Reminder {reminder.id} marcado como 'done'.")
                else:
                    print(f"Erro ao agendar a segunda notificação: {response}")
            else:
                # Caso ainda não esteja na hora
                print(
                    f"Ainda não está na hora de: {reminder.message}, faltam {time_until_reminder} minutos"
                )

    except Exception as e:
        print(f"Erro ao verificar lembretes: {str(e)}")

    finally:
        # Fechar a sessão do SQLAlchemy
        session.close()
