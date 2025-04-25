import os
import streamlit as st
import pandas as pd
import sqlite3
import tempfile
import shutil
from dotenv import load_dotenv

from sql_genrator import generate_sql_query
from db_connector import DatabaseConnector

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI SQL Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar for database connection settings
st.sidebar.title("Database Connection")

# Database type selection
db_type = st.sidebar.selectbox(
    "Select Database Type",
    ["sqlite", "mysql", "postgresql"],
    index=0
)

# Connection settings based on database type
db_connector = None

if db_type == "sqlite":
    # File uploader for SQLite database
    uploaded_file = st.sidebar.file_uploader("Upload SQLite Database", type=["db", "sqlite", "sqlite3"])
    use_sample_db = st.sidebar.checkbox("Use Sample Database")
    
    if uploaded_file is not None:
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            db_path = tmp_file.name
        
        # Create database connector
        db_connector = DatabaseConnector(db_type="sqlite", db_path=db_path)
        
    elif use_sample_db:
        # Use the sample database included with the application
        sample_db_path = os.path.join("sample_data", "sample_db.sqlite")
        if os.path.exists(sample_db_path):
            db_connector = DatabaseConnector(db_type="sqlite", db_path=sample_db_path)
        else:
            st.sidebar.error("Sample database not found. Please create it first using the 'Create Sample Database' button below.")
            
            if st.sidebar.button("Create Sample Database"):
                # Create directory if it doesn't exist
                os.makedirs("sample_data", exist_ok=True)
                
                # Create sample database
                create_sample_database(sample_db_path)
                st.sidebar.success(f"Sample database created at {sample_db_path}")
                
                # Connect to the new sample database
                db_connector = DatabaseConnector(db_type="sqlite", db_path=sample_db_path)

else:
    # Settings for MySQL and PostgreSQL
    with st.sidebar.form("db_connection_form"):
        db_host = st.text_input("Host", os.getenv("DB_HOST", "localhost"))
        db_port = st.text_input("Port", os.getenv("DB_PORT", "3306" if db_type == "mysql" else "5432"))
        db_name = st.text_input("Database Name", os.getenv("DB_NAME", ""))
        db_user = st.text_input("Username", os.getenv("DB_USER", ""))
        db_password = st.text_input("Password", os.getenv("DB_PASSWORD", ""), type="password")
        
        connect_button = st.form_submit_button("Connect")
        
        if connect_button:
            db_connector = DatabaseConnector(
                db_type=db_type,
                db_host=db_host,
                db_port=db_port,
                db_name=db_name,
                db_user=db_user,
                db_password=db_password
            )

# Main application content
st.title("🧠 AI SQL Agent")
st.markdown("""
Ask questions about your database in plain English, and get SQL queries and results back!
""")

# Check connection status
connection_status = None

if db_connector is not None:
    connection_status, message = db_connector.test_connection()
    
    if connection_status:
        st.sidebar.success(message)
        
        # Show database schema
        with st.sidebar.expander("Database Schema"):
            schema_info = db_connector.get_schema_info()
            st.text(schema_info)
        
        # Show tables
        with st.sidebar.expander("Database Tables"):
            tables = db_connector.get_tables()
            st.dataframe(tables)
    else:
        st.sidebar.error(message)

# Query input section
with st.container():
    # Show examples
    with st.expander("Example Queries"):
        examples = [
            "Show me the first 5 rows from each table",
            "What are the total sales by category?",
            "Who are our top 3 customers by purchase amount?",
            "Show me all orders placed in the last month",
            "How many products do we have in each category?",
            "What is the average price of products by category?"
        ]
        for example in examples:
            if st.button(example):
                st.session_state.user_input = example
    
    # User input
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""
    
    user_input = st.text_area("Ask a question about your data", value=st.session_state.user_input, height=100)
    
    # History of queries
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    # Buttons row
    col1, col2, col3 = st.columns(3)
    
    generate_button = col1.button("Generate SQL", type="primary", disabled=not connection_status)
    run_button = col2.button("Run Query", disabled=not connection_status)
    clear_button = col3.button("Clear", type="secondary")
    
    if clear_button:
        st.session_state.user_input = ""
        st.session_state.sql_query = ""
        st.rerun()

