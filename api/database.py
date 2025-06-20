"""
Sistema de Banco de Dados Opcional

Implementa integração opcional com SQLAlchemy para:
- Persistência de usuários
- Histórico de tarefas
- Logs estruturados
- Configurações
"""

from typing import Optional, Dict, Any, List
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from api.config import settings

# Base para modelos
Base = declarative_base()

# Variáveis globais
engine = None
SessionLocal = None
database_available = False


class User(Base):
    """Modelo de usuário no banco de dados"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    full_name = Column(String(100))
    hashed_password = Column(String(100), nullable=False)
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    api_key = Column(String(100), unique=True, index=True)


class ScrapingTask(Base):
    """Modelo de tarefa de scraping no banco de dados"""
    __tablename__ = "scraping_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(50), index=True, nullable=False)
    status = Column(String(20), index=True, nullable=False)
    config = Column(JSON)
    progress = Column(JSON)
    result_summary = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class ApiLog(Base):
    """Modelo de logs da API"""
    __tablename__ = "api_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String(10), index=True)  # INFO, ERROR, WARNING
    endpoint = Column(String(100), index=True)
    method = Column(String(10))
    user_id = Column(String(50), index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    request_data = Column(JSON)
    response_status = Column(Integer)
    response_time_ms = Column(Integer)
    error_message = Column(Text)


class SystemMetric(Base):
    """Modelo de métricas do sistema"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metric_name = Column(String(50), index=True)
    metric_value = Column(JSON)
    metadata = Column(JSON)


async def init_db():
    """
    Inicializa conexão com banco de dados se disponível
    
    Se DATABASE_URL não estiver configurada, usa armazenamento em memória
    """
    global engine, SessionLocal, database_available
    
    if not settings.DATABASE_URL:
        print("📦 Banco de dados não configurado - usando armazenamento em memória")
        database_available = False
        return
    
    try:
        print("🔌 Conectando ao banco de dados...")
        
        # Criar engine
        engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        # Criar tabelas
        Base.metadata.create_all(bind=engine)
        
        # Criar session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Testar conexão
        with SessionLocal() as session:
            session.execute("SELECT 1")
        
        database_available = True
        print("✅ Banco de dados conectado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao conectar banco de dados: {e}")
        print("📦 Continuando com armazenamento em memória...")
        database_available = False


def get_db() -> Session:
    """
    Dependency para obter sessão do banco de dados
    
    Returns:
        Sessão do SQLAlchemy ou None se não disponível
    """
    if not database_available or not SessionLocal:
        return None
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== OPERAÇÕES DE USUÁRIO ====================

def create_user_db(
    username: str, 
    email: str, 
    hashed_password: str, 
    full_name: str = "",
    role: str = "user"
) -> Optional[Dict[str, Any]]:
    """Cria usuário no banco de dados"""
    if not database_available:
        return None
    
    try:
        with SessionLocal() as session:
            # Verificar se já existe
            existing = session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing:
                return None
            
            # Criar usuário
            user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                full_name=full_name,
                role=role
            )
            
            session.add(user)
            session.commit()
            session.refresh(user)
            
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at
            }
            
    except SQLAlchemyError as e:
        print(f"Erro ao criar usuário: {e}")
        return None


def get_user_db(username: str) -> Optional[Dict[str, Any]]:
    """Busca usuário no banco de dados"""
    if not database_available:
        return None
    
    try:
        with SessionLocal() as session:
            user = session.query(User).filter(User.username == username).first()
            
            if not user:
                return None
            
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "hashed_password": user.hashed_password,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "last_login": user.last_login
            }
            
    except SQLAlchemyError as e:
        print(f"Erro ao buscar usuário: {e}")
        return None


def update_user_login_db(username: str):
    """Atualiza último login do usuário"""
    if not database_available:
        return
    
    try:
        with SessionLocal() as session:
            user = session.query(User).filter(User.username == username).first()
            if user:
                user.last_login = datetime.utcnow()
                session.commit()
                
    except SQLAlchemyError as e:
        print(f"Erro ao atualizar login: {e}")


# ==================== OPERAÇÕES DE TAREFAS ====================

def save_task_db(task_data: Dict[str, Any]) -> bool:
    """Salva tarefa no banco de dados"""
    if not database_available:
        return False
    
    try:
        with SessionLocal() as session:
            # Verificar se já existe
            existing = session.query(ScrapingTask).filter(
                ScrapingTask.task_id == task_data["task_id"]
            ).first()
            
            if existing:
                # Atualizar existente
                existing.status = task_data["status"]
                existing.progress = task_data.get("progress")
                existing.result_summary = task_data.get("result_summary")
                existing.error_message = task_data.get("error_message")
                existing.completed_at = task_data.get("completed_at")
            else:
                # Criar nova
                task = ScrapingTask(
                    task_id=task_data["task_id"],
                    user_id=task_data["user_id"],
                    status=task_data["status"],
                    config=task_data.get("config"),
                    progress=task_data.get("progress"),
                    result_summary=task_data.get("result_summary"),
                    error_message=task_data.get("error_message"),
                    started_at=task_data.get("started_at"),
                    completed_at=task_data.get("completed_at")
                )
                session.add(task)
            
            session.commit()
            return True
            
    except SQLAlchemyError as e:
        print(f"Erro ao salvar tarefa: {e}")
        return False


