# Aftermath AI

Aftermath AI is an AI-powered postmortem generation Agent for SRE teams. It ingests incident communication from Slack, deployment logs, and optionally GitHub data to automatically synthesize structured postmortem reports using LLMs.

## Key Features

* Slash-command workflow directly from Slack (`/aftermath generate-postmortem`)
* Automated context gathering (Slack, deploy logs, GitHub)
* Agent-based LLM pipeline (LangChain)
* Structured postmortem output (Summary → Impact → Timeline → RCA → Remediation)
* Modular ingestion system
* Kubernetes-ready deployment

## Architecture Overview

The system is split into three major layers:

| Layer                    | Responsibility                                          |
| ------------------------ | ------------------------------------------------------- |
| Ingestion                | Fetching raw data from Slack, GitHub, deployments       |
| Parsing/Context-building | Transforming raw logs into LLM-ready structured context |
| LLM agent                | Synthesising a final postmortem report                  |


## Data Flow

```
Slack Slash Command → FastAPI Endpoint → Ingestion → Parsing → Agent → LLM → Postmortem
```

## Slack Integration

The system exposes a public endpoint for `/aftermath generate-postmortem`.
You will need to configure a Slack App with:

* Slash command URL → `https://<domain>/api/v1/reports`
* Bot token
* Signing secret

## License

TBD

## Next Steps

* Add retry/error handling to LLM agent
* Structured output validation
* Multi-incident memory