import google.generativeai as genai
import os

genai.configure(api_key="AIzaSyCGqin4BhFsdOsvbQOv2_gYjW3kGJJo1d4")

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)

model = genai.GenerativeModel(model_name = "gemini-pro")
messages = [
    {
        'role':'user',
        'parts': ["你好"]
    }
]

response = model.generate_content(messages, stream=False)
print(response.text)