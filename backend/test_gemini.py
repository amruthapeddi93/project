import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing")

client = genai.Client(api_key=api_key)

models = [
    "gemini-3.8-flash",
    "gemini-3.6-flash",
]

for model in models:
    print(f"\nTesting model: {model}")

    try:
        response = client.models.generate_content(
            model=model,
            contents="Analyze this headline sentiment: "
            "Company reports strong quarterly revenue growth. "
            "Return only Positive, Negative, or Neutral.",
        )

        print("SUCCESS")
        print("Response:", response.text)

    except Exception as error:
        print("FAILED")
        print("Error type:", type(error).__name__)
        print("Error:", str(error))
