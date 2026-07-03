from __future__ import annotations

import csv
import json
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from .rules import classify_text, load_rules


def create_structure(root: Path) -> list[str]:
    rules = load_rules()
    created: list[str] = []
    for item in rules.get("raiz", []):
        p = root / item
        p.mkdir(parents=True, exist_ok=True)
        created.append(str(p))
    for _, data in rules.get("projetos", {}).items():
        p = root / data["pasta"]
        p.mkdir(parents=True, exist_ok=True)
        created.append(str(p))
        if data["pasta"].startswith("01_TRABALHO_BUIATTE"):
            for sub in ["01_Fontes", "02_Analises", "03_Entregaveis", "04_Evidencias", "05_Versoes_Antigas"]:
                (p / sub).mkdir(parents=True, exist_ok=True)
                created.append(str(p / sub))
    return created


def extract_messages_from_chatgpt_conversation(conv: dict[str, Any]) -> str:
    """Extrai texto de um item do conversations.json exportado pelo ChatGPT.

    A exportação pode variar. Esta função é conservadora e ignora campos ausentes.
    """
    texts: list[str] = []
    mapping = conv.get("mapping") or {}
    for node in mapping.values():
        msg = (node or {}).get("message") or {}
        content = msg.get("content") or {}
        parts = content.get("parts") or []
        for part in parts:
            if isinstance(part, str):
                texts.append(part)
            elif isinstance(part, dict):
                texts.append(json.dumps(part, ensure_ascii=False)[:1000])
    return "\n".join(texts[:80])


def import_chatgpt_json(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "conversations" in data:
        data = data["conversations"]
    rows: list[dict[str, Any]] = []
    for conv in data:
        title = conv.get("title") or "Sem título"
        content = extract_messages_from_chatgpt_conversation(conv)
        rows.append({"titulo": title, "conteudo": content, "fonte": "conversations.json"})
    return rows


def import_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "titulo": r.get("titulo") or r.get("title") or r.get("chat") or "Sem título",
                "conteudo": r.get("conteudo") or r.get("content") or r.get("resumo") or "",
                "fonte": str(path.name),
            })
    return rows


def classify_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        c = classify_text(row.get("titulo", ""), row.get("conteudo", ""))
        out.append({"titulo_original": row.get("titulo", ""), "classificacao": c})
    return out


def write_index_csv(classified: list[dict[str, Any]], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["titulo_original", "codigo", "pasta_destino", "prioridade", "status", "titulo_sugerido", "proxima_acao"]
    with output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in classified:
            c = item["classificacao"]
            writer.writerow({
                "titulo_original": item["titulo_original"],
                "codigo": c["codigo"],
                "pasta_destino": c["pasta_destino"],
                "prioridade": c["prioridade"],
                "status": c["status_sugerido"],
                "titulo_sugerido": c["titulo_sugerido"],
                "proxima_acao": c["proxima_acao"],
            })
    return output


def create_readme_for_project(root: Path) -> Path:
    readme = root / "README_APLICACAO.md"
    readme.write_text(
        "# ChatGPT Projetos API\n\n"
        "API local para classificar chats e projetos por código BUI/MUS/LUT/CAR/PES/TEC/ADM, "
        "gerar árvore de pastas, índice CSV e preparar integração com GitHub.\n\n"
        "## Limite importante\n\n"
        "Esta API não renomeia a barra lateral do ChatGPT diretamente. Ela trabalha com exportação oficial "
        "do ChatGPT ou listas CSV, e gera títulos sugeridos, pastas e backlog.\n\n"
        f"Gerado em {datetime.now().isoformat(timespec='seconds')}.\n",
        encoding="utf-8",
    )
    return readme


def github_create_issue(repo: str, title: str, body: str, labels: list[str] | None = None) -> dict[str, Any]:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Defina GITHUB_TOKEN no ambiente antes de usar este endpoint.")
    url = f"https://api.github.com/repos/{repo}/issues"
    payload: dict[str, Any] = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    resp = requests.post(url, headers=_github_headers(token), json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def github_create_or_update_file(repo: str, path: str, content: str, message: str, branch: str | None = None) -> dict[str, Any]:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Defina GITHUB_TOKEN no ambiente antes de usar este endpoint.")
    import base64
    base_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    params = {"ref": branch} if branch else None
    get_resp = requests.get(base_url, headers=_github_headers(token), params=params, timeout=30)
    sha = None
    if get_resp.status_code == 200:
        sha = get_resp.json().get("sha")
    elif get_resp.status_code != 404:
        get_resp.raise_for_status()

    payload: dict[str, Any] = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
    }
    if sha:
        payload["sha"] = sha
    if branch:
        payload["branch"] = branch
    put_resp = requests.put(base_url, headers=_github_headers(token), json=payload, timeout=30)
    put_resp.raise_for_status()
    return put_resp.json()


def _github_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def zip_project(src: Path, zip_path: Path) -> Path:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in src.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(src.parent))
    return zip_path
