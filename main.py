import os
from dotenv import load_dotenv
from src.factory.create_app import create_app

load_dotenv()

if __name__ == "__main__":
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
