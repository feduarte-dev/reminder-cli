import os
import json
import pymysql
import boto3
import click
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Inicializando o cliente SQS
sqs_client = boto3.client("sqs")

# Inicializando o cliente Lambda
lambda_client = boto3.client("lambda")

# Definir a URL da fila SQS
DESTINATION_QUEUE_URL = os.getenv("DESTINATION_QUEUE_URL")


# Carregar variáveis do .env
load_dotenv()

db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
port = int(os.getenv("DB_PORT"))


def lambda_save_db(event):
    # Parâmetros recebidos no evento
    data = json.loads(event["body"])

    # Conectando ao banco de dados MySQL
    connection = pymysql.connect(
        host=db_host, user=db_user, password=db_password, database=db_name
    )

    try:
        with connection.cursor() as cursor:
            phone_number = data["phone_number"]
            message = data["message"]
            gap = data.get("gap")  # In how many hours you want to be reminded
            frequency = data.get("frequency", 1)  # Number of reminders

            # Verifica se 'duration' foi passado, caso contrário calcula
            if "duration" in data:
                duration = datetime.strptime(data["duration"], "%Y-%m-%d %H:%M:%S")
            else:
                # Calcular 'duration' caso não seja fornecido
                duration = datetime.now() + timedelta(hours=frequency * gap)

            # Criação da query SQL
            sql = """
            INSERT INTO reminders (userId, message, frequency, gap, duration)
            VALUES ((SELECT id FROM users WHERE phone_number = %s), %s, %s, %s, %s)
            """

            # Executa a query
            cursor.execute(sql, (phone_number, message, frequency, gap, duration))

            # Commit para salvar as mudanças no banco
            connection.commit()

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f"Erro ao inserir dados: {str(e)}"),
        }

    finally:
        # Fecha a conexão com o banco
        connection.close()

    return {"statusCode": 200, "body": json.dumps("Dados inseridos com sucesso!")}


def lambda_send_queue():
    # Conectar ao banco de dados MySQL
    connection = pymysql.connect(
        host=db_host, user=db_user, password=db_password, database=db_name
    )

    try:
        with connection.cursor() as cursor:
            # Recuperar todos os lembretes não concluídos
            sql = """
            SELECT id, message, startAt, gap, frequency, userId
            FROM reminders
            WHERE done = FALSE
            """
            cursor.execute(sql)
            reminders = cursor.fetchall()

            now = datetime.now()

            # Verificar se o lembrete está dentro da janela de 10 minutos
            for reminder in reminders:
                reminder_id, message, startAt, gap, frequency, userId = reminder

                # Calcula o próximo horário do lembrete, atualizando o next reminder após envio da notificação
                next_reminder_time = startAt
                while next_reminder_time <= now:
                    next_reminder_time += timedelta(hours=gap)

                # Caso esteja na hora de enviar a notificação
                if now <= next_reminder_time <= now + timedelta(minutes=10):
                    print(f"now: {now}, next_reminder_time: {next_reminder_time}")

                    print(f"Está na hora de: {message}")

                    # Envia a primeira notificação
                    first_message = {
                        "userId": userId,
                        "message": message,
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
                        "userId": userId,
                        "message": "Já tomou seu remédio?",
                        "reminder_time": str(
                            next_reminder_time + timedelta(minutes=15)
                        ),
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
                        if frequency >= 1:
                            update_sql = """
                            UPDATE reminders
                            SET frequency = frequency - 1
                            WHERE id = %s
                            """
                            cursor.execute(update_sql, (reminder_id,))
                            connection.commit()
                            print(
                                f"Frequency decrementado para {frequency - 1} para o reminder_id {reminder_id}"
                            )
                        else:
                            # Quando frequency for 0, muda o status para done
                            update_sql = """
                            UPDATE reminders
                            SET done = TRUE
                            WHERE id = %s
                            """
                            cursor.execute(update_sql, (reminder_id,))
                            connection.commit()
                            print(f"Reminder {reminder_id} marcado como 'done'.")
                    else:
                        print(f"Erro ao agendar a segunda notificação: {response}")
                else:
                    # Caso ainda não esteja na hora
                    print(f"Ainda não está na hora de: {message}")

    except Exception as e:
        print(f"Erro ao verificar lembretes: {str(e)}")

    finally:
        # Fechar a conexão
        connection.close()


# # Função CLI usando Click
# @click.command()
# @click.argument("json_data")
# def cli(json_data):
#     """CLI para inserir dados no banco de dados MySQL a partir de uma string JSON"""

#     # Convertendo o argumento string para dicionário
#     try:
#         # Para que a string seja lida como JSON, precisamos substituir aspas simples por aspas duplas
#         json_data = json_data.replace("'", '"')
#         data = json.loads(json_data)
#     except json.JSONDecodeError as e:
#         click.echo(f"Erro ao converter JSON: {e}")
#         return

#     # Construindo o evento como se fosse passado para o Lambda
#     event = {"body": json.dumps(data)}

#     # Chama a função lambda_save_db
#     result = lambda_save_db(event)

#     # Mostra o resultado
#     click.echo(f"Resultado: {result['body']}")


# Função CLI usando Click
@click.group()
def cli():
    """CLI para gerenciar lembretes."""


@click.command()
@click.argument("json_data")
def add(json_data):
    """Adicionar um lembrete ao banco de dados MySQL a partir de uma string JSON"""

    # Convertendo o argumento string para dicionário
    try:
        json_data = json_data.replace("'", '"')
        data = json.loads(json_data)
    except json.JSONDecodeError as e:
        click.echo(f"Erro ao converter JSON: {e}")
        return

    # Construindo o evento como se fosse passado para o Lambda
    event = {"body": json.dumps(data)}

    # Chama a função lambda_save_db
    result = lambda_save_db(event)

    # Mostra o resultado
    click.echo(f"Resultado: {result['body']}")


@click.command()
def send_reminders():
    """Verificar lembretes e enviar notificações pela fila SQS."""

    lambda_send_queue()
    click.echo("Verificação de lembretes concluída.")


# Adicionando os comandos ao grupo CLI
cli.add_command(add)
cli.add_command(send_reminders)


if __name__ == "__main__":
    cli()
