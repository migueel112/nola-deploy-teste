import streamlit as st
from pathlib import Path
import importlib.util

st.set_page_config(page_title="God-Level", layout="wide")

dir_paginas = Path(__file__).parent / "paginas"

paginas = {
    "Marca": dir_paginas / "1_Marca.py",
    "Lojas": dir_paginas / "2_Lojas.py",
    "Clientes": dir_paginas / "3_Clientes.py",
    "Assistente": dir_paginas / "4_IA.py",
}


def carregar(caminho: Path):
    spec = importlib.util.spec_from_file_location(caminho.stem, str(caminho))
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
