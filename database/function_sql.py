from bd import Conexao
import sqlite3

class FunctionSql(Conexao):
    def __init__(self, banco="schema.db"):
        super().__init__(banco)

    def conectar(self):
        return super().conectar()

    def _garantir_conexao(self):
        if self.conexao is None:
            self.conectar()
        if self.conexao is None:
            raise Exception("Erro ao conectar ao banco")
        return self.conexao

    def executar_query(self, sql, valores=None):
        try:
            conexao = self._garantir_conexao()
            cursor = conexao.cursor()

            cursor.execute(sql, valores or ())
            conexao.commit()

            print("✅ Operação realizada com sucesso!")

        except Exception as e:
            print("❌ Erro:", e)

    def ler_dados(self, sql, valores=None):
        try:
            conexao = self._garantir_conexao()
            cursor = conexao.cursor()

            cursor.execute(sql, valores or ())
            colunas = [desc[0] for desc in cursor.description]

            # transforma em dicionário (igual MySQL dictionary=True)
            resultados = []
            for linha in cursor.fetchall():
                resultados.append(dict(zip(colunas, linha)))

            return resultados

        except Exception as e:
            print("❌ Erro:", e)
            return []

    def fechar_conexao(self):
        if self.conexao:
            self.conexao.close()
            self.conexao = None