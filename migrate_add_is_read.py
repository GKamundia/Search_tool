import os
import sys
from dotenv import load_dotenv
from flask import Flask
from src.database import init_db
from sqlalchemy.sql import text

load_dotenv()

# Create a minimal Flask app just for the database connection
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret')
db = init_db(app)

def add_is_read_column():
    with app.app_context():
        try:
            # Check if the column exists
            with db.engine.connect() as conn:
                # Try to add the column, if it fails it might already exist
                try:
                    conn.execute(text("ALTER TABLE search_results ADD COLUMN is_read BOOLEAN DEFAULT 0"))
                    conn.commit()
                    print("✅ Successfully added is_read column to search_results table")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print("Column is_read already exists, no changes needed")
                    else:
                        raise
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
        return True

if __name__ == "__main__":
    success = add_is_read_column()
    sys.exit(0 if success else 1)