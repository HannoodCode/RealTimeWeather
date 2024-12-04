import subprocess
import sys
import time
from datetime import datetime
import os

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
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Start all components
    processes = {
        'producer': {
            'command': [sys.executable, 'producer.py'],
            'log': 'logs/producer.log'
        },
        'consumer': {
            'command': [sys.executable, 'consumer.py'],
            'log': 'logs/consumer.log'
        },
        'flask': {
            'command': [sys.executable, 'app.py'],
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
        if sys.platform == 'win32':
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe'])
        else:
            subprocess.run(['pkill', '-f', 'python'])
        print("All components stopped")

if __name__ == '__main__':
    main()