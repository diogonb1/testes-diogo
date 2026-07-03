from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

import yaml

DEFAULT_RULES_PATH = Path(__file__).resolve().parents[1] / "data" / "regras_projetos.yaml"


def normalize(text: str) -> str:
    text = text or ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\-\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_rules(path: Path = DEFAULT_RULES_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def score_project(text: str, words: list[str]) -> int:
    norm = normalize(text)
    score = 0
    for word in words:
        w = normalize(word)
        if not w:
            continue
        if " " in w:
            if w in norm:
                score += 3
        else:
            # Evita falso positivo de termos curtos, como "nr" dentro de "Henri".
            if re.search(rf"\b{re.escape(w)}\b", norm):
                score += 1
    return score


def critical_override(text: str) -> str | None:
    norm = normalize(text)
    overrides = [
        ("BUI-002", ["jde", "kdp", "safefood", "exh-002", "exh002", "l262"]),
        ("BUI-003", ["chep", "mychep"]),
        ("BUI-004", ["alvara", "alvaras", "avcb", "sanitario", "sanitarios", "ambiental", "rpca", "geo"]),
        ("BUI-005", ["pgr", "pcmso", "cipa", "brigada", "tst"]),
        ("LUT-001", ["giannini", "gianini", "mastersonic", "master sonic"]),
        ("LUT-004", ["fishman", "b-band", "b band", "rmc", "lr baggs"]),
        ("MUS-004", ["yamaha", "tensor", "hh", "caixa de som", "caixas de som", "pa pagode"]),
        ("CAR-004", ["lebesgue", "calculo", "integral"]),
    ]
    for code, terms in overrides:
        for term in terms:
            t = normalize(term)
            if " " in t:
                if t in norm:
                    return code
            elif re.search(rf"\b{re.escape(t)}\b", norm):
                return code
    return None


def classify_text(title: str, content: str = "") -> dict[str, Any]:
    rules = load_rules()
    text = f"{title}\n{content}"
    override_code = critical_override(text)
    best_code = override_code or "ADM-001"
    best_score = -1
    best_data: dict[str, Any] | None = None

    if override_code:
        best_data = rules["projetos"][override_code]
        best_score = max(5, score_project(text, best_data.get("palavras", [])))
    else:
        for code, data in rules["projetos"].items():
            score = score_project(text, data.get("palavras", []))
            if score > best_score:
                best_code = code
                best_score = score
                best_data = data

        if best_score <= 0:
            best_code = "ADM-001"
            best_data = rules["projetos"][best_code]
            best_score = 0

    assert best_data is not None
    prioridade = best_data.get("prioridade", "Media")
    status = "Ativo" if prioridade in {"Alta", "Media"} else "Aguardando"
    titulo_sugerido = f"[{best_code}] {best_data['nome']} — Entrega principal"
    proxima = suggest_next_action(best_code, best_data["nome"])
    return {
        "codigo": best_code,
        "nome": best_data["nome"],
        "pasta_destino": best_data["pasta"],
        "prioridade": prioridade,
        "score": best_score,
        "status_sugerido": status,
        "titulo_sugerido": titulo_sugerido,
        "proxima_acao": proxima,
        "justificativa": f"Classificação por palavras-chave e regra de projeto+entrega. Score={best_score}.",
    }


def suggest_next_action(code: str, name: str) -> str:
    if code.startswith("BUI-"):
        return "Montar matriz de pendências, responsáveis, evidências e prazo."
    if code.startswith("LUT-"):
        return "Consolidar componentes, medidas reais, diagrama e teste necessário."
    if code.startswith("MUS-"):
        return "Separar referência técnica, objetivo de uso, orçamento e decisão de compra/execução."
    if code.startswith("CAR-"):
        return "Consolidar versão final, requisito da vaga/disciplina e entrega pendente."
    if code.startswith("PES-"):
        return "Separar decisão pessoal, orçamento, riscos e próxima ação prática."
    if code.startswith("TEC-"):
        return "Consolidar arquivos-fonte, erro atual, versão e teste de validação."
    return "Atualizar ficha do projeto e definir uma única próxima ação."
