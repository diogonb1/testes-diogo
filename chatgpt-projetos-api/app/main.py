from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from .models import ChatEntrada, ChatClassificado, EstruturaResultado, GitHubFileRequest, GitHubIssueRequest, ImportacaoResultado
from .rules import classify_text, load_rules
from .services import (
    classify_rows,
    create_readme_for_project,
    create_structure,
    github_create_issue,
    github_create_or_update_file,
    import_chatgpt_json,
    import_csv,
    write_index_csv,
    zip_project,
)

app = FastAPI(
    title="ChatGPT Projetos API",
    version="0.1.0",
    description="Classifica chats existentes por projeto+entrega e gera estrutura BUI/MUS/LUT/CAR/PES/TEC/ADM.",
)


@app.get("/")
def home() -> dict[str, str]:
    return {
        "status": "ok",
        "uso": "Acesse /docs para testar a API.",
        "limite": "Não renomeia a barra lateral do ChatGPT diretamente; trabalha com exportações/CSV e GitHub.",
    }


@app.get("/projetos")
def listar_projetos() -> dict:
    return load_rules()["projetos"]


@app.post("/classificar", response_model=ChatClassificado)
def classificar_chat(chat: ChatEntrada) -> ChatClassificado:
    c = classify_text(chat.titulo, chat.conteudo)
    return ChatClassificado(titulo_original=chat.titulo, classificacao=c)


@app.post("/classificar/lote", response_model=ImportacaoResultado)
async def classificar_lote(file: UploadFile = File(...)) -> ImportacaoResultado:
    suffix = Path(file.filename or "upload").suffix.lower()
    data = await file.read()
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / (file.filename or "upload")
        p.write_bytes(data)
        if suffix == ".json":
            rows = import_chatgpt_json(p)
        elif suffix == ".csv":
            rows = import_csv(p)
        else:
            raise HTTPException(status_code=400, detail="Envie .json exportado do ChatGPT ou .csv com coluna titulo.")
        classified = classify_rows(rows)
    return ImportacaoResultado(total=len(classified), classificados=classified)


@app.post("/estrutura", response_model=EstruturaResultado)
def gerar_estrutura(raiz: str = "./ChatGPT_Projetos_Aplicado") -> EstruturaResultado:
    root = Path(raiz).resolve()
    created = create_structure(root)
    create_readme_for_project(root)
    return EstruturaResultado(raiz=str(root), pastas_criadas=created)


@app.post("/exportar/pacote")
async def exportar_pacote(file: UploadFile = File(...)) -> FileResponse:
    suffix = Path(file.filename or "upload").suffix.lower()
    data = await file.read()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        input_file = tmp_path / (file.filename or "upload")
        input_file.write_bytes(data)
        rows = import_chatgpt_json(input_file) if suffix == ".json" else import_csv(input_file)
        classified = classify_rows(rows)
        root = tmp_path / "ChatGPT_Projetos_Aplicado_API"
        create_structure(root)
        create_readme_for_project(root)
        write_index_csv(classified, root / "Indice_Chats_Reclassificados.csv")
        zip_path = Path(tempfile.gettempdir()) / "ChatGPT_Projetos_Aplicado_API.zip"
        zip_project(root, zip_path)
    return FileResponse(zip_path, filename="ChatGPT_Projetos_Aplicado_API.zip")


@app.post("/github/issues")
def criar_issue_github(req: GitHubIssueRequest) -> dict:
    try:
        return github_create_issue(req.repository_full_name, req.titulo, req.corpo, req.labels)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/github/files")
def criar_ou_atualizar_arquivo_github(req: GitHubFileRequest) -> dict:
    try:
        return github_create_or_update_file(req.repository_full_name, req.path, req.content, req.message, req.branch)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
