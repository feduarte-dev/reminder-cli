import os
import pymysql
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
port = int(os.getenv("DB_PORT"))

# Conectar ao servidor MySQL
connection = pymysql.connect(host=db_host, user=db_user, password=db_password)

try:
    with connection.cursor() as cursor:
        # Apagar o banco de dados se ele já existir
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name};")
        print(f"Banco de dados '{db_name}' apagado.")

        # Criar o banco de dados novamente
        cursor.execute(f"CREATE DATABASE {db_name};")
        print(f"Banco de dados '{db_name}' recriado.")

        # Usar o banco de dados criado
        cursor.execute(f"USE {db_name};")

        # Criar a tabela `users` (se não existir) com valores padrão para frequency e gap
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            phone_number VARCHAR(20),
            message VARCHAR(50),
            frequency INT DEFAULT 1,
            gap INT DEFAULT 0
        );
        """
        )
        print("Tabela 'users' criada (ou já existe).")

        # Inserir dados na tabela
        cursor.execute(
            """
        INSERT INTO users (phone_number, message, frequency, gap)
        VALUES
        ('+5511987654322', 'lembre me de tomar remedio', 5, 8);
        """
        )
        print("Dados inseridos na tabela 'users'.")
        cursor.execute(
            """
        INSERT INTO users (phone_number, message)
        VALUES
        ('+5511987654321', 'lembre me de levantar!');
        """
        )
        print("Dados inseridos na tabela 'users'.")

        # Confirmar mudanças
        connection.commit()

except pymysql.MySQLError as e:
    print(f"Erro ao executar o script: {e}")
finally:
    # Fechar a conexão
    connection.close()
