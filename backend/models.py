import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Caminho absoluto para o banco na pasta data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DATABASE_URL = f'sqlite:///{os.path.join(DATA_DIR, "crm.db")}'

# Engine com configurações otimizadas para evitar locks
engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
    echo=False
)

SessionLocal = sessionmaker(bind=engine, autoflush=True)
Base = declarative_base()

class Lead(Base):
    """
    Tabela principal de leads.
    Substitui: leads_*.csv + leads_tratados_para_envio.csv
    """
    __tablename__ = 'leads'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    empresa_original = Column(String(300), nullable=False)
    empresa_contato = Column(String(200), nullable=False)
    telefone = Column(String(15), nullable=False, index=True)
    bairro = Column(String(100))
    site = Column(String(500))
    segmento = Column(String(100), default='clínicas de estética')
    link_landing = Column(String(1000))  # Link para index.html personalizado
    link_preview = Column(String(1000))  # Link para preview_print.html
    prioridade = Column(Integer, default=0)
    pronto_para_enviar = Column(String(10), default='REVISAR')  # SIM ou REVISAR
    
    # Campos do CRM
    status = Column(String(50), default='Novo')  # Novo, Contatado, Interessado, Fechado
    ultimo_contato = Column(DateTime)
    observacao = Column(Text)
    caminho_print = Column(String(500))
    mensagem_whatsapp = Column(Text)
    
    # Metadados
    data_captura = Column(DateTime)
    data_processamento = Column(DateTime, default=datetime.now)
    data_envio = Column(DateTime)
    
    def to_dict(self):
        """Converte o objeto para dicionário (útil para API)"""
        return {
            'id': self.id,
            'empresa_original': self.empresa_original,
            'empresa_contato': self.empresa_contato,
            'telefone': self.telefone,
            'bairro': self.bairro,
            'site': self.site,
            'segmento': self.segmento,
            'link_landing': self.link_landing,
            'link_preview': self.link_preview,
            'prioridade': self.prioridade,
            'pronto_para_enviar': self.pronto_para_enviar,
            'status': self.status,
            'ultimo_contato': self.ultimo_contato.isoformat() if self.ultimo_contato else None,
            'observacao': self.observacao,
            'caminho_print': self.caminho_print,
            'mensagem_whatsapp': self.mensagem_whatsapp,
            'data_captura': self.data_captura.isoformat() if self.data_captura else None,
            'data_processamento': self.data_processamento.isoformat() if self.data_processamento else None,
            'data_envio': self.data_envio.isoformat() if self.data_envio else None,
        }

class ScrapingJob(Base):
    """
    Registra cada execução de scraping
    """
    __tablename__ = 'scraping_jobs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    consulta = Column(String(300), nullable=False)
    bairro = Column(String(100))
    nicho = Column(String(100))
    leads_encontrados = Column(Integer, default=0)
    leads_novos = Column(Integer, default=0)
    status = Column(String(20), default='executando')  # executando, concluido, erro
    log = Column(Text)
    data_inicio = Column(DateTime, default=datetime.now)
    data_fim = Column(DateTime)

class ScrapingProgress(Base):
    """
    Registra o progresso em tempo real do scraping
    """
    __tablename__ = 'scraping_progress'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, nullable=False, index=True)
    mensagem = Column(String(500), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'mensagem': self.mensagem,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }    

def init_db():
    """Cria todas as tabelas"""
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados inicializado com sucesso!")

def get_session():
    """Retorna uma nova sessão do banco"""
    return SessionLocal()

if __name__ == '__main__':
    init_db()