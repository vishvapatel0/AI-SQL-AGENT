import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Google Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

def generate_sql_query(prompt, schema_info, db_type="sqlite"):
    """
    Generate SQL query from natural language using Google's Gemini model.
    
    Args:
        prompt (str): Natural language query
        schema_info (str): Database schema information
        db_type (str): Type of database (sqlite, mysql, postgresql)
    
    Returns:
        str: Generated SQL query
    """
    
    try:
        # List available models (uncomment for debugging)
        # models = genai.list_models()
        # print("Available models:", [model.name for model in models])
        
        # Set up the model (using the correct model name)
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Define the prompt with database schema and query
        full_prompt = f"""You are an expert SQL query generator.
        Your task is to convert natural language questions into correct SQL queries for {db_type.upper()} databases.
        
        Database Schema Information:
        {schema_info}
        
        User Question: {prompt}
        
        Provide ONLY the SQL query without any additional text, explanation, or markdown formatting.
        The SQL query should be valid {db_type.upper()} syntax.
        """
        
        # Generate response
        response = model.generate_content(full_prompt)
        
        # Extract the SQL query from the response
        sql_query = response.text.strip()
        
        # Clean up the SQL query (remove any markdown formatting if present)
        if sql_query.startswith("```sql"):
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
        return sql_query
    
    except Exception as e:
        return f"Error generating SQL query: {str(e)}"


def get_table_schema(engine):
    """
    Extract schema information from database.
    
    Args:
        engine: SQLAlchemy engine
        
    Returns:
        str: Schema information in a readable format
    """
    try:
        import pandas as pd
        
        # Get a list of all tables
        query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables = pd.read_sql(query, engine)
        
        schema_info = []
        
        # For each table, get the column information
        for table_name in tables['name']:
            # Skip SQLite system tables
            if table_name.startswith('sqlite_'):
                continue
                
            # Get column info
            query = f"PRAGMA table_info('{table_name}');"
            columns = pd.read_sql(query, engine)
            
            table_schema = f"Table: {table_name}\n"
            table_schema += "Columns:\n"
            
            for _, row in columns.iterrows():
                col_name = row['name']
                col_type = row['type']
                is_pk = "PRIMARY KEY" if row['pk'] == 1 else ""
                
                table_schema += f"  - {col_name} ({col_type}) {is_pk}\n"
            
            schema_info.append(table_schema)
        
        return "\n".join(schema_info)
    
    except Exception as e:
        return f"Error extracting schema: {str(e)}"