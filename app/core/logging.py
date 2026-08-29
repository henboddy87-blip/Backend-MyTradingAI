import logging
import sys
from datetime import datetime

# Configure standard logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("mytradeai")

def get_logger(name: str):
    return logging.getLogger(f"mytradeai.{name}")
