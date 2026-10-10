# Deploy the research advisor

The web interface is `app.py`. It can run locally or be deployed from the GitHub repository to [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Run locally

Python 3.10 or newer is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

The app opens in your browser. Choose a model provider, enter your own API key in the password field, choose a model supported by that provider, and submit a topic. The tracker itself does not need a model key; the key is only used for the AI synthesis.

## Deploy from GitHub

1. Push the project to your GitHub repository.
2. Sign in at [Streamlit Community Cloud](https://share.streamlit.io/) and connect GitHub.
3. Choose **Create app**, select `nadiw1245/OpenScienceAgentBench`, branch `main`, and entrypoint `app.py`.
4. Deploy. Community Cloud installs the dependencies from `requirements.txt`.
5. Open the app, choose a provider, and use your own key and model. Do not add a shared personal model key to the app's secrets for a public app.

See Streamlit's [deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) for current setup details. Streamlit changes its UI and hosting policies over time.

## Key and data handling

- A provider key typed into the app is processed by the Streamlit server for that request; the app does not write it to the repository or a database.
- The selected model provider receives your question, researcher profile, and the retrieved paper titles and abstracts. Read its current data terms before sending unpublished or sensitive material.
- Anyone operating the hosting server can technically access data processed by that server. Self-host the app if you need to control the runtime.
- Do not place a personal API key in a public app's shared configuration. Visitors could use it and create charges.
- A public app has no built-in account system or usage quota. Keep provider credit limits in place and monitor usage if you publish it.
- arXiv retrieval uses public metadata and does not require a key.
