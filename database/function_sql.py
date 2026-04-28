from bd import Conexao
from mysql.connector import Error

class FunctionSql(Conexao):
    def __init__(self, host, database, user, password):
        super().__init__(host, database, user, password)

    def conectar(self):
        """Estabelece a conexão usando a lógica da classe pai."""
        return super().conectar()

    def _garantir_conexao(self):
        """Garante que existe uma conexão ativa antes de executar operações."""
        if self.conexao is None:
            self.conectar()
        if self.conexao is None:
            raise ConnectionError("Não foi possível estabelecer conexão com o banco de dados.")
        return self.conexao

    def executar_query(self, sql, valores=None):
        """Executa comandos de INSERT, UPDATE e DELETE."""
        try:
            conexao = self._garantir_conexao()
            with conexao.cursor() as cursor:
                cursor.execute(sql, valores or ())
                conexao.commit()
                print("✅ Operação realizada com sucesso!")
        except Error as e:
            print(f"❌ Erro ao executar comando: {e}")

    def ler_dados(self, sql, valores=None):
        """Executa comandos de SELECT."""
        try:
            conexao = self._garantir_conexao()
            # 📖 Retorna os dados como dicionário para facilitar a leitura
            with conexao.cursor(dictionary=True) as cursor:
                cursor.execute(sql, valores or ())
                return cursor.fetchall()
        except Error as e:
            print(f"❌ Erro na leitura: {e}")
            return []

    def fechar_conexao(self):
        """Encerra a conexão chamando o método da classe pai."""
        metodo = getattr(super(), "fechar_conexao", None)
        if callable(metodo):
            metodo()
        elif self.conexao is not None:
            self.conexao.close()
            self.conexao = None