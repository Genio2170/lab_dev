import sqlite3

class Conexao:
    def __init__(self, banco="user_bd.db"):
        self.banco = banco
        self.conexao = None
        self.cursor = None

    def conectar(self):
        try:
            self.conexao = sqlite3.connect(self.banco)
            self.cursor = self.conexao.cursor()
            print("Conectado ao SQLite!")
            return True
        except Exception as e:
            print("Erro:", e)
            return False

    def desconectar(self):
        if self.conexao:
            self.conexao.close()
            print("Conexão encerrada.")

    def executar(self, query, dados=()):
        if self.cursor:
            self.cursor.execute(query, dados)
            self.conexao.commit()

    def buscar(self, query, dados=()):
        if self.cursor:
            self.cursor.execute(query, dados)
            return self.cursor.fetchall()