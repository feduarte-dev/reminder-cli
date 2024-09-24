import os
import json
import pymysql
import boto3
import click
from dotenv import load_dotenv

# Inicializando o cliente SQS
client = boto3.client("sqs")


# Carregar variáveis do .env
load_dotenv()

db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
port = int(os.getenv("DB_PORT"))


# Na documentação existe mais um parametro chamado 'context', devo adicioná-lo aqui?
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
            # Usar valores padrão se não forem fornecidos
            frequency = data.get("frequency", 1)  # Valor padrão de 1
            gap = data.get("gap", 0)  # Valor padrão de 0

            # Criação da query SQL
            sql = "INSERT INTO users (phone_number, message, frequency, gap) VALUES (%s, %s, %s, %s)"

            # Executa a query
            cursor.execute(sql, (phone_number, message, frequency, gap))

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


# Inicializando o cliente Lambda
lambda_client = boto3.client("lambda")


def lambda_send_queue(event):
    pass


# Função CLI usando Click
@click.command()
@click.argument("json_data")
def cli(json_data):
    """CLI para inserir dados no banco de dados MySQL a partir de uma string JSON"""

    # Convertendo o argumento string para dicionário
    try:
        # Para que a string seja lida como JSON, precisamos substituir aspas simples por aspas duplas
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


if __name__ == "__main__":
    cli()
