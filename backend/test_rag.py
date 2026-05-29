import sys
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.DEBUG)

from rag.chain import query_rag

try:
    print("Testing query_rag...")
    result = query_rag("What does NCPDP reject code 75 mean?")
    print("SUCCESS")
    print(result.answer)
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
