import sys
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

models_to_test = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-8b",
]

for model_name in models_to_test:
    print(f"Testing {model_name}...")
    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0,
            max_retries=0, # FAIL FAST
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        response = llm.invoke("Hi")
        print(f"SUCCESS: {model_name} works!")
    except Exception as e:
        print(f"FAILED: {model_name} - {str(e)[:150]}")
