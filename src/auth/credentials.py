"""
Credential management module for authentication.
"""

import json
import streamlit as st
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import secrets
import time


def load_credentials(credentials_path: Optional[Path] = None) -> Dict:
    """
    Load user credentials from JSON file.

    Args:
        credentials_path: Path to credentials file. If None, uses default location.

    Returns:
        Dictionary containing user credentials.
    """
    if credentials_path is None:
        # Get project root (2 levels up from src/auth/)
        project_root = Path(__file__).parent.parent.parent
        credentials_path = project_root / "credentials.json"

    if credentials_path.exists():
        try:
            with open(credentials_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading credentials: {e}")
            return {"users": []}

    return {"users": []}


def check_credentials(username: str, password: str) -> bool:
    """
    Verify username and password against stored credentials.

    Args:
        username: Username to verify
        password: Password to verify

    Returns:
        True if credentials are valid, False otherwise.
    """
    if not username or not password:
        return False

    credentials = load_credentials()

    for user in credentials.get("users", []):
        if user.get("username") == username and user.get("password") == password:
            return True

    return False


def generate_token(username: str) -> str:
    """
    Generate a secure token for the user session.

    Args:
        username: Username to include in token

    Returns:
        Secure token string
    """
    # Create a simple token (in production, use JWT or similar)
    random_part = secrets.token_hex(16)
    timestamp = str(int(time.time()))
    token_string = f"{username}:{random_part}:{timestamp}"
    return hashlib.sha256(token_string.encode()).hexdigest()


def save_auth_token(username: str, token: str):
    """
    Save authentication token to a local file for persistence.

    Args:
        username: Username to save
        token: Token to save
    """
    auth_file = Path.home() / ".wbr_auth"
    auth_data = {
        "username": username,
        "token": token,
        "timestamp": time.time()
    }
    try:
        with open(auth_file, 'w') as f:
            json.dump(auth_data, f)
    except Exception as e:
        print(f"Error saving auth: {e}")


def load_auth_token() -> Optional[Dict]:
    """
    Load authentication token from local file.

    Returns:
        Dict with username and token if valid, None otherwise
    """
    auth_file = Path.home() / ".wbr_auth"
    if not auth_file.exists():
        return None

    try:
        with open(auth_file, 'r') as f:
            auth_data = json.load(f)

        # Check if token is still valid (24 hours)
        if time.time() - auth_data.get("timestamp", 0) > 86400:
            auth_file.unlink()  # Delete expired token
            return None

        return auth_data
    except Exception as e:
        print(f"Error loading auth: {e}")
        return None


def clear_auth_token():
    """Clear the saved authentication token."""
    auth_file = Path.home() / ".wbr_auth"
    if auth_file.exists():
        try:
            auth_file.unlink()
        except Exception as e:
            print(f"Error clearing auth: {e}")


def logout():
    """
    Clear authentication from session state and local storage, then trigger app rerun.
    """
    # Clear authentication-related session state
    keys_to_clear = ["authenticated", "username", "auth_token"]

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    # Clear saved token
    clear_auth_token()

    # Trigger app rerun to redirect to login page
    st.rerun()