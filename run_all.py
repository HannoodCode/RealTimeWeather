import subprocess
import sys
import time
from datetime import datetime
import os
import venv
import platform

def create_venv():
    """Create virtual environment if it doesn't exist"""
    venv_dir = 'venv'
    if not os.path.exists(venv_dir):
        print("Creating virtual environment...")
        venv.create(venv_dir, with_pip=True)
        print("Virtual environment created successfully!")
    return venv_dir

def get_venv_python():
    """Get the path to the virtual environment's Python executable"""
    if platform.system() == 'Windows':
        python_path = os.path.join('venv', 'Scripts', 'python.exe')
    else:
        python_path = os.path.join('venv', 'bin', 'python')
    return python_path

def get_venv_pip():
    """Get the path to the virtual environment's pip executable"""
    if platform.system() == 'Windows':
        pip_path = os.path.join('venv', 'Scripts', 'pip.exe')
    else:
        pip_path = os.path.join('venv', 'bin', 'pip')
    return pip_path

def check_and_install_requirements():
    """Check and install required packages in virtual environment"""
    if not os.path.exists('requirements.txt'):
        print("Creating requirements.txt...")
        with open('requirements.txt', 'w') as f:
            f.write("""confluent-kafka
requests
flask
folium
pandas
python-dotenv
""")

    print("Installing requirements in virtual environment...")
    try:
        pip_path = get_venv_pip()
        subprocess.check_call([pip_path, 'install', '-r', 'requirements.txt'])
        print("All requirements installed successfully!")
    except Exception as e:
        print(f"Error installing requirements: {e}")
        sys.exit(1)

def run_command(command, log_file):
    """Run a command and log its output"""
    with open(log_file, 'a') as f:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        for line in process.stdout:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f'[{timestamp}] {line}')
            f.flush()
            print(f'[{timestamp}] {line}', end='')
            
        process.wait()
        return process.returncode

def main():
    # Create virtual environment
    venv_dir = create_venv()
    
    # Get virtual environment Python path
    python_path = get_venv_python()
    
    # Check and install requirements
    check_and_install_requirements()

    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Start all components using virtual environment Python
    processes = {
        'producer': {
            'command': [python_path, 'producer.py'],
            'log': 'logs/producer.log'
        },
        'consumer': {
            'command': [python_path, 'consumer.py'],
            'log': 'logs/consumer.log'
        },
        'flask': {
            'command': [python_path, 'app.py'],
            'log': 'logs/flask.log'
        }
    }

    print("Starting all components...")
    
    try:
        # Start each component in a separate process
        for name, config in processes.items():
            print(f"Starting {name}...")
            subprocess.Popen(
                config['command'],
                stdout=open(config['log'], 'a'),
                stderr=subprocess.STDOUT
            )
            time.sleep(2)  # Wait a bit between starting components
        
        print("\nAll components started!")
        print("Logs are being written to the 'logs' directory")
        print("\nPress Ctrl+C to stop all components")
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping all components...")
        # Kill all Python processes (this will stop our components)
        if platform.system() == 'Windows':
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe'])
        else:
            subprocess.run(['pkill', '-f', 'python'])
        print("All components stopped")

if __name__ == '__main__':
    main()