import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
found_dotenv = False


def find_and_load_dotenv(base_dir) -> bool:
    for root, dirs, files in os.walk(base_dir):
        logger.debug(f"Checking {root} for .env file")
        if '.env' in files:
            dotenv_path = os.path.join(root, '.env')
            load_dotenv(dotenv_path)
            logger.info(f".env file loaded from: {dotenv_path}")
            return True

    return False


# First check for a .secrets folder. Unsure why this would load ALL the .envs in the folder but leaving
# the behavior as is.
# Load sensitive information such as API keys from .env files so that they are not stored in the repository
# but can still be accessed by the tests through os.environ
secrets_path = Path(__file__).parent.parent / '.secrets'
if secrets_path.exists():
    for secret_file in secrets_path.glob('*.env'):
        load_dotenv(secret_file)
        found_dotenv = True


# Next, check the directory where script is being run
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
logger.debug(f"script_dir: {script_dir}")
found_dotenv = find_and_load_dotenv(script_dir)

if not found_dotenv:
    # Lastly, check the root directory of the project. This should probably be checked first,
    # since it's what the readme says to do.
    cwd_dir = os.getcwd()
    logger.debug(f"cwd_dir: {cwd_dir}")
    found_dotenv = find_and_load_dotenv(cwd_dir)

# If no .env file was found, print a warning message
if not found_dotenv:
    # Create a colored message for the log using termcolor
    msg = "No .env file found. please create a .env file in the root directory of the project."
    logger.warning(msg)
