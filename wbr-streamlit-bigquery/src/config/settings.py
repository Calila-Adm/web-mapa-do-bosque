import os

class Settings:
    def __init__(self):
        self.BIGQUERY_PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID")
        self.BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET")
        self.BIGQUERY_PRIVATE_KEY = os.getenv("BIGQUERY_PRIVATE_KEY")
        self.BIGQUERY_CLIENT_EMAIL = os.getenv("BIGQUERY_CLIENT_EMAIL")
        self.STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", 8501))
        self.STREAMLIT_SERVER_ADDRESS = os.getenv("STREAMLIT_SERVER_ADDRESS", "localhost")

    def validate(self):
        if not all([self.BIGQUERY_PROJECT_ID, self.BIGQUERY_DATASET, self.BIGQUERY_PRIVATE_KEY, self.BIGQUERY_CLIENT_EMAIL]):
            raise ValueError("Missing required environment variables for BigQuery settings.")

settings = Settings()