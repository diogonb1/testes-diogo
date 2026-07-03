# ChatGPT Projetos API

API local para aplicar a organização por **projeto + entrega** nos chats existentes. Ela classifica conversas exportadas do ChatGPT ou uma planilha CSV, gera estrutura de pastas e prepara publicação no GitHub.

## O que ela faz

- Classifica chats por códigos `BUI`, `MUS`, `LUT`, `CAR`, `PES`, `TEC` e `ADM`.
- Gera título sugerido para renomear chats na barra lateral.
- Gera árvore de pastas conforme a metodologia PARA/GTD/WBS/SGQ definida.
- Importa `conversations.json` da exportação oficial do ChatGPT ou CSV.
- Exporta índice `Indice_Chats_Reclassificados.csv`.
- Possui endpoints opcionais para criar issues e arquivos no GitHub.

## Limite importante

A API **não tem acesso interno à barra lateral do ChatGPT**. Para aplicar aos chats reais, use uma das duas rotas:

1. Exporte os dados do ChatGPT e envie o `conversations.json` para a API.
2. Use um CSV manual com os títulos dos chats.

Depois, use a coluna `titulo_sugerido` para renomear os chats manualmente ou como base de automação de navegador autorizada.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Rodar API

```bash
uvicorn app.main:app --reload
```

Abra:

```text
http://127.0.0.1:8000/docs
```

## Classificar um chat

```bash
curl -X POST http://127.0.0.1:8000/classificar \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Alvarás Sanitários Caucaia","conteudo":"AVCB sanitário funcionamento protocolo"}'
```

## Classificar lote por CSV

```bash
curl -X POST http://127.0.0.1:8000/classificar/lote \
  -F "file=@examples/chats_exemplo.csv"
```

## Gerar estrutura de pastas

```bash
curl -X POST "http://127.0.0.1:8000/estrutura?raiz=./ChatGPT_Projetos_Aplicado"
```

## Importar exportação do ChatGPT via linha de comando

```bash
python scripts/importar_export_chatgpt.py conversations.json --saida ChatGPT_Projetos_Aplicado_API
```

## GitHub

Crie um token com permissões adequadas e configure:

```bash
export GITHUB_TOKEN="seu_token"
```

Criar issue via API:

```bash
curl -X POST http://127.0.0.1:8000/github/issues \
  -H "Content-Type: application/json" \
  -d '{"repository_full_name":"diogonb1/testes-diogo","titulo":"[BUI-004] Alvarás Caucaia","corpo":"Matriz de pendências e responsáveis","labels":["BUI-004","projeto"]}'
```

Publicar arquivo no repositório:

```bash
python scripts/github_publicar_indice.py diogonb1/testes-diogo ChatGPT_Projetos_Aplicado_API/Indice_Chats_Reclassificados.csv docs/Indice_Chats_Reclassificados.csv
```

## Exportação oficial do ChatGPT

No ChatGPT, acesse **Settings > Data controls > Export data** e baixe o ZIP quando chegar. Dentro dele normalmente há `conversations.json`.

## Segurança

- Não coloque senha, 2FA, cartão ou segredo dentro de chat.
- Use `.env` local para tokens.
- Não versione `.env`.
- A classificação padrão é offline, por regras locais.
