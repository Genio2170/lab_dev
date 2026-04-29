import sqlite3
import logging
from typing import Optional, List, Tuple, Any, Union

class Conexao:
    def __init__(self, banco="schema.db"):
        self.banco = banco
        self.conexao: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        
        # Configurar logging se não estiver configurado
        if not logging.getLogger().handlers:
            logging.basicConfig(level=logging.INFO)

    def conectar(self) -> bool:
        """Estabelece conexão com o banco SQLite"""
        try:
            if self.conexao is not None:
                logging.warning("Conexão já existe, fechando conexão anterior")
                self.desconectar()
                
            self.conexao = sqlite3.connect(self.banco)
            self.cursor = self.conexao.cursor()
            logging.info(f"Conectado ao SQLite: {self.banco}")
            return True
        except sqlite3.Error as e:
            logging.error(f"Erro ao conectar ao SQLite: {e}")
            self.conexao = None
            self.cursor = None
            return False
        except Exception as e:
            logging.error(f"Erro inesperado ao conectar: {e}")
            self.conexao = None
            self.cursor = None
            return False

    def desconectar(self) -> None:
        """Fecha a conexão com o banco SQLite"""
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
                
            if self.conexao:
                self.conexao.close()
                self.conexao = None
                logging.info("Conexão SQLite encerrada")
        except Exception as e:
            logging.error(f"Erro ao encerrar conexão: {e}")

    def executar(self, query: str, dados: Union[Tuple, List] = ()) -> bool:
        """Executa uma query SQL (INSERT, UPDATE, DELETE)"""
        try:
            if not self.cursor or not self.conexao:
                logging.error("Não há conexão ativa com o banco")
                return False
                
            self.cursor.execute(query, dados)
            self.conexao.commit()
            logging.debug(f"Query executada: {query[:50]}...")
            return True
            
        except sqlite3.Error as e:
            logging.error(f"Erro ao executar query: {e}")
            if self.conexao:
                self.conexao.rollback()
            return False
        except Exception as e:
            logging.error(f"Erro inesperado ao executar query: {e}")
            return False

    def buscar(self, query: str, dados: Union[Tuple, List] = ()) -> Optional[List[Tuple[Any, ...]]]:      
        """Executa uma query SELECT e retorna os resultados"""
        try:
            if not self.cursor:
                logging.error("Não há conexão ativa com o banco")
                return None
                
            self.cursor.execute(query, dados)
            resultados = self.cursor.fetchall()
            logging.debug(f"Query de busca executada: {query[:50]}... - {len(resultados)} resultados")
            return resultados
            
        except sqlite3.Error as e:
            logging.error(f"Erro ao buscar dados: {e}")
            return None
        except Exception as e:
            logging.error(f"Erro inesperado ao buscar dados: {e}")
            return None
    
    def buscar_um(self, query: str, dados: Union[Tuple, List] = ()) -> Optional[Tuple[Any, ...]]:
        """Executa uma query SELECT e retorna apenas o primeiro resultado"""
        try:
            if not self.cursor:
                logging.error("Não há conexão ativa com o banco")
                return None
                
            self.cursor.execute(query, dados)
            resultado = self.cursor.fetchone()
            logging.debug(f"Query de busca (um resultado): {query[:50]}...")
            return resultado
            
        except sqlite3.Error as e:
            logging.error(f"Erro ao buscar um resultado: {e}")
            return None
        except Exception as e:
            logging.error(f"Erro inesperado ao buscar um resultado: {e}")
            return None
    
    def executar_muitos(self, query: str, dados_lista: List[Tuple]) -> bool:
        """Executa a mesma query com múltiplos conjuntos de dados"""
        try:
            if not self.cursor or not self.conexao:
                logging.error("Não há conexão ativa com o banco")
                return False
                
            self.cursor.executemany(query, dados_lista)
            self.conexao.commit()
            logging.debug(f"Query executada para {len(dados_lista)} registros")
            return True
            
        except sqlite3.Error as e:
            logging.error(f"Erro ao executar múltiplas queries: {e}")
            if self.conexao:
                self.conexao.rollback()
            return False
        except Exception as e:
            logging.error(f"Erro inesperado ao executar múltiplas queries: {e}")
            return False
    
    def existe_tabela(self, nome_tabela: str) -> bool:
        """Verifica se uma tabela existe no banco"""
        resultado = self.buscar_um(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (nome_tabela,)
        )
        return resultado is not None
    
    def contar_registros(self, tabela: str, condicao: str = "", dados: Union[Tuple, List] = ()) -> int:
        """Conta o número de registros em uma tabela"""
        query = f"SELECT COUNT(*) FROM {tabela}"
        if condicao:
            query += f" WHERE {condicao}"
        
        resultado = self.buscar_um(query, dados)
        return resultado[0] if resultado else 0
    
    def esta_conectado(self) -> bool:
        """Verifica se há uma conexão ativa com o banco"""
        return self.conexao is not None and self.cursor is not None
    
    def __enter__(self):
        """Context manager - entrada"""
        self.conectar()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager - saída"""
        self.desconectar()
        
    def __del__(self):
        """Destructor - garante que a conexão seja fechada"""
        self.desconectar()