from openai import OpenAI

client = OpenAI(api_key="sk-", base_url="https://api.openai.com/v1/")

for data in client.models.list().data:
    print(data)

completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
)

print(completion.choices[0].message)