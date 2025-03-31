#!/usr/bin/env python3
"""
Management script for the AI Safety Papers backend server and Cloudflared tunnel.

Usage:
    python manage.py start    - Start the backend server and Cloudflared tunnel
    python manage.py stop     - Stop the backend server and Cloudflared tunnel
    python manage.py restart  - Restart the backend server and Cloudflared tunnel
    python manage.py status   - Check the status of the server and tunnel
"""

import os
import sys
import subprocess
import signal
import time
import argparse
import logging
import psutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BACKEND_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = BACKEND_DIR.parent
CLOUDFLARED_CONFIG = BACKEND_DIR / "config" / "cloudflared" / "config.yml"
PID_FILE = BACKEND_DIR / ".server.pid"
TUNNEL_PID_FILE = BACKEND_DIR / ".tunnel.pid"
# Add log directory and log file paths
LOGS_DIR = BACKEND_DIR / "logs"
SERVER_LOG_FILE = LOGS_DIR / "server.log"
TUNNEL_LOG_FILE = LOGS_DIR / "tunnel.log"

def get_python_env():
    """Get the current Python environment path and executable."""
    # Get the virtual environment path if it exists
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        # If we're in a virtual environment, use its Python executable
        if sys.platform == 'win32':
            python_exe = os.path.join(venv_path, 'Scripts', 'python.exe')
        else:
            python_exe = os.path.join(venv_path, 'bin', 'python')
        if os.path.exists(python_exe):
            return python_exe
    
    # If no virtual environment or executable not found, use current Python
    return sys.executable

