import streamlit as st
from pathlib import Path
import importlib.util
from dotenv import load_dotenv


import sys
import os

# garante que a raiz do repo esteja no sys.path para permitir "import backend"
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

# carrega .env (tenta python-dotenv, senão faz parsing simples)
env_path = repo_root / ".env"
if env_path.exists():
    try:
        load_dotenv(env_path)
    except Exception:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k.strip(), v)



st.set_page_config(page_title="God-Level", layout="wide")

dir_paginas = Path(__file__).parent / "paginas"

paginas = {
    "Marca": dir_paginas / "1_Marca.py",
    "Lojas": dir_paginas / "2_Lojas.py",
    "Clientes": dir_paginas / "3_Clientes.py",
    "Assistente": dir_paginas / "4_IA.py",
}


def carregar(caminho: Path):
    spec = importlib.util.spec_from_file_location(f"paginas.{caminho.stem}", str(caminho))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():

    menu = [
        ("🏠 Marca", "Marca"),
        ("🏬 Lojas", "Lojas"),
        ("👥 Clientes", "Clientes"),
        ("🤖 Assistente", "Assistente")
    ]
    labels = [m[0] for m in menu]
    sel = st.sidebar.radio("Escolha a página:", labels, label_visibility="collapsed")
    mapa = {m[0]: m[1] for m in menu}
    chave = mapa[sel]
    mod = carregar(paginas[chave])
    mod.app()
    


if __name__ == "__main__":
    main()