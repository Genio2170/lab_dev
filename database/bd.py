import mysql.connector
from mysql.connector import Error

def conectar_banco():
    linha=[]
    try:
        # Configuração da conexão
        conexao = mysql.connector.connect(
            host='localhost',          # Geralmente localhost
            database='user_bd', # O nome que você deu ao banco
            user='root',               # Usuário padrão do MySQL
            password=''                # Sua senha (vazia por padrão no XAMPP)
        )

        if conexao.is_connected():
            print("Conectado ao MySQL com sucesso!")
            
            # O cursor permite executar comandos SQL
            cursor = conexao.cursor()
            cursor.execute("SELECT DATABASE();")
            linha = cursor.fetchone()
            if linha:
                print(f"Você está conectado ao banco")

    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")

    finally:
        # Sempre feche a conexão ao terminar
        if 'conexao' in locals() and conexao.is_connected():
            cursor.close()
            conexao.close()
            print("Conexão encerrada.")

if __name__ == "__main__":
    conectar_banco()
    class Conexao:
        def __init__(self, host='localhost', database='user_bd', user='root', password=''):
            self.host = host
            self.database = database
            self.user = user
            self.password = password
            self.conexao = None
            self.cursor = None

        def conectar(self):
            try:
                self.conexao = mysql.connector.connect(
                    host=self.host,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
                if self.conexao.is_connected():
                    self.cursor = self.conexao.cursor()
                    print("Conectado ao MySQL com sucesso!")
                    return True
            except Error as e:
                print(f"Erro ao conectar ao MySQL: {e}")
                return False

        def desconectar(self):
            if self.conexao and self.conexao.is_connected():
                if self.cursor:
                    self.cursor.close()
                self.conexao.close()
                print("Conexão encerrada.")

        def executar(self, query):
            if self.cursor:
                self.cursor.execute(query)
                self.conexao

        def buscar(self, query):
            if self.cursor:
                self.cursor.execute(query)
                return self.cursor.fetchall()