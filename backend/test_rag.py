import sys
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.DEBUG)

from rag.chain import answer

try:
    print("Testing answer...")
    result = answer("What does NCPDP reject code 75 mean and how do I resolve it?", "test-session")
    print("SUCCESS")
    print(result)
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
