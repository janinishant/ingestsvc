import asyncio
from typing import Optional, Any, Dict, List
import asyncpg
from asyncpg import Pool, Connection
import logging
from contextlib import asynccontextmanager

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseAccessor:
    """
    Single database accessor class for PostgreSQL connection management.
    Handles connection pooling, schema management, and query execution.
    """
    
    def __init__(self):
        self.pool: Optional[Pool] = None
        self.schema = settings.DB_SCHEMA
        self._lock = asyncio.Lock()
    
    async def connect(self) -> None:
        """Initialize the database connection pool."""
        if self.pool is not None:
            return
            
        async with self._lock:
            if self.pool is not None:
                return
                
            try:
                logger.info(f"Connecting to database: {settings.DB_NAME} on {settings.DB_HOST}:{settings.DB_PORT}")
                
                self.pool = await asyncpg.create_pool(
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                    database=settings.DB_NAME,
                    min_size=settings.DB_POOL_MIN_SIZE,
                    max_size=settings.DB_POOL_MAX_SIZE,
                    max_queries=settings.DB_POOL_MAX_QUERIES,
                    max_inactive_connection_lifetime=settings.DB_POOL_MAX_INACTIVE_CONNECTION_LIFETIME,
                    command_timeout=60.0,
                    ssl='require',
                    server_settings={
                        'search_path': f'{self.schema}, public'
                    }
                )
                
                # Test the connection and schema
                await self._verify_connection()
                
                logger.info(f"Successfully connected to database with schema: {self.schema}")
                
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
    
    async def disconnect(self) -> None:
        """Close the database connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")
    
    async def _verify_connection(self) -> None:
        """Verify database connection and schema exists."""
        async with self.pool.acquire() as conn:
            # Check if schema exists
            schema_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = $1)",
                self.schema
            )
            
            if not schema_exists:
                raise ValueError(f"Schema '{self.schema}' does not exist in database '{settings.DB_NAME}'")
            
            # Verify we can query with the schema
            current_schema = await conn.fetchval("SELECT current_schema()")
            logger.info(f"Current schema: {current_schema}")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool."""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            # Ensure schema is set for this connection
            await conn.execute(f"SET search_path TO {self.schema}, public")
            yield conn
    
    async def execute(self, query: str, *args, timeout: float = None) -> str:
        """Execute a query without returning results."""
        async with self.acquire() as conn:
            return await conn.execute(query, *args, timeout=timeout)
    
    async def executemany(self, query: str, args: List[tuple], timeout: float = None) -> None:
        """Execute a query multiple times with different arguments."""
        async with self.acquire() as conn:
            await conn.executemany(query, args, timeout=timeout)
    
    async def fetch(self, query: str, *args, timeout: float = None) -> List[asyncpg.Record]:
        """Execute a query and fetch all results."""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)
    
    async def fetchrow(self, query: str, *args, timeout: float = None) -> Optional[asyncpg.Record]:
        """Execute a query and fetch a single row."""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)
    
    async def fetchval(self, query: str, *args, column: int = 0, timeout: float = None) -> Any:
        """Execute a query and fetch a single value."""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args, column=column, timeout=timeout)
    
    @asynccontextmanager
    async def transaction(self):
        """Create a database transaction context."""
        async with self.acquire() as conn:
            async with conn.transaction():
                yield conn
    
    async def create_table_if_not_exists(self, table_name: str, table_schema: str) -> None:
        """Create a table if it doesn't exist."""
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.schema}.{table_name} (
            {table_schema}
        )
        """
        await self.execute(query)
        logger.info(f"Table {self.schema}.{table_name} created or already exists")
    
    async def insert_one(self, table: str, data: Dict[str, Any]) -> Any:
        """Insert a single row into a table."""
        columns = list(data.keys())
        values = list(data.values())
        placeholders = [f"${i+1}" for i in range(len(values))]
        
        query = f"""
        INSERT INTO {self.schema}.{table} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        RETURNING *
        """
        
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *values)
    
    async def insert_many(self, table: str, data: List[Dict[str, Any]]) -> None:
        """Insert multiple rows into a table."""
        if not data:
            return
        
        columns = list(data[0].keys())
        
        # Prepare the COPY command
        async with self.acquire() as conn:
            await conn.copy_records_to_table(
                table_name=table,
                schema_name=self.schema,
                records=[tuple(row[col] for col in columns) for row in data],
                columns=columns
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the database connection."""
        try:
            if not self.pool:
                await self.connect()
            
            async with self.acquire() as conn:
                # Simple query to test connection
                result = await conn.fetchval("SELECT 1")
                pool_size = self.pool.get_size() if self.pool else 0
                idle_size = self.pool.get_idle_size() if self.pool else 0
                
                return {
                    "status": "healthy",
                    "database": settings.DB_NAME,
                    "schema": self.schema,
                    "pool_size": pool_size,
                    "idle_connections": idle_size,
                    "connected": result == 1
                }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "database": settings.DB_NAME,
                "schema": self.schema
            }


# Create a singleton instance
db = DatabaseAccessor()