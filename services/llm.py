from groq import AsyncGroq
from dotenv import load_dotenv
import os
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_default_api_key_here")
async def generate_answer(query: str, context: str):
    client = AsyncGroq(api_key=GROQ_API_KEY)
    chat_completion = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Context: {context}\n\nQuestion: {query}"
            }
        ],
        model="llama-3.1-8b-instant",
    )
    return chat_completion.choices[0].message.content