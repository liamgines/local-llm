from llama_cpp import Llama

# CHAT_FORMAT must be set according to the model
CHAT_FORMAT = "chatml"
MODEL_PATH = "model.gguf"
SYSTEM_CONTENT = "You are an assistant who perfectly summarizes information and answers questions." 

def chat_completion_get_contents(chat_completion):
    contents = []
    if "choices" not in chat_completion:
        return contents
    
    choices = chat_completion["choices"]
    for choice in choices:
        if "message" not in choice:
            continue

        message = choice["message"]
        if "content" not in message:
            continue

        content = message["content"]
        contents.append(content)

    return contents

def chat_completion_get_content(chat_completion):
    # return chat_completion["choices"][0]["message"]["content"]

    contents = chat_completion_get_contents(chat_completion)
    if not contents:
        return ""

    return contents[0]

def main():
    llm = Llama(model_path=MODEL_PATH, chat_format=CHAT_FORMAT, verbose=False)

    messages = []
    system_message = { "role": "system", "content": SYSTEM_CONTENT }
    messages.append(system_message)

    while True:
        message = input("\nQ: ")
        if not message:
            return 

        message = message.strip()
        messages.append( { "role": "user", "content": message } )

        chat_completion = llm.create_chat_completion(messages=messages)
        content = chat_completion_get_content(chat_completion)

        content = content.strip()
        print("A: " + content)

        messages.append( { "role": "assistant", "content": content } )

main()