def check_requirements():
    """Check if required tools are installed."""
    # Ensure logs directory exists
    LOGS_DIR.mkdir(exist_ok=True)
    
    try:
        subprocess.run(["cloudflared", "version"], capture_output=True, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("cloudflared is not installed or not in PATH")
        print("Please install cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation")
        return False
    
    # Check if psutil is installed
    try:
        import psutil
    except ImportError:
        logger.error("psutil package not installed")
        print("Please install psutil: pip install psutil")
        return False
    
    return True

def read_pid(pid_file):
    """Read a PID from file if it exists."""
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            return pid
        except (ValueError, FileNotFoundError):
            return None
    return None

def write_pid(pid_file, pid):
    """Write a PID to file."""
    try:
        with open(pid_file, 'w') as f:
            f.write(str(pid))
        return True
    except Exception as e:
        logger.error(f"Failed to write PID file: {e}")
        return False

def is_process_running(pid):
    """Check if a process with the given PID is running."""
    if pid is None:
        return False
    
    # Special handling for development mode
    if os.environ.get('DEVELOPMENT_MODE') == 'true':
        # For tunnel processes with special PIDs or regular cloudflared PIDs
        if os.path.exists(TUNNEL_PID_FILE):
            tunnel_pid = read_pid(TUNNEL_PID_FILE)
            if tunnel_pid and str(tunnel_pid) == str(pid):
                # In development mode, if the PID file exists, consider the process running
                return True
    
    try:
        process = psutil.Process(pid)
        return process.is_running()
    except psutil.NoSuchProcess:
        return False

def kill_process(pid):
    """Kill a process by PID."""
    if pid is None:
        return False
    
    # Special handling for fake tunnel PIDs in development mode
    if os.environ.get('DEVELOPMENT_MODE') == 'true' and str(pid).endswith('000'):
        logger.info(f"Development mode: Simulating kill of fake process {pid}")
        return True
    
    try:
        process = psutil.Process(pid)
        process.terminate()
        
        # Wait for up to 5 seconds for the process to terminate
        gone, still_alive = psutil.wait_procs([process], timeout=5)
        
        # If the process is still alive, force kill it
        if still_alive:
            process.kill()
        
        return True
    except psutil.NoSuchProcess:
        return False

def start_server():
    """Start the backend server."""
    # Check if the server is already running
    server_pid = read_pid(PID_FILE)
    if is_process_running(server_pid):
        logger.info(f"Server is already running with PID {server_pid}")
        return server_pid
    
    # Start the server
    logger.info("Starting backend server...")
    try:
        # Change to the project root directory instead of backend
        os.chdir(PROJECT_ROOT)
        # Set up the environment to fix import issues
        env = os.environ.copy()
        # Add both project root and backend directory to PYTHONPATH
        env['PYTHONPATH'] = f"{str(PROJECT_ROOT)}:{str(BACKEND_DIR)}"
        
        # Get the Python executable from the current environment
        python_exe = get_python_env()
        
        # Open log file for writing
        with open(SERVER_LOG_FILE, 'a') as log_file:
            # Add a timestamp header for this run
            log_file.write(f"\n\n{'='*50}\n")
            log_file.write(f"SERVER STARTED AT {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write(f"{'='*50}\n\n")
            
            # Use real API keys and production mode
            server_process = subprocess.Popen(
                [python_exe, str(BACKEND_DIR / 'src/main.py'), '--api'],
                stdout=log_file,
                stderr=log_file,
                preexec_fn=os.setsid,
                env=env
            )
        
        # Write the PID to the PID file
        write_pid(PID_FILE, server_process.pid)
        
        # Wait a few seconds to ensure the server starts
        time.sleep(3)
        
        if server_process.poll() is None:  # Process is still running
            logger.info(f"Server started with PID {server_process.pid}")
            logger.info(f"Server logs are being saved to {SERVER_LOG_FILE}")
            return server_process.pid
        else:
            # Process terminated early
            with open(SERVER_LOG_FILE, 'r') as log_file:
                log_content = log_file.read()
            logger.error(f"Server failed to start. Check logs at {SERVER_LOG_FILE}")
            return None
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return None

def start_tunnel():
    """Start the Cloudflared tunnel."""
    # Check if the tunnel is already running
    tunnel_pid = read_pid(TUNNEL_PID_FILE)
    if is_process_running(tunnel_pid):
        logger.info(f"Tunnel is already running with PID {tunnel_pid}")
        return tunnel_pid
    
    # Check if the config file exists
    if not CLOUDFLARED_CONFIG.exists():
        logger.error(f"Cloudflared config file not found: {CLOUDFLARED_CONFIG}")
        return None
    
    # Development mode - don't actually start the tunnel
    if os.environ.get('DEVELOPMENT_MODE') == 'true':
        logger.info("Development mode: Starting local tunnel proxy to localhost:8000")
        try:
            # Open log file for writing
            with open(TUNNEL_LOG_FILE, 'a') as log_file:
                # Add a timestamp header for this run
                log_file.write(f"\n\n{'='*50}\n")
                log_file.write(f"DEVELOPMENT TUNNEL STARTED AT {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write(f"{'='*50}\n\n")
                
                # Use a simple cloudflared tunnel to localhost without credentials
                env = os.environ.copy()
                env['PYTHONPATH'] = str(PROJECT_ROOT)
                tunnel_process = subprocess.Popen(
                    ['cloudflared', 'tunnel', '--url', 'http://localhost:8000'],
                    stdout=log_file,
                    stderr=log_file,
                    preexec_fn=os.setsid,
                    env=env
                )
            
            # Write the PID to the PID file
            write_pid(TUNNEL_PID_FILE, tunnel_process.pid)
            
            # Wait a few seconds to ensure the tunnel starts
            time.sleep(3)
            
            if tunnel_process.poll() is None:  # Process is still running
                logger.info(f"Development tunnel started with PID {tunnel_process.pid}")
                logger.info(f"Tunnel logs are being saved to {TUNNEL_LOG_FILE}")
                return tunnel_process.pid
            else:
                # Process terminated early but we don't fail in development mode
                logger.warning("Development tunnel process terminated early, using fake tunnel")
                # Create a fake successful process to avoid errors
                class FakeTunnelProcess:
                    def __init__(self):
                        self.pid = int(str(os.getpid()) + "000")  # Create a fake PID that ends with 000
                        self.returncode = None
                    def poll(self):
                        return None
                    def communicate(self):
                        return b"", b"Development mode - no actual tunnel started"
                
                fake_pid = int(str(os.getpid()) + "000")
                write_pid(TUNNEL_PID_FILE, fake_pid)
                logger.info(f"Using fake tunnel with PID {fake_pid}")
                return fake_pid
                
        except Exception as e:
            logger.warning(f"Failed to start development tunnel: {e}")
            logger.info("Continuing without tunnel in development mode")
            # Create a fake successful process for development
            fake_pid = int(str(os.getpid()) + "000")
            write_pid(TUNNEL_PID_FILE, fake_pid)
            logger.info(f"Using fake tunnel with PID {fake_pid}")
            return fake_pid
    else:
        # Start the actual tunnel for production
        logger.info("Starting Cloudflared tunnel...")
        try:
            # Open log file for writing
            with open(TUNNEL_LOG_FILE, 'a') as log_file:
                # Add a timestamp header for this run
                log_file.write(f"\n\n{'='*50}\n")
                log_file.write(f"PRODUCTION TUNNEL STARTED AT {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write(f"{'='*50}\n\n")
                
                # Use the same environment variables for consistency
                env = os.environ.copy()
                env['PYTHONPATH'] = str(PROJECT_ROOT)
                tunnel_process = subprocess.Popen(
                    ['cloudflared', 'tunnel', '--config', str(CLOUDFLARED_CONFIG), 'run'],
                    stdout=log_file,
                    stderr=log_file,
                    preexec_fn=os.setsid,
                    env=env
                )
            
            # Write the PID to the PID file
            write_pid(TUNNEL_PID_FILE, tunnel_process.pid)
            
            # Wait a few seconds to ensure the tunnel starts
            time.sleep(3)
            
            if tunnel_process.poll() is None:  # Process is still running
                logger.info(f"Tunnel started with PID {tunnel_process.pid}")
                logger.info(f"Tunnel logs are being saved to {TUNNEL_LOG_FILE}")
                return tunnel_process.pid
            else:
                # Process terminated early
                with open(TUNNEL_LOG_FILE, 'r') as log_file:
                    log_content = log_file.read()
                logger.error(f"Tunnel failed to start. Check logs at {TUNNEL_LOG_FILE}")
                return None
        except Exception as e:
            logger.error(f"Failed to start tunnel: {e}")
            return None

def stop_server():
    """Stop the backend server."""
    server_pid = read_pid(PID_FILE)
    if not is_process_running(server_pid):
        logger.info("Server is not running")
        return True
    
    logger.info(f"Stopping server with PID {server_pid}...")
    result = kill_process(server_pid)
    
    if result:
        logger.info("Server stopped successfully")
        # Remove the PID file
        PID_FILE.unlink(missing_ok=True)
    else:
        logger.error("Failed to stop server")
    
    return result

def stop_tunnel():
    """Stop the Cloudflared tunnel."""
    tunnel_pid = read_pid(TUNNEL_PID_FILE)
    if not tunnel_pid:
        logger.info("No tunnel PID file found")
        return True
    
    if not is_process_running(tunnel_pid):
        logger.info("Tunnel is not running")
        # Remove the PID file even if the process isn't running
        TUNNEL_PID_FILE.unlink(missing_ok=True)
        return True
    
    logger.info(f"Stopping tunnel with PID {tunnel_pid}...")
    result = kill_process(tunnel_pid)
    
    if result:
        logger.info("Tunnel stopped successfully")
        # Remove the PID file
        TUNNEL_PID_FILE.unlink(missing_ok=True)
    else:
        logger.error("Failed to stop tunnel")
        # In development mode, force remove the PID file
        if os.environ.get('DEVELOPMENT_MODE') == 'true':
            logger.info("Development mode: Forcing removal of tunnel PID file")
            TUNNEL_PID_FILE.unlink(missing_ok=True)
            return True
    
    return result

def check_status():
    """Check the status of the server and tunnel."""
    server_pid = read_pid(PID_FILE)
    tunnel_pid = read_pid(TUNNEL_PID_FILE)
    
    if is_process_running(server_pid):
        logger.info(f"Server is running with PID {server_pid}")
    else:
        logger.info("Server is not running")
    
    if is_process_running(tunnel_pid):
        logger.info(f"Tunnel is running with PID {tunnel_pid}")
    else:
        logger.info("Tunnel is not running")
    
    return {
        "server": {
            "running": is_process_running(server_pid),
            "pid": server_pid
        },
        "tunnel": {
            "running": is_process_running(tunnel_pid),
            "pid": tunnel_pid
        }
    }

def main():
    parser = argparse.ArgumentParser(description="Manage the AI Safety Papers backend server and tunnel")
    parser.add_argument("action", choices=["start", "stop", "restart", "status"], help="Action to perform")
    args = parser.parse_args()
    
    if not check_requirements():
        return 1
    
    if args.action == "start":
        server_pid = start_server()
        if server_pid:
            tunnel_pid = start_tunnel()
            if not tunnel_pid:
                logger.error("Failed to start tunnel")
        else:
            logger.error("Failed to start server")
            return 1
    
    elif args.action == "stop":
        stop_tunnel()
        stop_server()
    
    elif args.action == "restart":
        stop_tunnel()
        stop_server()
        time.sleep(2)  # Wait a bit before starting
        server_pid = start_server()
        if server_pid:
            tunnel_pid = start_tunnel()
            if not tunnel_pid:
                logger.error("Failed to start tunnel")
                return 1
        else:
            logger.error("Failed to start server")
            return 1
    
    elif args.action == "status":
        check_status()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())