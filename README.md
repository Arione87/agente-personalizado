---
title: Assistente de IA configurável
emoji: "🎓"
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.50.0
app_file: app.py
pinned: false
---

# Assistente de IA configurável

Um chat em português, pronto para publicar em um **Hugging Face Space**. A personalidade, identidade visual, modelos e perguntas de exemplo ficam em um único arquivo: [`config/assistant.yaml`](config/assistant.yaml).

## Publicar

1. Crie um Space **Gradio** público no Hugging Face.
2. No GitHub, adicione os secrets `HF_TOKEN` (token com permissão de escrita) e `HF_SPACE_ID` (`usuario/nome-do-space`).
3. No Space, crie secrets para cada chave que for usar: `OPENROUTER_API_KEY`, `OPENAI_API_KEY` e/ou `ANTHROPIC_API_KEY`.
4. Faça push para a branch `main`. O workflow valida a configuração e procura segredos antes de sincronizar o Space.

Se a validação falhar, o passo de sincronização não é executado: a versão que já está no Space continua no ar. Veja a aba **Actions** do GitHub para a mensagem de correção.

## Personalizar sem código

Edite somente `config/assistant.yaml` pela interface do GitHub. Antes de salvar, mantenha todos os campos obrigatórios preenchidos e use cores hexadecimais (por exemplo, `#0B3D91`). A logo deve apontar para um arquivo existente dentro deste repositório.

O `api_key_env` é o **nome** do secret no Hugging Face; nunca cole o valor da chave no YAML. A lista `providers` é tentada de cima para baixo. Provedores suportados: `openrouter`, `openai` e `anthropic`.

### Rodar localmente

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export OPENROUTER_API_KEY='sua-chave'
python app.py
```

Para verificar o arquivo de configuração sem iniciar o chat:

```bash
python scripts/validate_config.py
```

## Segurança

Chaves são lidas apenas de variáveis de ambiente configuradas como secrets do Space. O workflow usa Gitleaks para bloquear credenciais versionadas por engano. Caso ele detecte uma chave, revogue-a no provedor antes de prosseguir.
