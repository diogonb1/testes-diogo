#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from app.services import classify_rows, create_readme_for_project, create_structure, import_chatgpt_json, import_csv, write_index_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Classifica exportação do ChatGPT ou CSV por projeto+entrega.")
    parser.add_argument("entrada", help="Arquivo conversations.json ou CSV com coluna titulo")
    parser.add_argument("--saida", default="ChatGPT_Projetos_Aplicado_API", help="Pasta de saída")
    args = parser.parse_args()

    entrada = Path(args.entrada)
    saida = Path(args.saida)
    if entrada.suffix.lower() == ".json":
        rows = import_chatgpt_json(entrada)
    elif entrada.suffix.lower() == ".csv":
        rows = import_csv(entrada)
    else:
        raise SystemExit("Use .json ou .csv")

    classified = classify_rows(rows)
    create_structure(saida)
    create_readme_for_project(saida)
    write_index_csv(classified, saida / "Indice_Chats_Reclassificados.csv")
    print(f"OK: {len(classified)} chats classificados em {saida}")


if __name__ == "__main__":
    main()
