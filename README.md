Local LLM
========
A script for chatting with a large language model (LLM) that runs locally.

Installation
--------
First, ensure you have Python 3 installed.

Then, run the following commands:
```
git clone <repository_url>
cd local-llm
py -m pip install --upgrade pip
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Next, create a `.env` file with this structure:
```
MODEL_PATH="model.gguf"
CHAT_FORMAT="chatml"

SEARCH_ENGINE_BASE_URL="http://localhost:8080"
USER_AGENT="User Agent"
```

Finally, run `py main.py` with the virtual environment activated.

If you want to give a LLM context about a local git repository, install Git.

If you want to give a LLM context about the first web search result related to your prompt, you need access to a search engine like SearXNG.

To use SearXNG, proceed with the following:
1. Install Docker Desktop.
2. Use Docker Desktop to install the `searxng/searxng` Docker image.
3. Assign a host port, then run the image. The search engine will now be running in a container. You should be able to access the search engine at `http://localhost:{port}` with the host port you assigned.
4. Find the `settings.yml` file in the container and open it for editing.
5. Locate the `search` key and the `formats` subkey under that and add `json` to the formats list so it looks something like:
```
search:
  ...
  formats:
    - html
    - json
```
6. Save the file and restart the container so the search engine can respond to searches with `json` on request.
