import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseConnector:
    def __init__(self, db_type="sqlite", db_path=None, db_host=None, db_name=None, 
                 db_user=None, db_password=None, db_port=None):
        """
        Initialize database connector.
        
        Args:
            db_type (str): Type of database (sqlite, mysql, postgresql)
            db_path (str): Path to SQLite database file
            db_host (str): Database host
            db_name (str): Database name
            db_user (str): Database username
            db_password (str): Database password
            db_port (str): Database port
        """
        self.db_type = db_type
        
        # Use provided arguments or get from environment variables
        self.db_path = db_path or os.getenv("DB_PATH")
        self.db_host = db_host or os.getenv("DB_HOST")
        self.db_name = db_name or os.getenv("DB_NAME")
        self.db_user = db_user or os.getenv("DB_USER")
        self.db_password = db_password or os.getenv("DB_PASSWORD")
        self.db_port = db_port or os.getenv("DB_PORT")
        
        self.engine = self._create_engine()
    
    def _create_engine(self):
        """Create appropriate SQLAlchemy engine based on database type."""
        try:
            if self.db_type == "sqlite":
                return create_engine(f"sqlite:///{self.db_path}")
            
            elif self.db_type == "mysql":
                return create_engine(
                    f"mysql+mysqlconnector://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
                )
            
            elif self.db_type == "postgresql":
                return create_engine(
                    f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
                )
            
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")
                
        except Exception as e:
            print(f"Error creating database engine: {str(e)}")
            return None
    
    def execute_query(self, query):
        """
        Execute SQL query and return results.
        
        Args:
            query (str): SQL query string
            
        Returns:
            DataFrame or str: Query result as pandas DataFrame or error message
        """
        try:
            # Check if engine is valid
            if self.engine is None:
                return "Database connection not established."
            
            # Execute query and return results as pandas DataFrame
            return pd.read_sql_query(text(query), self.engine)
            
        except Exception as e:
            return f"Error executing query: {str(e)}"
    
    def get_tables(self):
        """Get list of tables in the database."""
        try:
            if self.db_type == "sqlite":
                query = "SELECT name FROM sqlite_master WHERE type='table';"
            elif self.db_type == "mysql":
                query = "SHOW TABLES;"
            elif self.db_type == "postgresql":
                query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
            else:
                return "Unsupported database type."
            
            return pd.read_sql_query(text(query), self.engine)
            
        except Exception as e:
            return f"Error fetching tables: {str(e)}"
    
    def get_schema_info(self):
        """Get schema information for all tables in the database."""
        try:
            schema_info = []
            
            if self.db_type == "sqlite":
                # Get list of tables
                tables_query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
                tables = pd.read_sql_query(text(tables_query), self.engine)
                
                for table_name in tables['name']:
                    # Get column info for each table
                    pragma_query = f"PRAGMA table_info('{table_name}');"
                    columns = pd.read_sql_query(text(pragma_query), self.engine)
                    
                    table_info = f"Table: {table_name}\n"
                    table_info += "Columns:\n"
                    
                    for _, row in columns.iterrows():
                        col_name = row['name']
                        col_type = row['type']
                        is_pk = "PRIMARY KEY" if row['pk'] == 1 else ""
                        
                        table_info += f"  - {col_name} ({col_type}) {is_pk}\n"
                    
                    # Add sample data count
                    count_query = f"SELECT COUNT(*) as count FROM '{table_name}';"
                    count = pd.read_sql_query(text(count_query), self.engine).iloc[0]['count']
                    table_info += f"Total rows: {count}\n"
                    
                    schema_info.append(table_info)
            
            elif self.db_type in ["mysql", "postgresql"]:
                # Get list of tables (implementation varies by DB type)
                if self.db_type == "mysql":
                    tables_query = f"SHOW TABLES FROM {self.db_name};"
                else:  # postgresql
                    tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
                
                tables = pd.read_sql_query(text(tables_query), self.engine)
                table_col = tables.columns[0]
                
                for table_name in tables[table_col]:
                    if self.db_type == "mysql":
                        columns_query = f"DESCRIBE {table_name};"
                        columns = pd.read_sql_query(text(columns_query), self.engine)
                        
                        table_info = f"Table: {table_name}\n"
                        table_info += "Columns:\n"
                        
                        for _, row in columns.iterrows():
                            col_name = row['Field']
                            col_type = row['Type']
                            key = row['Key']
                            is_pk = "PRIMARY KEY" if key == "PRI" else ""
                            
                            table_info += f"  - {col_name} ({col_type}) {is_pk}\n"
                    
                    else:  # postgresql
                        columns_query = f"""
                            SELECT column_name, data_type, 
                                   CASE WHEN EXISTS (
                                       SELECT 1 FROM information_schema.table_constraints tc
                                       JOIN information_schema.key_column_usage kcu 
                                         ON tc.constraint_name = kcu.constraint_name
                                       WHERE tc.constraint_type = 'PRIMARY KEY' 
                                         AND tc.table_name = '{table_name}'
                                         AND kcu.column_name = columns.column_name
                                   ) THEN 'PRIMARY KEY' ELSE '' END as key
                            FROM information_schema.columns
                            WHERE table_name = '{table_name}';
                        """
                        columns = pd.read_sql_query(text(columns_query), self.engine)
                        
                        table_info = f"Table: {table_name}\n"
                        table_info += "Columns:\n"
                        
                        for _, row in columns.iterrows():
                            col_name = row['column_name']
                            col_type = row['data_type']
                            is_pk = row['key']
                            
                            table_info += f"  - {col_name} ({col_type}) {is_pk}\n"
                    
                    # Add sample data count
                    count_query = f"SELECT COUNT(*) as count FROM {table_name};"
                    count = pd.read_sql_query(text(count_query), self.engine).iloc[0]['count']
                    table_info += f"Total rows: {count}\n"
                    
                    schema_info.append(table_info)
            
            return "\n".join(schema_info)
            
        except Exception as e:
            return f"Error fetching schema information: {str(e)}"
    
    def test_connection(self):
        """Test database connection."""
        try:
            if self.engine is None:
                return False, "Database engine not created."
            
            # Try a simple query to test connection
            if self.db_type == "sqlite":
                test_query = "SELECT sqlite_version();"
            elif self.db_type == "mysql":
                test_query = "SELECT VERSION();"
            else:  # postgresql
                test_query = "SELECT version();"
            
            pd.read_sql_query(text(test_query), self.engine)
            return True, "Connection successful."
            
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def close(self):
        """Close database connection."""
        if self.engine is not None:
            self.engine.dispose()