def get_task_db(task_id: str) -> Optional[Dict[str, Any]]:
    """Busca tarefa no banco de dados"""
    if not database_available:
        return None
    
    try:
        with SessionLocal() as session:
            task = session.query(ScrapingTask).filter(
                ScrapingTask.task_id == task_id
            ).first()
            
            if not task:
                return None
            
            return {
                "task_id": task.task_id,
                "user_id": task.user_id,
                "status": task.status,
                "config": task.config,
                "progress": task.progress,
                "result_summary": task.result_summary,
                "error_message": task.error_message,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "created_at": task.created_at
            }
            
    except SQLAlchemyError as e:
        print(f"Erro ao buscar tarefa: {e}")
        return None


def get_user_tasks_db(user_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """Busca tarefas do usuário no banco de dados"""
    if not database_available:
        return []
    
    try:
        with SessionLocal() as session:
            tasks = session.query(ScrapingTask).filter(
                ScrapingTask.user_id == user_id
            ).order_by(
                ScrapingTask.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            return [
                {
                    "task_id": task.task_id,
                    "status": task.status,
                    "config": task.config,
                    "progress": task.progress,
                    "result_summary": task.result_summary,
                    "error_message": task.error_message,
                    "started_at": task.started_at,
                    "completed_at": task.completed_at,
                    "created_at": task.created_at
                }
                for task in tasks
            ]
            
    except SQLAlchemyError as e:
        print(f"Erro ao buscar tarefas do usuário: {e}")
        return []


# ==================== OPERAÇÕES DE LOGS ====================

def log_api_request_db(
    endpoint: str,
    method: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_data: Optional[Dict] = None,
    response_status: Optional[int] = None,
    response_time_ms: Optional[int] = None,
    error_message: Optional[str] = None,
    level: str = "INFO"
):
    """Registra requisição da API no banco de dados"""
    if not database_available:
        return
    
    try:
        with SessionLocal() as session:
            log = ApiLog(
                level=level,
                endpoint=endpoint,
                method=method,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_data=request_data,
                response_status=response_status,
                response_time_ms=response_time_ms,
                error_message=error_message
            )
            
            session.add(log)
            session.commit()
            
    except SQLAlchemyError as e:
        print(f"Erro ao registrar log: {e}")


# ==================== OPERAÇÕES DE MÉTRICAS ====================

def save_metric_db(metric_name: str, metric_value: Any, metadata: Optional[Dict] = None):
    """Salva métrica no banco de dados"""
    if not database_available:
        return
    
    try:
        with SessionLocal() as session:
            metric = SystemMetric(
                metric_name=metric_name,
                metric_value=metric_value,
                metadata=metadata
            )
            
            session.add(metric)
            session.commit()
            
    except SQLAlchemyError as e:
        print(f"Erro ao salvar métrica: {e}")


def get_metrics_db(
    metric_name: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Busca métricas no banco de dados"""
    if not database_available:
        return []
    
    try:
        with SessionLocal() as session:
            query = session.query(SystemMetric)
            
            if metric_name:
                query = query.filter(SystemMetric.metric_name == metric_name)
            
            if start_time:
                query = query.filter(SystemMetric.timestamp >= start_time)
            
            if end_time:
                query = query.filter(SystemMetric.timestamp <= end_time)
            
            metrics = query.order_by(
                SystemMetric.timestamp.desc()
            ).limit(limit).all()
            
            return [
                {
                    "metric_name": metric.metric_name,
                    "metric_value": metric.metric_value,
                    "metadata": metric.metadata,
                    "timestamp": metric.timestamp
                }
                for metric in metrics
            ]
            
    except SQLAlchemyError as e:
        print(f"Erro ao buscar métricas: {e}")
        return []


# ==================== HELPERS ====================

def is_database_available() -> bool:
    """Verifica se o banco de dados está disponível"""
    return database_available


def get_database_stats() -> Dict[str, Any]:
    """Retorna estatísticas do banco de dados"""
    if not database_available:
        return {"available": False}
    
    try:
        with SessionLocal() as session:
            user_count = session.query(User).count()
            task_count = session.query(ScrapingTask).count()
            log_count = session.query(ApiLog).count()
            metric_count = session.query(SystemMetric).count()
            
            return {
                "available": True,
                "user_count": user_count,
                "task_count": task_count,
                "log_count": log_count,
                "metric_count": metric_count
            }
            
    except SQLAlchemyError as e:
        print(f"Erro ao obter estatísticas: {e}")
        return {"available": True, "error": str(e)}


# Export principais
__all__ = [
    "init_db",
    "get_db",
    "is_database_available",
    "get_database_stats",
    "create_user_db",
    "get_user_db",
    "update_user_login_db",
    "save_task_db",
    "get_task_db",
    "get_user_tasks_db",
    "log_api_request_db",
    "save_metric_db",
    "get_metrics_db"
]