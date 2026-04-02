from llama_cpp import Llama
import os

# CHAT_FORMAT must be set according to the model
CHAT_FORMAT = "chatml"
MODEL_PATH = "model.gguf"
SYSTEM_CONTENT = "You are an assistant who perfectly summarizes information and answers questions." 
CURRENT_WORKING_DIRECTORY = os.getcwd()

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
    git_repository_path = CURRENT_WORKING_DIRECTORY

    llm = Llama(model_path=MODEL_PATH, chat_format=CHAT_FORMAT, verbose=False)

    messages = []
    system_message = { "role": "system", "content": SYSTEM_CONTENT }
    messages.append(system_message)

    while True:
        message = input("\nQ: ")
        if not message:
            return 
        message = message.strip()

        message_split = message.split()
        if message_split:
            command = message_split[0]
            if command == "cd":
                if len(message_split) == 1:
                    git_repository_path = CURRENT_WORKING_DIRECTORY

                else:
                    new_relative_path = os.path.join(git_repository_path, message_split[1])
                    new_absolute_path = os.path.join(message_split[1])
                    if os.path.isdir(new_relative_path):
                        git_repository_path = new_relative_path

                    elif os.path.isdir(new_absolute_path):
                        git_repository_path = new_absolute_path

                    git_repository_path = os.path.realpath(git_repository_path)

                print(f"A: {git_repository_path}")
                continue

            elif command == "pwd":
                print(f"A: {git_repository_path}")
                continue

        messages.append( { "role": "user", "content": message } )

        chat_completion = llm.create_chat_completion(messages=messages)
        content = chat_completion_get_content(chat_completion)

        content = content.strip()
        print("A: " + content)

        messages.append( { "role": "assistant", "content": content } )

main()
