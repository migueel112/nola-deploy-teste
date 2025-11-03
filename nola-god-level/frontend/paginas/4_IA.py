import json
import os
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
from backend.carregador_dados import dados_vendas_cache, dados_itens_cache
from backend.logica_IA import gerar_contexto_analise, SCHEMA_DB_DESCRIPTION
load_dotenv()


def app():
    st.title("Assistente de Análise Estratégica com IA")
    st.markdown("Use o assistente para insights em vendas, CRM e marketing, com Gemini e busca Google.")
    st.markdown("---")

    GEMINI_MODEL = "gemini-2.5-flash-preview-09-2025"
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        st.error("Configure a variável de ambiente GEMINI_API_KEY no arquivo .env antes de usar o assistente.")
        st.stop()

    if "messages_ia" not in st.session_state:
        st.session_state.messages_ia = []

    df_vendas = dados_vendas_cache()
    if df_vendas.empty:
        return
    df_vendas['sale_date'] = pd.to_datetime(df_vendas['created_at']).dt.date
    df_vendas_concluidas = df_vendas[df_vendas['sale_status_desc'] == 'COMPLETED']

    df_itens = dados_itens_cache()
    df_itens_concluidos = df_itens[df_itens['sale_status_desc'] == 'COMPLETED']

    data_minima, data_maxima = df_vendas_concluidas['sale_date'].min(), df_vendas_concluidas['sale_date'].max()
    periodo_selecionado = st.sidebar.date_input(
        "Período para Contexto da IA:",
        (data_minima, data_maxima),
        data_minima,
        data_maxima,
        key="ia_periodo",
    )
    data_inicio_ia, data_fim_ia = (
        periodo_selecionado if len(periodo_selecionado) == 2 else (data_minima, data_maxima)
    )

    def get_gemini_response(prompt, context_data_dict):
        context_json = json.dumps(context_data_dict, indent=2)
        system_instruction = f"""
        Você é um Analista de Marketing e CRM Estratégico sênior. Analise os dados fornecidos e responda em português, profissionalmente.
        Use busca Google para tendências. Mantenha respostas concisas e focadas em crescimento.
        Schema: {SCHEMA_DB_DESCRIPTION}
        Contexto: {context_json}
        """

        contents = [
            {"role": msg["role"], "parts": [{"text": str(msg["content"])}]}
            for msg in st.session_state.messages_ia
        ]
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "tools": [{"google_search": {}}],
            "systemInstruction": {"parts": [{"text": system_instruction}]},
        }

        response = requests.post(
            f"{API_URL}?key={api_key}",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload),
        )
        response.raise_for_status()
        result = response.json()
        text = result['candidates'][0]['content']['parts'][0]['text']
        sources = result['candidates'][0].get('groundingMetadata', {}).get('groundingAttributions', [])
        return text, sources

    for message in st.session_state.messages_ia:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Pergunte sobre vendas, CRM ou marketing..."):
        st.session_state.messages_ia.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner(
            f"Calculando KPIs para {data_inicio_ia.strftime('%d/%m/%Y')} a {data_fim_ia.strftime('%d/%m/%Y')}..."
        ):
            context_json = gerar_contexto_analise(
                df_vendas_concluidas, df_itens_concluidos, data_inicio_ia, data_fim_ia
            )
            context_data = json.loads(context_json)

        with st.chat_message("model"):
            with st.spinner("Gerando análise com Gemini..."):
                response_text, sources = get_gemini_response(prompt, context_data)
                full_response = response_text
                if sources:
                    full_response += "\n\n---\n**Referências:**\n" + "\n".join(
                        f"- [{s['web']['title']}]({s['web']['uri']})" for s in sources if s.get('web')
                    )
                st.markdown(full_response)
                st.session_state.messages_ia.append({"role": "model", "content": full_response})
