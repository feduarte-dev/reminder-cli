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

        # Criar a tabela `users`
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            phone_number VARCHAR(20) UNIQUE NOT NULL
        );
        """
        )
        print("Tabela 'users' criada (ou já existe).")

        # Criar a tabela `reminders`
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS reminders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            userId INT,
            message VARCHAR(50),
            frequency INT DEFAULT 1,
            gap INT,
            startAt DATETIME DEFAULT CURRENT_TIMESTAMP,
            duration DATETIME,
            done BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (userId) REFERENCES users(id) ON DELETE CASCADE
        );
        """
        )
        print("Tabela 'reminders' criada (ou já existe).")

        # Inserir dados na tabela `users`
        cursor.execute(
            """
        INSERT INTO users (phone_number)
        VALUES
        ('+5511987654322'),
        ('+5511987654321');
        """
        )
        print("Dados inseridos na tabela 'users'.")

        # Inserir dados na tabela `reminders`, calculando o valor de `duration`
        cursor.execute(
            """
        INSERT INTO reminders (userId, message, frequency, gap, duration)
        VALUES
        (1, 'lembre me de tomar remedio', 3, 6, DATE_ADD(NOW(), INTERVAL (3 * 6) HOUR)),
        (1, 'lembre me de tomar remedio', 3, 6, DATE_ADD(NOW(), INTERVAL (3 * 6) HOUR)),
        (2, 'lembre me de levantar!', 1, 12, DATE_ADD(NOW(), INTERVAL (1 * 12) HOUR));
        """
        )
        print("Dados inseridos na tabela 'reminders'.")

        # Confirmar mudanças
        connection.commit()

except pymysql.MySQLError as e:
    print(f"Erro ao executar o script: {e}")
finally:
    # Fechar a conexão
    connection.close()
