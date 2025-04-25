# AI SQL Agent with Streamlit UI

This application allows users to query databases using natural language. It converts English questions into SQL queries using an AI language model, executes them on a connected database, and displays the results in a user-friendly Streamlit interface.

## 🌟 Features

- 💬 **Natural Language Queries**: Convert plain English questions into SQL using AI language models
- 🔄 **Multi-Database Support**: Connect to SQLite, MySQL, and PostgreSQL databases
- 📊 **Interactive Results**: View query results in an interactive data table
- 📝 **Query History**: Save and reuse previous queries
- 📤 **Export Functionality**: Download query results as CSV files
- 🧩 **Sample Database**: Built-in sample database for demo purposes
- 🛠️ **Editable SQL**: Review and modify generated SQL before execution

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- pip (Python package manager)

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ai-sql-agent.git
   cd ai-sql-agent
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the project root with the following variables:
   ```
   GOOGLE_API_KEY=your_google_gemini_api_key
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=your_database
   DB_USER=your_username
   DB_PASSWORD=your_password
   ```

### Running the Application

Start the Streamlit app:
```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501` in your web browser.

## 🔧 Usage

### Connecting to a Database

1. **SQLite**:
   - Upload your own SQLite database file (.db, .sqlite, .sqlite3)
   - Or use the built-in sample database by checking "Use Sample Database"

2. **MySQL/PostgreSQL**:
   - Enter your connection details in the sidebar
   - Click "Connect" to establish a connection

### Querying Your Data

1. Type a natural language question in the text area (e.g., "What are the total sales by category?")
2. Click "Generate SQL" to convert your question to SQL
3. Review the generated SQL query (you can edit it if needed)
4. Click "Run Query" to execute and see the results
5. Download results as CSV using the "Download Results" button

### Example Queries

- "Show me the first 5 rows from each table"
- "What are the total sales by category?"
- "Who are our top 3 customers by purchase amount?"
- "Show me all orders placed in the last month"
- "How many products do we have in each category?"
- "What is the average price of products by category?"

## 📚 Project Structure

```
ai-sql-agent/
├── app.py                 # Main Streamlit application
├── db_connector.py        # Database connection handler
├── sql_generator.py       # AI-based SQL query generator
├── requirements.txt       # Python dependencies
├── sample_data/           # Sample database files
└── .env                   # Environment variables (not tracked in git)
```

## 💡 How It Works

1. **User Input**: The application takes a natural language question from the user.
2. **AI Processing**: The question is sent to an AI language model (Google Gemini) along with the database schema.
3. **SQL Generation**: The AI generates an appropriate SQL query based on the question and schema.
4. **Query Execution**: The generated SQL is executed against the connected database.
5. **Results Display**: Query results are shown in an interactive table format.

## 🛡️ Security Considerations

- API keys and database credentials are stored in environment variables
- SQL queries are executed in a controlled environment
- User-uploaded database files are handled securely in temporary storage

## 🧪 Sample Database

The built-in sample database includes the following tables:
- `customers`: Customer information
- `categories`: Product categories
- `products`: Product details
- `orders`: Order information
- `order_items`: Items within each order

This provides a realistic e-commerce dataset for testing and demonstration.

## 🔍 Troubleshooting

- **Connection Issues**: Ensure your database is running and accessible
- **SQL Generation Errors**: Try rephrasing your question to be more specific
- **Query Execution Errors**: Check the generated SQL for syntax errors

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📬 Contact

For support or questions, please create an issue on the project repository.

---

*Built with ❤️ using Python, Streamlit, and AI*
