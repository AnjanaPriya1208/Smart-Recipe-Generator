import psycopg2

def get_db_connection():
    try:
        connection = psycopg2.connect(
            dbname="SmartRecipeDB",  # Use your actual database name
            user="postgres",      # Your PostgreSQL username
            password="root",      # Your PostgreSQL password
            host="localhost",     # Host
            port="5432"           # Default PostgreSQL port
        )
        print("Database connection established successfully.")
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        return None
    # Function to return GPT API key
def get_gpt_key():
    return "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"
if __name__ == "_main_":
    get_db_connection()