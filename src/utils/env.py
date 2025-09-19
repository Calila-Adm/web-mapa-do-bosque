import os
from dotenv import load_dotenv

def load_environment_variables(base_dir: str | None = None):
    """Load environment variables from .env and .secrets/.env
    - When base_dir is provided, load in this order:
      1) base_dir/.env
      2) base_dir/.secrets/.env (override=True)
    - Otherwise, use CWD and also try ./.secrets/.env
    """
    if base_dir:
        env_path = os.path.join(base_dir, ".env")
        secrets_env_path = os.path.join(base_dir, ".secrets", ".env")

        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
        if os.path.exists(secrets_env_path):
            # Ensure secrets override general .env values when both are defined
            load_dotenv(dotenv_path=secrets_env_path, override=True)
        return

    # Fallback: load from CWD
    load_dotenv()
    secrets_env_path = os.path.join(os.getcwd(), ".secrets", ".env")
    if os.path.exists(secrets_env_path):
        load_dotenv(dotenv_path=secrets_env_path, override=True)

def get_env_variable(var_name):
    """Get the environment variable or raise an exception."""
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Missing environment variable: {var_name}")
    return value

# Optional: don't auto-load here to allow callers to specify base_dir explicitly