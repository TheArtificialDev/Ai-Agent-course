# Production Deployment

This repository has two deployable surfaces:

- `chainlit`: the authenticated Python nutrition assistant on port `10000`.
- `chatkit`: the Next.js frontend and ChatKit session API on port `3000`.
- `multi-agent`: an optional Chainlit service on port `10001` that also needs `EXA_API_KEY` for web search.

## Required environment

Create a server-side `.env` file. Do not commit it or bake it into an image.

```dotenv
OPENAI_API_KEY=replace-with-a-new-key
CHAINLIT_AUTH_SECRET=replace-with-a-long-random-secret
CHAINLIT_USERNAME=choose-a-login
CHAINLIT_PASSWORD=choose-a-password
NEXT_PUBLIC_CHATKIT_WORKFLOW_ID=wf_your_published_workflow_id
# Optional for multi-agent web search
EXA_API_KEY=replace-with-exa-key
```

Generate a Chainlit secret with `chainlit create-secret`. Rotate any credentials that have been exposed during development before deploying.

## Docker Compose

From the repository root:

```bash
docker compose -f docker-compose.production.yml up -d --build
```

The Chainlit app is available on port `10000`, the optional multi-agent app on `10001`, and the ChatKit frontend on `3000`. Chroma data and conversation databases are stored in named Docker volumes. Back up those volumes and put a TLS reverse proxy in front of the public services.

The ChatKit health check is `GET /api/health`. Configure the OpenAI domain allowlist for the final HTTPS frontend domain before accepting traffic.

The workflow ID is public configuration and is passed as a Docker build argument because Next.js embeds `NEXT_PUBLIC_*` values into the browser bundle at build time. Rebuild the ChatKit image whenever this value changes.

To run only the authenticated Chainlit service and frontend:

```bash
docker compose -f docker-compose.production.yml up -d --build chainlit chatkit
```

## Manual launches

Python Chainlit:

```bash
cd chatbot_complete
chainlit run 4_authentication.py --host 0.0.0.0 --port 10000
```

Next.js:

```bash
cd chatkit
npm ci
npm run build
npm run start
```

Keep `OPENAI_API_KEY` and Chainlit secrets server-side. The browser only receives the public workflow ID and the short-lived ChatKit client secret returned by `/api/create-session`.

## Render

The repository includes a Render Blueprint in `render.yaml`.

1. Push this repository to GitHub or GitLab.
2. In Render, choose **New > Blueprint** and select the repository.
3. Set the secret values requested by Render: `OPENAI_API_KEY`, `CHAINLIT_USERNAME`, and `CHAINLIT_PASSWORD`.
4. Set `NEXT_PUBLIC_CHATKIT_WORKFLOW_ID` to the published Agent Builder workflow ID if deploying the ChatKit service.
5. Deploy both services.

Render will build the authenticated Chainlit service and the ChatKit frontend. The Chainlit service uses Render's persistent disk for conversation history and Chroma data. A persistent disk requires a paid Render instance; without one, local SQLite and Chroma data are ephemeral after redeploys. The ChatKit public URL must be added to OpenAI's domain allowlist.

For a Chainlit-only deployment, create one Render web service with:

```text
Build command: pip install -r requirements.txt
Start command: cd chatbot_complete && chainlit run 4_authentication.py --host 0.0.0.0 --port $PORT
Health check path: /
```
