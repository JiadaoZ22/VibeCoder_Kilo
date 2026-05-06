# Kilo Code

## Set Up Kilo Code CLI
> Refer https://kilo.ai/docs/code-with-ai/platforms/cli
```bash
npm install -g @kilocode/cli
```

### Set Up LM Providers

#### OpenRouter
- That is easy, just `kilo` and then `/connect`, and then choose `OpenRouter` and select the default model you'd like to use as favourite.

#### Ark (Voclano Engine)
> Refer https://www.volcengine.com/docs/82379/1928261?lang=zh
- created *~/.config/kilo/opencode.json* with the Ark (Volcano Engine Coding Plan) setup.
    - Provider ID: ark
    - Base URL: https://ark.cn-beijing.volces.com/api/coding/v3 (OpenAI-compatible ndpoint for Coding Plan), or https://ark.cn-beijing.volces.com/api/coding.
    - API Key: pulled from your existing *~/.local/share/kilo/auth.json*, which is set by Kilo's `connect` commands.
    - Models: all supported Coding Plan models from the doc:
        - doubao-seed-2.0-code/pro/lite
        - doubao-seed-code
        - minimax-latest (MiniMax M2.7)
        - glm-5.1, glm-4.7
        - deepseek-v3.2
        - kimi-k2.6, kimi-k2.5
        - **Default model is set to ark/glm-5.1 You can change the "model" field at the top level to any other model ID (e.g., "ark/deepseek-v3.2").**
- Next steps:
    1. Restart Kilo (kilo or kilocode).
    2. Run /models in the TUI to switch models if needed.
    3. If you ever want to rotate the key without editing this file, replace "apiK with "apiKey": "{env:ARK_API_KEY}" and set the environment variable instead