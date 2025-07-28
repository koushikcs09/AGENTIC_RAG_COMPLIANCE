
"""
Database connection and utilities for Snowflake integration.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
import snowflake.connector
from snowflake.connector import DictCursor
from snowflake.sqlalchemy import URL
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .config import config

logger = logging.getLogger(__name__)


class SnowflakeConnection:
    """Snowflake database connection manager."""
    
    def __init__(self):
        self.connection_params = {
            'account': config.snowflake.account,
            'user': config.snowflake.user,
            'password': config.snowflake.password,
            'warehouse': config.snowflake.warehouse,
            'database': config.snowflake.database,
            'schema': config.snowflake.schema,
            'role': config.snowflake.role
        }
        self._engine = None
        self._session_factory = None
    
    @property
    def engine(self):
        """Get SQLAlchemy engine."""
        if self._engine is None:
            url = URL(**self.connection_params)
            self._engine = create_engine(url, echo=not config.is_production())
        return self._engine
    
    @property
    def session_factory(self):
        """Get SQLAlchemy session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory
    
    @contextmanager
    def get_connection(self):
        """Get raw Snowflake connection."""
        conn = None
        try:
            conn = snowflake.connector.connect(**self.connection_params)
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_session(self):
        """Get SQLAlchemy session."""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a query and return results as list of dictionaries."""
        with self.get_connection() as conn:
            cursor = conn.cursor(DictCursor)
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
            except Exception as e:
                logger.error(f"Query execution error: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_non_query(self, query: str, params: Optional[Dict] = None) -> int:
        """Execute a non-query statement and return affected rows."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.rowcount
            except Exception as e:
                logger.error(f"Non-query execution error: {e}")
                raise
            finally:
                cursor.close()
    
    def bulk_insert(self, table: str, data: List[Dict], schema: str = None) -> int:
        """Bulk insert data into a table."""
        if not data:
            return 0
        
        schema_prefix = f"{schema}." if schema else ""
        columns = list(data[0].keys())
        placeholders = ", ".join([f"%({col})s" for col in columns])
        
        query = f"""
        INSERT INTO {schema_prefix}{table} ({', '.join(columns)})
        VALUES ({placeholders})
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany(query, data)
                return cursor.rowcount
            except Exception as e:
                logger.error(f"Bulk insert error: {e}")
                raise
            finally:
                cursor.close()


class VectorStore:
    """Vector store operations for embeddings and similarity search."""
    
    def __init__(self, db_connection: SnowflakeConnection):
        self.db = db_connection
    
    def generate_embedding(self, text: str, model: str = None) -> List[float]:
        """Generate embedding using Snowflake Cortex."""
        model = model or config.snowflake.embedding_model
        query = f"""
        SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_1536('{model}', %s) as embedding
        """
        
        result = self.db.execute_query(query, {'text': text})
        if result:
            return result[0]['EMBEDDING']
        return []
    
    def store_clause_embedding(self, clause_id: str, clause_text: str, 
                             metadata: Optional[Dict] = None) -> str:
        """Store clause embedding in vector store."""
        embedding = self.generate_embedding(clause_text)
        
        data = {
            'embedding_id': f"emb_{clause_id}",
            'clause_id': clause_id,
            'embedding': json.dumps(embedding),
            'embedding_model': config.snowflake.embedding_model,
            'chunk_text': clause_text,
            'embedding_metadata': json.dumps(metadata or {})
        }
        
        query = """
        INSERT INTO VECTORS.CLAUSE_EMBEDDINGS 
        (embedding_id, clause_id, embedding, embedding_model, chunk_text, embedding_metadata)
        VALUES (%(embedding_id)s, %(clause_id)s, PARSE_JSON(%(embedding)s), 
                %(embedding_model)s, %(chunk_text)s, PARSE_JSON(%(embedding_metadata)s))
        """
        
        self.db.execute_non_query(query, data)
        return data['embedding_id']
    
    def find_similar_regulations(self, clause_embedding: List[float], 
                               threshold: float = None, limit: int = 10) -> List[Dict]:
        """Find similar regulations using vector similarity."""
        threshold = threshold or config.processing.similarity_threshold
        embedding_json = json.dumps(clause_embedding)
        
        query = f"""
        SELECT 
            re.regulation_id,
            re.regulation_text,
            re.regulation_category,
            re.jurisdiction,
            re.act_name,
            VECTOR_COSINE_SIMILARITY(PARSE_JSON('{embedding_json}'), re.embedding) as similarity_score
        FROM VECTORS.REGULATION_EMBEDDINGS re
        WHERE VECTOR_COSINE_SIMILARITY(PARSE_JSON('{embedding_json}'), re.embedding) >= {threshold}
        ORDER BY similarity_score DESC
        LIMIT {limit}
        """
        
        return self.db.execute_query(query)
    
    def batch_similarity_computation(self, batch_size: int = None) -> int:
        """Compute similarities for unprocessed clause embeddings."""
        batch_size = batch_size or config.processing.batch_size
        
        query = f"""
        CALL VECTORS.COMPUTE_BATCH_SIMILARITIES({batch_size})
        """
        
        result = self.db.execute_query(query)
        return len(result) if result else 0


class DocumentRepository:
    """Repository for document-related database operations."""
    
    def __init__(self, db_connection: SnowflakeConnection):
        self.db = db_connection
    
    def create_document(self, document_data: Dict) -> str:
        """Create a new document record."""
        query = """
        INSERT INTO RAW.RAW_DOCUMENTS 
        (document_id, file_name, file_path, file_size_bytes, file_hash, 
         content_type, document_type, raw_content, metadata, created_by)
        VALUES (%(document_id)s, %(file_name)s, %(file_path)s, %(file_size_bytes)s,
                %(file_hash)s, %(content_type)s, %(document_type)s, %(raw_content)s,
                PARSE_JSON(%(metadata)s), %(created_by)s)
        """
        
        self.db.execute_non_query(query, document_data)
        return document_data['document_id']
    
    def update_document_status(self, document_id: str, status: str, 
                             metadata: Optional[Dict] = None) -> None:
        """Update document processing status."""
        params = {
            'document_id': document_id,
            'processing_status': status,
            'updated_at': 'CURRENT_TIMESTAMP()'
        }
        
        query = """
        UPDATE RAW.RAW_DOCUMENTS 
        SET processing_status = %(processing_status)s,
            updated_at = CURRENT_TIMESTAMP()
        """
        
        if metadata:
            params['metadata'] = json.dumps(metadata)
            query += ", metadata = PARSE_JSON(%(metadata)s)"
        
        query += " WHERE document_id = %(document_id)s"
        
        self.db.execute_non_query(query, params)
    
    def get_document(self, document_id: str) -> Optional[Dict]:
        """Get document by ID."""
        query = """
        SELECT * FROM RAW.RAW_DOCUMENTS 
        WHERE document_id = %(document_id)s
        """
        
        result = self.db.execute_query(query, {'document_id': document_id})
        return result[0] if result else None
    
    def list_documents(self, filters: Optional[Dict] = None, 
                      page: int = 1, limit: int = 20) -> Tuple[List[Dict], int]:
        """List documents with filtering and pagination."""
        where_conditions = []
        params = {}
        
        if filters:
            if filters.get('document_type'):
                where_conditions.append("document_type = %(document_type)s")
                params['document_type'] = filters['document_type']
            
            if filters.get('processing_status'):
                where_conditions.append("processing_status = %(processing_status)s")
                params['processing_status'] = filters['processing_status']
            
            if filters.get('date_from'):
                where_conditions.append("upload_timestamp >= %(date_from)s")
                params['date_from'] = filters['date_from']
            
            if filters.get('date_to'):
                where_conditions.append("upload_timestamp <= %(date_to)s")
                params['date_to'] = filters['date_to']
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Count query
        count_query = f"SELECT COUNT(*) as total FROM RAW.RAW_DOCUMENTS{where_clause}"
        count_result = self.db.execute_query(count_query, params)
        total_count = count_result[0]['TOTAL'] if count_result else 0
        
        # Data query with pagination
        offset = (page - 1) * limit
        params.update({'limit': limit, 'offset': offset})
        
        data_query = f"""
        SELECT document_id, file_name, document_type, processing_status, 
               upload_timestamp, file_size_bytes, metadata
        FROM RAW.RAW_DOCUMENTS{where_clause}
        ORDER BY upload_timestamp DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """
        
        documents = self.db.execute_query(data_query, params)
        return documents, total_count


# Global database connection instance
db_connection = SnowflakeConnection()
vector_store = VectorStore(db_connection)
document_repository = DocumentRepository(db_connection)
