import requests
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Credentials are stored in the user's home directory
CREDENTIALS_DIR = Path.home() / ".venturalitica"
CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"

def load_credentials() -> Optional[Dict[str, Any]]:
    """Loads stored credentials from ~/.venturalitica/credentials.json."""
    if not CREDENTIALS_FILE.exists():
        return None
    try:
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    except:
        return None

def save_credentials(api_key: Optional[str] = None, 
                     session_token: Optional[str] = None,
                     ai_system_name: str = "Unknown", 
                     expires_at: Optional[str] = None) -> None:
    """Saves credentials (API key or session token) to ~/.venturalitica/credentials.json."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "ai_system_name": ai_system_name,
        "expires_at": expires_at
    }
    if api_key:
        data["api_key"] = api_key
    if session_token:
        data["session_token"] = session_token
        
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(data, f, indent=2)

class VenturaliticaClient:
    def __init__(self, base_url: str = "http://localhost:3000", 
                 api_key: Optional[str] = None,
                 session_token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        
        # Priority: explicit > env var > stored credentials
        self.api_key = api_key
        self.session_token = session_token
        
        if not self.api_key and not self.session_token:
            if os.getenv("VENTURALITICA_API_KEY"):
                self.api_key = os.getenv("VENTURALITICA_API_KEY")
            else:
                creds = load_credentials()
                if creds:
                    self.api_key = creds.get("api_key")
                    self.session_token = creds.get("session_token")

        self.headers = {
            "Content-Type": "application/json",
        }
        
        # Use session token if available, otherwise API key
        token = self.session_token or self.api_key
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def is_authenticated(self) -> bool:
        """Checks if valid credentials are available."""
        return self.api_key is not None or self.session_token is not None


    def pull_config(self, format: Optional[str] = None) -> Dict[str, Any]:
        """Fetches governance configuration for the authenticated AI System."""
        if not self.is_authenticated():
            raise Exception("Not authenticated. Run 'venturalitica login' first.")
        url = f"{self.base_url}/api/pull"
        params = {}
        if format:
            params['format'] = format
            
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def push_results(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Pushes evaluation results to the SaaS."""
        if not self.is_authenticated():
            raise Exception("Not authenticated. Run 'venturalitica login' first.")
        url = f"{self.base_url}/api/push"
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
        
    def register_key(self, ai_system_id: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Registers a new API key for an AI System. (Legacy)"""
        url = f"{self.base_url}/api/cli-auth"
        response = requests.post(url, headers={"Content-Type": "application/json"}, json={
            "aiSystemId": ai_system_id,
            "name": name or "CLI Key"
        })
        response.raise_for_status()
        return response.json()

    def initiate_device_flow(self) -> Dict[str, Any]:
        """Initiates the OAuth 2.0 Device Flow."""
        url = f"{self.base_url}/api/auth/device/code"
        response = requests.post(url, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        return response.json()

    def poll_device_token(self, device_code: str) -> Optional[Dict[str, Any]]:
        """Polls for the session token using the device code."""
        url = f"{self.base_url}/api/auth/device/token"
        response = requests.post(url, json={"deviceCode": device_code})
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400: # Ongoing polling
            error = response.json().get('error')
            if error in ['authorization_pending', 'slow_down']:
                return None
            raise Exception(f"OAuth Error: {error}")
        else:
            response.raise_for_status()
            return None

