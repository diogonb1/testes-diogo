#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from app.services import github_create_or_update_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Publica um arquivo no GitHub usando GITHUB_TOKEN.")
    parser.add_argument("repo", help="Ex.: diogonb1/testes-diogo")
    parser.add_argument("arquivo_local")
    parser.add_argument("path_repo", help="Ex.: docs/Indice_Chats_Reclassificados.csv")
    parser.add_argument("--branch", default=None)
    args = parser.parse_args()

    content = Path(args.arquivo_local).read_text(encoding="utf-8")
    result = github_create_or_update_file(
        args.repo,
        args.path_repo,
        content,
        "docs: publica índice de projetos ChatGPT",
        args.branch,
    )
    print(result.get("content", {}).get("html_url") or result)


if __name__ == "__main__":
    main()