# Generate SQL section
if generate_button and user_input and connection_status:
    with st.spinner("Generating SQL query..."):
        # Get schema info for context
        schema_info = db_connector.get_schema_info()
        
        # Generate SQL query
        sql_query = generate_sql_query(user_input, schema_info, db_type)
        
        # Store in session state
        st.session_state.sql_query = sql_query
        
        # Add to history
        st.session_state.query_history.append({
            "question": user_input,
            "sql": sql_query
        })

# Display SQL and results
if connection_status and 'sql_query' in st.session_state and st.session_state.sql_query:
    st.subheader("Generated SQL Query")
    
    # Text area for SQL with edit capability
    edited_sql = st.text_area("SQL Query (you can edit before running)", 
                              st.session_state.sql_query, 
                              height=150)
    
    # Update the SQL query in session state if edited
    if edited_sql != st.session_state.sql_query:
        st.session_state.sql_query = edited_sql
    
    # Run the query
    if run_button or 'auto_run' in st.session_state and st.session_state.auto_run:
        with st.spinner("Executing query..."):
            # Execute the query
            results = db_connector.execute_query(st.session_state.sql_query)
            
            st.subheader("Query Results")
            
            # Check if results is a DataFrame or error message
            if isinstance(results, pd.DataFrame):
                # Show results as DataFrame
                st.dataframe(results)
                
                # Download button for results
                st.download_button(
                    label="Download Results (CSV)",
                    data=results.to_csv(index=False).encode('utf-8'),
                    file_name="query_results.csv",
                    mime="text/csv"
                )
                
                
                
                # Basic visualization options if results are suitable
                if not results.empty and results.shape[1] >= 2:
                    with st.expander("Visualize Results"):
                        # Only offer visualization for numerical data
                        numeric_cols = results.select_dtypes(include=['number']).columns.tolist()
                        
                        if numeric_cols:
                            # Get all available columns
                            all_cols = results.columns.tolist()
                            
                            # Select columns for visualization if they exist
                            x_col = st.selectbox("X-axis", all_cols)
                            
                            # Only allow y-axis selection if there are numeric columns
                            if numeric_cols:
                                y_col = st.selectbox("Y-axis", numeric_cols)
                                
                                # Select chart type
                                chart_type = st.selectbox("Chart Type", ["Bar Chart", "Line Chart", "Scatter Plot"])
                                
                                # Make sure both selected columns exist before creating visualization
                                if x_col in all_cols and y_col in numeric_cols:
                                    try:
                                        # Create visualization
                                        if chart_type == "Bar Chart":
                                            st.bar_chart(results.set_index(x_col)[y_col])
                                        elif chart_type == "Line Chart":
                                            st.line_chart(results.set_index(x_col)[y_col])
                                        else:  # Scatter Plot
                                            st.scatter_chart(results.set_index(x_col)[y_col])
                                    except Exception as e:
                                        st.error(f"Visualization error: {str(e)}")
                                        st.info("Try selecting different columns or a different chart type.")
                        else:
                            st.info("No numeric columns available for visualization. Visualizations require at least one numeric column.")

# Query history section
with st.sidebar.expander("Query History"):
    if st.session_state.query_history:
        for i, query in enumerate(st.session_state.query_history):
            st.write(f"**Query {i+1}**: {query['question']}")
            if st.button(f"Load Query {i+1}", key=f"load_{i}"):
                st.session_state.user_input = query['question']
                st.session_state.sql_query = query['sql']
                st.session_state.auto_run = True
                st.rerun()
    else:
        st.write("No queries yet.")


# Settings
with st.sidebar.expander("Settings"):
    google_api_key = st.text_input(
        "Google Gemini API Key", 
        value=os.getenv("GOOGLE_API_KEY", ""),
        type="password",
        help="Enter your Google Gemini API key to enable SQL generation"
    )
    
    if google_api_key:
        os.environ["GOOGLE_API_KEY"] = google_api_key
