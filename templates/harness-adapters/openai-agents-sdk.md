# OpenAI Agents SDK Adapter Notes

Use the OpenAI Agents SDK when the application itself needs an agent runtime:

- Tool-using application flows.
- Handoffs between specialized agents.
- Streaming partial results.
- Tracing and operational visibility.
- Reusable agent components inside a product.

Do not use this kit to reimplement the SDK runtime. Keep project instructions
and security policy in the canonical templates, and keep runtime code in the
application.

Official references:

- https://platform.openai.com/docs/guides/agents-sdk/
- https://platform.openai.com/docs/api-reference/responses

