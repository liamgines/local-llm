from llama_cpp import Llama
import os
import subprocess
import mimetypes
import requests
from markitdown import MarkItDown
from urllib.parse import urljoin, urlsplit
from dotenv import load_dotenv

load_dotenv()

# CHAT_FORMAT must be set according to the model
CHAT_FORMAT = os.getenv("CHAT_FORMAT")
MODEL_PATH = os.getenv("MODEL_PATH")
DEFAULT_SYSTEM_CONTENT = "You are an assistant who perfectly summarizes information and answers questions." 
CURRENT_WORKING_DIRECTORY = os.path.realpath(os.getcwd())

SEARCH_ENGINE_BASE_URL = os.getenv("SEARCH_ENGINE_BASE_URL")
USER_AGENT = os.getenv("USER_AGENT")
SEARCH_HEADERS = { "Accept": "application/json,text/html;q=0.9,*/*;q=0.8", "User-Agent": USER_AGENT }

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
    try:
        is_repository = subprocess.run(["git", "-C", path, "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
    except:
        return False

    if is_repository.stdout:
        return True

    return False

def path_is_repository_message(path):
    is_repository = path_is_repository(path)
    if is_repository:
        return "(git repository)"
    return ""
    # return "(not a git repository)"

def path_get_repository_files(path):
    git_repository_files = []
    if (path_is_repository(path)):
        git_repository_files = subprocess.run(["git", "-C", path, "ls-tree", "--full-tree", "-r", "--name-only", "HEAD"], capture_output=True, text=True).stdout.split()

    return git_repository_files

def system_content_get(git_repository_path):
    system_content = DEFAULT_SYSTEM_CONTENT
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

    return system_content

def path_repository_commit_hash(path):
    commit_hash = ""
    if path_is_repository(path):
        commit_hash = subprocess.run(["git", "-C", path, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

    return commit_hash

def directory_print(git_repository_path):
    print(f"A: {git_repository_path} {path_is_repository_message(git_repository_path)}")

def directory_change(full_command, git_repository_path):
    if len(full_command) == 1:
        git_repository_path = CURRENT_WORKING_DIRECTORY

    else:
        new_relative_path = os.path.join(git_repository_path, full_command[1])
        new_absolute_path = os.path.join(full_command[1])
        if os.path.isdir(new_relative_path):
            git_repository_path = new_relative_path

        elif os.path.isdir(new_absolute_path):
            git_repository_path = new_absolute_path

        git_repository_path = os.path.realpath(git_repository_path)

    return git_repository_path


def web_search_first_page_urls(search_url, parameters):
    urls = []

    try:
        response = requests.get(search_url, params=parameters)

    except:
        print(f"ERROR: Search engine failed to load.")
        return urls

    if response.status_code < 200 or response.status_code >= 300:
        print(f"ERROR: Web search failed.")
        return urls

    response_json = response.json()
    if "results" in response_json:
        results = response_json["results"]
        for result in results:
            if "url" in result:
                url = result["url"]
                urls.append(url)
    if urls:
        print("SUCCESS: ", end="")

    else:
        print("ERROR: ", end="")

    print(f"Web search retrieved {len(urls)} url{"" if len(urls) == 1 else "s"}.")
    return urls

def web_search_with_local_engine(query):
    search_url = urljoin(SEARCH_ENGINE_BASE_URL, "search")
    search_parameters = { "q": query, "format": "json" }

    urls = web_search_first_page_urls(search_url, search_parameters)
    return urls

def url_to_markdown(url):
    if not url:
        return ""

    print(f"Converting {url} to Markdown...")

    response = requests.get(url, headers=SEARCH_HEADERS)
    markitdown = MarkItDown()
    document_converter_result = markitdown.convert(response)
    return document_converter_result.text_content

def web_search_first_result_to_markdown(query):
    urls = web_search_with_local_engine(query)
    if not urls:
        return ""

    first_url = urls[0]
    markdown = url_to_markdown(first_url)
    return markdown


def main():
    git_repository_path = CURRENT_WORKING_DIRECTORY

    # if n_ctx is 0, it is determined from the model
    llm = Llama(model_path=MODEL_PATH, chat_format=CHAT_FORMAT, n_ctx=0, verbose=False)

    messages = []
    system_message = { "role": "system", "content": system_content_get(git_repository_path) }
    messages.append(system_message)
    commit_hash = path_repository_commit_hash(git_repository_path)

    while True:
        message = input("\nQ: ")
        if not message:
            return 
        print()
        message = message.strip()

        message_split = message.split()
        command = ""
        if message_split:
            command = message_split[0]
            if command == "cd":
                previous_git_repository_path = git_repository_path
                git_repository_path = directory_change(message_split, git_repository_path)
                directory_print(git_repository_path)

                if previous_git_repository_path != git_repository_path:
                    system_message = { "role": "system", "content": system_content_get(git_repository_path) }
                    # Reset history if path was changed
                    messages = [system_message]

                continue

            elif command == "pwd":
                directory_print(git_repository_path)
                continue

            elif command == "web-search":
                search_query = ""
                for i in range(1, len(message_split)):
                    search_query += message_split[i] + " "

                if not search_query:
                    print("A: Search query cannot be empty.")
                    continue

                markdown = web_search_first_result_to_markdown(search_query)
                if not markdown:
                    print("A: Web search yielded no results.")
                    continue

                message = search_query + "\n\n"
                message += "Please provide a short answer if possible and reference the following information if applicable:\n"
                message += markdown

        if commit_hash != path_repository_commit_hash(git_repository_path):
            commit_hash = path_repository_commit_hash(git_repository_path)
            system_message = { "role": "system", "content": system_content_get(git_repository_path) }
            # Get new system message if commit hash changed
            messages[0] = system_message

        messages.append( { "role": "user", "content": message } )

        print("Waiting for response...\n")
        chat_completion = llm.create_chat_completion(messages=messages)
        content = chat_completion_get_content(chat_completion)

        content = content.strip()
        if content.startswith("A:"):
            content = content[2:]
        content = content.strip()
        print("A: " + content)

        messages.append( { "role": "assistant", "content": content } )

        # Remove last two messages from history since storing pages may cause the token limit to be reached too quickly
        if command == "web-search":
            messages.pop()
            messages.pop()

main()
