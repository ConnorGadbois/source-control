from .config import config
from datetime import datetime

class LogLevel:
    INFO = '[INFO]'
    WARN = '[WARNING]'
    ERROR = '[ERROR]'

def log(level: LogLevel, message: str) -> None:
    log = f'{level} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - {message}\n'

    if config['logging']['print_logs']:
        print(log, end='')

    if config['logging']['write_logs']:
        with open(config['logging']['log_file'], 'a') as log_file:
            log_file.write(log)