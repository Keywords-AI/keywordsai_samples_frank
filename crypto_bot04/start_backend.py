#!/usr/bin/env python3
"""
Startup script for the AI Crypto Trading Bot backend.
Run this from the root directory to start the FastAPI server.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the root directory
    root_dir = Path(__file__).parent
    backend_dir = root_dir / "backend"
    src_dir = backend_dir / "src"
    
    # Check if backend directory exists
    if not backend_dir.exists():
        print("❌ Backend directory not found!")
        print("Please make sure you're running this from the project root directory.")
        sys.exit(1)
    
    # Check if virtual environment exists
    venv_dir = backend_dir / "venv"
    if not venv_dir.exists():
        print("❌ Virtual environment not found!")
        print("Please create a virtual environment first:")
        print("  cd backend")
        print("  python -m venv venv")
        print("  venv\\Scripts\\activate  # Windows")
        print("  source venv/bin/activate  # macOS/Linux")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    # Check if .env file exists
    env_file = backend_dir / ".env"
    if not env_file.exists():
        print("⚠️  .env file not found!")
        print("Creating a template .env file...")
        
        env_template = """# OpenAI API Key (required for LLM strategy)
OPENAI_API_KEY=your_openai_api_key_here

# Keywords AI API Key (for logging)
KEYWORDSAI_API_KEY=your_keywordsai_api_key_here

# Coinbase API Credentials (for live trading)
COINBASE_SANDBOX_API_KEY=your_coinbase_api_key
COINBASE_SANDBOX_API_SECRET=your_coinbase_api_secret
"""
        with open(env_file, 'w') as f:
            f.write(env_template)
        
        print(f"✅ Created {env_file}")
        print("Please edit the .env file with your actual API keys before starting the server.")
        return
    
    # Prepare the command
    if os.name == 'nt':  # Windows
        python_exe = venv_dir / "Scripts" / "python.exe"
        activate_script = venv_dir / "Scripts" / "activate.bat"
    else:  # macOS/Linux
        python_exe = venv_dir / "bin" / "python"
        activate_script = venv_dir / "bin" / "activate"
    
    # Check if Python executable exists in venv
    if not python_exe.exists():
        print("❌ Python not found in virtual environment!")
        print("Please reinstall the virtual environment.")
        sys.exit(1)
    
    print("🚀 Starting AI Crypto Trading Bot Backend...")
    print(f"📁 Working directory: {src_dir}")
    print(f"🐍 Python: {python_exe}")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📊 API docs: http://localhost:8000/docs")
    print("🎨 Frontend: Open frontend/index.html in your browser")
    print("\n" + "="*60)
    
    try:
        # Change to src directory and run uvicorn
        os.chdir(src_dir)
        
        # Run the server
        cmd = [
            str(python_exe),
            "-m", "uvicorn",
            "api.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ]
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to start server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 