import os
from dotenv import load_dotenv

def load_environment_variables(base_dir: str | None = None):
    """Load environment variables from a .env file.
    If base_dir is provided, load from base_dir/.env; otherwise, use CWD.
    """
    if base_dir:
        env_path = os.path.join(base_dir, ".env")
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
            return
    load_dotenv()

def get_env_variable(var_name):
    """Get the environment variable or raise an exception."""
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Missing environment variable: {var_name}")
    return value

# Optional: don't auto-load here to allow callers to specify base_dir explicitly