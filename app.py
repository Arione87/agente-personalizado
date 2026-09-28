"""Chat configurável com tentativa automática de provedores de IA."""
import os
from pathlib import Path
from typing import Literal

import gradio as gr
import requests
import yaml
from pydantic import BaseModel, Field, field_validator


ROOT = Path(__file__).parent


class AssistantSettings(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    logo: str = Field(min_length=1)
    logo_size: int = Field(ge=24, le=200)
    primary_color: str
    secondary_color: str
    max_output_tokens: int = Field(ge=50, le=4000)

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def valid_color(cls, value: str) -> str:
        if not value.startswith("#") or len(value) not in (4, 7) or not all(c in "0123456789abcdefABCDEF" for c in value[1:]):
            raise ValueError("use uma cor hexadecimal, como #155EEF")
        return value


class Provider(BaseModel):
    provider: Literal["openrouter", "openai", "anthropic"]
    model: str = Field(min_length=1)
    api_key_env: str = Field(pattern=r"^[A-Z][A-Z0-9_]*$")


class Settings(BaseModel):
    assistant: AssistantSettings
    providers: list[Provider] = Field(min_length=1)
    behavior: str = Field(min_length=1)
    example_questions: list[str] = Field(min_length=1, max_length=8)


def load_settings() -> Settings:
    return Settings.model_validate(yaml.safe_load((ROOT / "config/assistant.yaml").read_text(encoding="utf-8")))


SETTINGS = load_settings()


def call_provider(item: Provider, messages: list[dict]) -> str:
    key = os.getenv(item.api_key_env)
    if not key:
        raise RuntimeError(f"o secret {item.api_key_env} não está configurado no Space")
    if item.provider in ("openrouter", "openai"):
        url = "https://openrouter.ai/api/v1/chat/completions" if item.provider == "openrouter" else "https://api.openai.com/v1/chat/completions"
        response = requests.post(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": item.model, "messages": messages, "max_tokens": SETTINGS.assistant.max_output_tokens}, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    response = requests.post("https://api.anthropic.com/v1/messages", headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}, json={"model": item.model, "system": SETTINGS.behavior, "messages": messages[1:], "max_tokens": SETTINGS.assistant.max_output_tokens}, timeout=60)
    response.raise_for_status()
    return response.json()["content"][0]["text"]


def answer(message: str, history: list[dict]) -> str:
    messages = [{"role": "system", "content": SETTINGS.behavior}, *history, {"role": "user", "content": message}]
    failures = []
    for item in SETTINGS.providers:
        try:
            return call_provider(item, messages)
        except (requests.RequestException, KeyError, IndexError, RuntimeError) as error:
            failures.append(f"- **{item.provider}/{item.model}**: {str(error)[:300]}")
    return "Não foi possível obter uma resposta com os provedores configurados.\n\n**Tentativas:**\n" + "\n".join(failures)


def submit(message: str, history: list[dict] | None) -> tuple[list[dict], str]:
    history = history or []
    if not message.strip():
        return history, ""
    reply = answer(message, history)
    return [*history, {"role": "user", "content": message}, {"role": "assistant", "content": reply}], ""


def build_app() -> gr.Blocks:
    a = SETTINGS.assistant
    css = f""":root {{ --primary: {a.primary_color}; --secondary: {a.secondary_color}; }} .gradio-container {{ background: var(--secondary); }} #title {{ color: var(--primary); }} .gr-button-primary {{ background: var(--primary) !important; }}"""
    with gr.Blocks(title=a.name, css=css) as app:
        with gr.Row():
            gr.Image(value=str(ROOT / a.logo), width=a.logo_size, height=a.logo_size, show_label=False, container=False, interactive=False)
            with gr.Column():
                gr.Markdown(f"# <span id='title'>{a.name}</span>\n{a.description}")
        chatbot = gr.Chatbot(type="messages", label="Conversa", height=460)
        box = gr.Textbox(label="Sua pergunta", placeholder="Escreva sua dúvida aqui…")
        with gr.Row():
            send = gr.Button("Enviar", variant="primary")
            clear = gr.Button("Limpar conversa")
        gr.Markdown("### Perguntas para começar")
        for question in SETTINGS.example_questions:
            example = gr.Button(question)
            example.click(submit, inputs=[example, chatbot], outputs=[chatbot, box])
        send.click(submit, inputs=[box, chatbot], outputs=[chatbot, box])
        box.submit(submit, inputs=[box, chatbot], outputs=[chatbot, box])
        clear.click(lambda: ([], ""), outputs=[chatbot, box])
    return app


if __name__ == "__main__":
    build_app().launch()
