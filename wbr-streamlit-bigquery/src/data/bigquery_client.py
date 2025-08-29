from google.cloud import bigquery
import os


class BigQueryClient:
    def __init__(self):
        # Autentica sob demanda para facilitar testes sem credenciais
        self.client = None

    def authenticate(self):
        """Authenticate to Google Cloud using service account credentials (lazy)."""
        if self.client is not None:
            return self.client
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            raise ValueError(
                "Google application credentials not found. Set the GOOGLE_APPLICATION_CREDENTIALS environment variable."
            )
        self.client = bigquery.Client.from_service_account_json(credentials_path)
        return self.client

    def run_query(self, query: str):
        """Run a SQL query against BigQuery and return a pandas DataFrame."""
        client = self.authenticate()
        query_job = client.query(query)
        results = query_job.result()  # Wait for the job to complete.
        return results.to_dataframe()

    def fetch_wbr_data(self, *, project_id: str | None = None, dataset: str | None = None, table: str | None = None):
        """Fetch WBR data using SQL at src/data/queries/wbr.sql and env/template variables.

        Uses BIGQUERY_PROJECT_ID, BIGQUERY_DATASET, BIGQUERY_TABLE if args not provided.
        Replaces backticked `your_project.your_dataset.your_table` in the SQL.
        """
        sql_path = os.path.join(os.path.dirname(__file__), 'queries', 'wbr.sql')
        with open(sql_path, 'r') as file:
            query = file.read()

        project_id = project_id or os.getenv('BIGQUERY_PROJECT_ID') or os.getenv('BQ_PROJECT_ID')
        dataset = dataset or os.getenv('BIGQUERY_DATASET') or os.getenv('BQ_DATASET_ID')
        table = table or os.getenv('BIGQUERY_TABLE') or os.getenv('BQ_TABLE_ID')

        if not all([project_id, dataset, table]):
            raise ValueError(
                "Missing BigQuery identifiers. Set BIGQUERY_PROJECT_ID, BIGQUERY_DATASET and BIGQUERY_TABLE in .env, "
                "or pass them to fetch_wbr_data()."
            )

        placeholder = "`your_project.your_dataset.your_table`"
        qualified = f"`{project_id}.{dataset}.{table}`"
        query = query.replace(placeholder, qualified)

        return self.run_query(query)