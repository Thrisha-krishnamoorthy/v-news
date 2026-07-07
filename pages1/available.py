import google.generativeai as genai

# 🔐 Replace with your API key
genai.configure(api_key="AIzaSyD3ZGW08Dq2C7Ruq6TnosvbIyhhInOPXY8")

# Fetch and list all available models
models = genai.list_models()

print("📦 Available Models:")
for model in models:
    print(f"- {model.name} | Input Type: {model.input_token_limit} tokens")
# Example in Python
usage_counter = 0

# import datetime

# usage_counter = 0

# def call_gemini_api():
#     global usage_counter
#     usage_counter += 1
#     now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     print(f"[{now}] Used {usage_counter} requests so far today.")
#     # Call the actual API here

