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

    def fetch_wbr_data(self, *, project_id: str | None = None, dataset: str | None = None, table: str | None = None,
                       date_col: str | None = None, metric_col: str | None = None, shopping_col: str | None = None):
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

        # Normalize dataset if it includes project (e.g., "project.dataset")
        if dataset and '.' in dataset:
            parts = dataset.split('.')
            if len(parts) == 2:
                proj_part, ds_part = parts
                # If project_id wasn't given explicitly, use from dataset
                if not project_id:
                    project_id = proj_part
                dataset = ds_part

        if not all([project_id, dataset, table]):
            raise ValueError(
                "Missing BigQuery identifiers. Set BIGQUERY_PROJECT_ID, BIGQUERY_DATASET and BIGQUERY_TABLE in .env, "
                "or pass them to fetch_wbr_data()."
            )

        placeholder = "`your_project.your_dataset.your_table`"

        # Normalize table to fully-qualified
        if table.count('.') == 0:
            qualified = f"`{project_id}.{dataset}.{table}`"
        elif table.count('.') == 1:
            ds, tbl = table.split('.')
            qualified = f"`{project_id}.{ds}.{tbl}`"
        else:
            qualified = table.strip()
            if not qualified.startswith('`'):
                qualified = f"`{qualified}`"

        # Replace placeholders for columns (default names if not provided)
        date_col = date_col or os.getenv('WBR_DATE_COL') or 'date'
        metric_col = metric_col or os.getenv('WBR_METRIC_COL') or 'metric_value'
        shopping_col = shopping_col or os.getenv('WBR_SHOPPING_COL') or 'NULL'

        query = query.replace(placeholder, qualified)
        query = query.replace('{{date_col}}', date_col)
        query = query.replace('{{metric_col}}', metric_col)
        query = query.replace('{{shopping_col}}', shopping_col)

        return self.run_query(query)

    def list_tables(self, *, project_id: str | None = None, dataset: str | None = None) -> list[str]:
        """List table IDs for a dataset.

        When project_id/dataset are omitted, read from env.
        """
        client = self.authenticate()
        project_id = project_id or os.getenv('BIGQUERY_PROJECT_ID') or os.getenv('BQ_PROJECT_ID')
        dataset = dataset or os.getenv('BIGQUERY_DATASET') or os.getenv('BQ_DATASET_ID')
        # Support dataset specified as "project.dataset"
        if dataset and '.' in dataset:
            parts = dataset.split('.')
            if len(parts) == 2:
                proj_part, ds_part = parts
                if not project_id:
                    project_id = proj_part
                dataset = ds_part
        if not all([project_id, dataset]):
            raise ValueError("Missing project_id or dataset to list tables.")
        dataset_ref = f"{project_id}.{dataset}"
        tables = client.list_tables(dataset_ref)
        return [t.table_id for t in tables]

    def infer_wbr_columns(self, *, project_id: str | None = None, dataset: str | None = None, table: str | None = None) -> tuple[str | None, str | None]:
        """Infer likely date and metric columns from a table schema.

        Returns (date_col, metric_col), any of which may be None if not inferred.
        """
        client = self.authenticate()
        project_id = project_id or os.getenv('BIGQUERY_PROJECT_ID') or os.getenv('BQ_PROJECT_ID')
        dataset = dataset or os.getenv('BIGQUERY_DATASET') or os.getenv('BQ_DATASET_ID')
        table = table or os.getenv('BIGQUERY_TABLE') or os.getenv('BQ_TABLE_ID')
        if not all([project_id, dataset, table]):
            return (None, None)

        # Normalize dataset
        if dataset and '.' in dataset:
            parts = dataset.split('.')
            if len(parts) == 2:
                proj_part, ds_part = parts
                if not project_id:
                    project_id = proj_part
                dataset = ds_part

        # Normalize table for get_table
        if table.count('.') == 0:
            table_fqid = f"{project_id}.{dataset}.{table}"
        elif table.count('.') == 1:
            ds, tbl = table.split('.')
            table_fqid = f"{project_id}.{ds}.{tbl}"
        else:
            table_fqid = table

        try:
            tbl = client.get_table(table_fqid)
        except Exception:
            return (None, None)

        date_candidates = {'date', 'data', 'dt', 'event_date', 'created_at', 'timestamp', 'datetime'}
        date_types = {'DATE', 'TIMESTAMP', 'DATETIME'}
        numeric_types = {'INTEGER', 'INT64', 'FLOAT', 'FLOAT64', 'NUMERIC', 'BIGNUMERIC', 'DECIMAL'}

        date_col = None
        metric_col = None

        # First, prefer explicit name matches for date-like fields with date types
        for field in tbl.schema:
            if field.field_type in date_types and field.name.lower() in date_candidates:
                date_col = field.name
                break
        # Fallback: any date-like type
        if not date_col:
            for field in tbl.schema:
                if field.field_type in date_types:
                    date_col = field.name
                    break

        # Metric: prefer fields with numeric type and common metric names
        metric_name_hints = {'metric', 'value', 'valor', 'quantidade', 'amount', 'total', 'count', 'visits', 'volume'}
        for field in tbl.schema:
            if field.field_type in numeric_types and (field.name.lower() in metric_name_hints or any(h in field.name.lower() for h in metric_name_hints)):
                metric_col = field.name
                break
        if not metric_col:
            for field in tbl.schema:
                if field.field_type in numeric_types:
                    metric_col = field.name
                    break

        return (date_col, metric_col)