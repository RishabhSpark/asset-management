import logging
import logging.handlers
import os
import yaml

import logging
import os
import yaml

def setup_logger(yaml_path: str = "app/config/logger_config.yaml") -> logging.Logger:
    # Load YAML config
    with open(yaml_path, 'r') as f:
        config = yaml.safe_load(f)

    logger_cfg = config.get('logger', {})
    if not logger_cfg:
        raise ValueError("Logger config section 'logger' not found in YAML")

    # Extract config values with defaults
    name = logger_cfg.get('name', 'app_logger')
    level_name = logger_cfg.get('level', 'INFO')
    level = getattr(logging, level_name.upper(), logging.INFO)

    log_dir = logger_cfg.get('log_dir', 'logs')
    file_name = logger_cfg.get('file_name', 'app.log')

    handlers_cfg = logger_cfg.get('handlers', {})
    console_cfg = handlers_cfg.get('console', {})
    file_cfg = handlers_cfg.get('file', {})

    format_cfg = logger_cfg.get('format', {})
    pattern = format_cfg.get('pattern', '[%(asctime)s] [%(levelname)s] %(name)s: %(message)s')
    datefmt = format_cfg.get('datefmt', '%Y-%m-%d %H:%M:%S')

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Avoid duplicate logs if root logger configured

    # Clear existing handlers if any
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(pattern, datefmt)

    # Create log directory if needed
    os.makedirs(log_dir, exist_ok=True)

    # Console handler
    if console_cfg.get('enabled', False):
        console_level_name = console_cfg.get('level', level_name)
        console_level = getattr(logging, console_level_name.upper(), level)
        ch = logging.StreamHandler()
        ch.setLevel(console_level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    # File handler
    if file_cfg.get('enabled', False):
        file_level_name = file_cfg.get('level', level_name)
        file_level = getattr(logging, file_level_name.upper(), level)
        file_path = os.path.join(log_dir, file_name)
        fh = logging.FileHandler(
            filename=file_path,
            mode='a', 
            encoding='utf-8'
        )
        fh.setLevel(file_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger