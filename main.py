from llama_cpp import Llama
import os
import subprocess
import mimetypes

# CHAT_FORMAT must be set according to the model
CHAT_FORMAT = "chatml"
MODEL_PATH = "model.gguf"
DEFAULT_SYSTEM_CONTENT = "You are an assistant who perfectly summarizes information and answers questions." 
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

def path_is_repository(path):
    is_repository = subprocess.run(["git", "-C", path, "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
    if is_repository.stdout:
        return True

    return False

def path_is_repository_message(path):
    is_repository = path_is_repository(path)
    if is_repository:
        return "(git repository)"
    return "(not a git repository)"

def path_get_repository_files(path):
    git_repository_files = []
    if (path_is_repository(path)):
        git_repository_files = subprocess.run(["git", "ls-tree", "--full-tree", "-r", "--name-only", "HEAD"], capture_output=True, text=True).stdout.split()

    return git_repository_files

def main():
    system_content = DEFAULT_SYSTEM_CONTENT
    git_repository_path = CURRENT_WORKING_DIRECTORY
    git_repository_files = path_get_repository_files(git_repository_path)
    if git_repository_files:
        system_content += "\nYou may use the following files to help you answer the questions if necessary:\n\n"
        for file_name in git_repository_files:
            absolute_file_path = os.path.join(git_repository_path, file_name)
            mime_type = mimetypes.guess_type(absolute_file_path)[0]
            if not mime_type or not mime_type.startswith("text/"):
                continue

            system_content += file_name + ":\n"
            with open(absolute_file_path, "r") as file:
                file_data = file.read().rstrip()
                system_content += file_data + "\n\n"

    # if n_ctx is 0, it is determined from the model
    llm = Llama(model_path=MODEL_PATH, chat_format=CHAT_FORMAT, n_ctx=0, verbose=False)

    messages = []
    system_message = { "role": "system", "content": system_content }
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

                print(f"A: {git_repository_path} {path_is_repository_message(git_repository_path)}")
                continue

            elif command == "pwd":
                print(f"A: {git_repository_path} {path_is_repository_message(git_repository_path)}")
                continue

        messages.append( { "role": "user", "content": message } )

        chat_completion = llm.create_chat_completion(messages=messages)
        content = chat_completion_get_content(chat_completion)

        content = content.strip()
        print("A: " + content)

        messages.append( { "role": "assistant", "content": content } )

main()