# Function to create a sample SQLite database
def create_sample_database(db_path):
    """Create a sample SQLite database for demonstration purposes."""
    # Create connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT,
        registration_date DATE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE categories (
        category_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category_id INTEGER,
        price REAL NOT NULL,
        stock INTEGER NOT NULL,
        FOREIGN KEY (category_id) REFERENCES categories (category_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        order_date DATE,
        total_amount REAL,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE order_items (
        order_item_id INTEGER PRIMARY KEY,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (order_id),
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    )
    ''')
    
    # Insert sample data
    # Customers
    customers = [
        (1, "John Doe", "john@example.com", "2023-01-15"),
        (2, "Jane Smith", "jane@example.com", "2023-02-20"),
        (3, "Bob Johnson", "bob@example.com", "2023-03-10"),
        (4, "Alice Brown", "alice@example.com", "2023-04-05"),
        (5, "Charlie Wilson", "charlie@example.com", "2023-05-22")
    ]
    cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", customers)
    
    # Categories
    categories = [
        (1, "Electronics", "Electronic devices and accessories"),
        (2, "Clothing", "Apparel and fashion items"),
        (3, "Books", "Books and publications"),
        (4, "Home & Kitchen", "Home and kitchen products")
    ]
    cursor.executemany("INSERT INTO categories VALUES (?, ?, ?)", categories)
    
    # Products
    products = [
        (1, "Smartphone", 1, 799.99, 50),
        (2, "Laptop", 1, 1299.99, 30),
        (3, "T-shirt", 2, 19.99, 100),
        (4, "Jeans", 2, 49.99, 75),
        (5, "Novel", 3, 14.99, 200),
        (6, "Cookbook", 3, 24.99, 60),
        (7, "Blender", 4, 89.99, 40),
        (8, "Coffee Maker", 4, 69.99, 35),
        (9, "Headphones", 1, 149.99, 80),
        (10, "Tablet", 1, 399.99, 45)
    ]
    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?)", products)
    
    # Orders
    orders = [
        (1, 1, "2023-06-10", 849.98),
        (2, 2, "2023-06-15", 1349.98),
        (3, 3, "2023-06-20", 64.98),
        (4, 4, "2023-06-25", 114.98),
        (5, 5, "2023-06-30", 159.98),
        (6, 1, "2023-07-05", 399.99),
        (7, 2, "2023-07-10", 149.99),
        (8, 3, "2023-07-15", 89.99)
    ]
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", orders)
    
    # Order Items
    order_items = [
        (1, 1, 1, 1, 799.99),
        (2, 1, 3, 2, 19.99),
        (3, 2, 2, 1, 1299.99),
        (4, 2, 4, 1, 49.99),
        (5, 3, 5, 2, 14.99),
        (6, 3, 6, 1, 24.99),
        (7, 4, 7, 1, 89.99),
        (8, 4, 5, 1, 14.99),
        (9, 5, 9, 1, 149.99),
        (10, 6, 10, 1, 399.99),
        (11, 7, 9, 1, 149.99),
        (12, 8, 7, 1, 89.99)
    ]
    cursor.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?)", order_items)
    
    # Commit and close
    conn.commit()
    conn.close()

# Footer
st.markdown("""
---
### How to Use
1. Connect to your database using the sidebar options
2. Type your question in the text area
3. Click "Generate SQL" to create a query
4. Review the SQL and click "Run Query" to see results

For support, please create an issue on the project repository.
""")

# Cleanup on exit
def cleanup():
    # Close database connection
    if 'db_connector' in locals() and db_connector is not None:
        db_connector.close()
    
    # Remove temporary files
    if 'db_path' in locals() and uploaded_file is not None:
        try:
            os.unlink(db_path)
        except:
            pass

# Register cleanup function
import atexit
atexit.register(cleanup)