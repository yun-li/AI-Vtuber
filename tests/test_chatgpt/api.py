from openai import OpenAI
client = OpenAI(api_key="sk-")

for data in client.models.list().data:
    print(data)
