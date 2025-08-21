"""
Configuration file for Azure OpenAI API
Loads configuration from environment variables or uses safe defaults
"""

import os

# Azure OpenAI Configuration
# Load from environment variables first, then use safe defaults
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-resource-name.openai.azure.com/")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "your-api-key-here")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4-vision-preview")

# Complete endpoint URL for chat completions
AZURE_OPENAI_CHAT_ENDPOINT = f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions"

def get_azure_openai_config():
    """Get Azure OpenAI configuration"""
    return {
        "endpoint": AZURE_OPENAI_ENDPOINT,
        "api_key": AZURE_OPENAI_API_KEY,
        "api_version": AZURE_OPENAI_API_VERSION,
        "deployment_name": AZURE_OPENAI_DEPLOYMENT_NAME,
        "chat_endpoint": AZURE_OPENAI_CHAT_ENDPOINT
    }

def get_openai_key():
    """Get the OpenAI API key (for backward compatibility)"""
    return AZURE_OPENAI_API_KEY

def is_azure_openai():
    """Check if we're using Azure OpenAI"""
    return True

def test_api_key():
    """Test if the API key is configured properly"""
    key = get_openai_key()
    if not key:
        print("❌ No API key found")
        print("💡 Set AZURE_OPENAI_API_KEY environment variable or update config.py")
        return False
    
    if key == "your-api-key-here":
        print("❌ Default placeholder API key detected")
        return False
    
    if len(key) < 10:
        print("❌ Invalid API key format")
        return False
    
    print("✅ Azure OpenAI API key is configured")
    return True

def load_env_file(env_file_path=".env"):
    """
    Load environment variables from .env file if it exists
    This is a simple implementation - for production use python-dotenv
    """
    try:
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        os.environ[key] = value
            print(f"✅ Loaded environment variables from {env_file_path}")
        else:
            print(f"ℹ️ No {env_file_path} file found, using environment variables or defaults")
    except Exception as e:
        print(f"⚠️ Error loading {env_file_path}: {e}")

# Load .env file on import (if it exists)
load_env_file()

if __name__ == "__main__":
    print("🔧 Azure OpenAI Configuration Test")
    print("=" * 40)
    
    config = get_azure_openai_config()
    print(f"Endpoint: {config['endpoint']}")
    print(f"API Version: {config['api_version']}")
    print(f"Deployment: {config['deployment_name']}")
    print(f"API Key: {'*' * (len(config['api_key']) - 8) + config['api_key'][-8:] if len(config['api_key']) > 8 else 'Not set'}")
    print("=" * 40)
    
    test_api_key() 