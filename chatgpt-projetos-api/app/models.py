from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

Status = Literal["Ativo", "Aguardando", "Concluído", "Arquivado"]


class ChatEntrada(BaseModel):
    titulo: str = Field(..., examples=["Alvarás Sanitários Caucaia"])
    conteudo: str = Field("", description="Texto, resumo ou corpo do chat")
    fonte: str | None = Field(None, description="Origem: export ChatGPT, CSV, manual etc.")


class Classificacao(BaseModel):
    codigo: str
    nome: str
    pasta_destino: str
    prioridade: str
    score: int
    status_sugerido: Status
    titulo_sugerido: str
    proxima_acao: str
    justificativa: str


class ChatClassificado(BaseModel):
    titulo_original: str
    classificacao: Classificacao


class ImportacaoResultado(BaseModel):
    total: int
    classificados: list[ChatClassificado]


class EstruturaResultado(BaseModel):
    raiz: str
    pastas_criadas: list[str]


class GitHubIssueRequest(BaseModel):
    repository_full_name: str = Field(..., examples=["diogonb1/testes-diogo"])
    titulo: str
    corpo: str
    labels: list[str] = Field(default_factory=list)


class GitHubFileRequest(BaseModel):
    repository_full_name: str = Field(..., examples=["diogonb1/testes-diogo"])
    path: str = Field(..., examples=["docs/indice.md"])
    content: str
    message: str = "docs: adiciona organização de projetos ChatGPT"
    branch: str | None = None


class ExportRow(BaseModel):
    titulo_original: str
    codigo: str
    pasta_destino: str
    prioridade: str
    status: str
    titulo_sugerido: str
    proxima_acao: str
