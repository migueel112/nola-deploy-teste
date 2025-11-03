import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go
from backend.carregador_dados import dados_vendas_cache

# Mapeamento
MAPA_NOMES_CANAIS = {
    7: 'Presencial', 8: 'iFood', 9: 'Rappi',
    10: 'Uber Eats', 11: 'WhatsApp', 12: 'App Próprio'
}
MAPA_CORES_CANAIS = {
    'WhatsApp': '#25D366', 'iFood': '#EA1D2C', 'Rappi': '#FF5722',
    'Uber Eats': '#000000', 'App Próprio': '#3498DB', 'Presencial': '#7F8C8D'
}
MAPA_DIAS_SEMANA = {
    0: 'Segunda', 1: 'Terça', 2: 'Quarta',
    3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'
}

def carregar_dados():
    df = dados_vendas_cache()
    df = df.copy()
    df.loc[:, 'sale_date'] = df['created_at'].dt.date
    return df[df['sale_status_desc'] == 'COMPLETED'].copy()


def aplicar_filtro_data(df):
    data_minima = df['sale_date'].min()
    data_maxima = df['sale_date'].max()
    
    periodo = st.sidebar.date_input(
        "Selecione o Período:",
        value=(data_minima, data_maxima),
        min_value=data_minima,
        max_value=data_maxima
    )
    
    if len(periodo) == 2:
        data_inicio, data_fim = periodo
        df_filtrado = df[(df['sale_date'] >= data_inicio) & (df['sale_date'] <= data_fim)].copy()
    else:
        df_filtrado = df.copy()
        data_inicio, data_fim = data_minima, data_maxima
    
    return df_filtrado, data_inicio, data_fim

# filtros de modo, estado e loja
def aplicar_filtros_unidade(df):
    st.sidebar.header("Modo de Análise")
    modo = st.sidebar.radio(
        "Selecione o foco da análise:",
        options=["Comparativo (Todas as Lojas)", "Unidade Única (Loja Detalhada)"],
        index=0
    )
    
    estado_sel = 'Todos os Estados'
    loja_sel = 'Todas as Lojas'
    titulo = "Comparativo de Performance e Ranking entre Unidades"
    
    if modo == "Unidade Única (Loja Detalhada)":
        st.sidebar.markdown("---")
        st.sidebar.subheader("Filtrar Unidade")
        
        estados = ['Todos os Estados'] + sorted(df['state'].dropna().unique())
        estado_sel = st.sidebar.selectbox("1. Filtrar por Estado:", options=estados)
        
        if estado_sel != 'Todos os Estados':
            lojas = df[df['state'] == estado_sel]['store_id'].unique()
            titulo = f"Performance do Estado: {estado_sel}"
        else:
            lojas = df['store_id'].unique()
        
        loja_sel = st.sidebar.selectbox("2. Selecione a Loja (ID):", options=['Selecione a Loja'] + sorted(lojas))
        
        if loja_sel != 'Selecione a Loja':
            df = df[df['store_id'] == loja_sel].copy()
            titulo = f"Performance Detalhada da Loja: ID {loja_sel}"
    
    return df, titulo


def calcular_kpis(df):
  
    faturamento = df['total_amount'].sum()
    vendas = len(df)
    ticket_medio = faturamento / vendas 
    
    return {'faturamento': faturamento, 'vendas': vendas, 'ticket_medio': ticket_medio}


def preparar_ranking_lojas(df):
    df_ranking = df.groupby(['store_id', 'store_name']).agg(
        Faturamento=('total_amount', 'sum'),
        Vendas=('store_id', 'size')
    ).reset_index()
    
    df_ranking['Loja'] = df_ranking['store_name'].fillna('Loja') + ' (ID ' + df_ranking['store_id'].astype(str) + ')'
    df_ranking['Ticket Médio'] = df_ranking['Faturamento'] / df_ranking['Vendas']
    df_ranking = df_ranking.sort_values('Faturamento', ascending=False).reset_index(drop=True)
    df_ranking['Rank'] = range(1, len(df_ranking) + 1)
    
    return df_ranking


def exibir_kpis(kpis):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Faturamento Total", f"R$ {kpis['faturamento']:,.2f}")
    with col2:
        st.metric("Total de Vendas", f"{kpis['vendas']:,}")
    with col3:
        st.metric("Ticket Médio", f"R$ {kpis['ticket_medio']:,.2f}")

#(top/bottom 10)
def exibir_ranking_lojas(df_ranking):
    st.header("Top 10 Melhores Lojas (Faturamento)")
    df_top10 = df_ranking.head(10).sort_values('Faturamento', ascending=True)
    
    fig_top = px.bar(df_top10, x='Faturamento', y='Loja', orientation='h',
                     title='Faturamento das Top 10 Melhores Lojas', color_discrete_sequence=['#1F77B4'])
    fig_top.update_xaxes(tickprefix="R$ ")
    st.plotly_chart(fig_top, use_container_width=True)
    
    st.markdown("---")
    st.header("Top 10 Piores Lojas (Faturamento)")
    df_bottom10 = df_ranking.nsmallest(10, 'Faturamento').sort_values('Faturamento', ascending=False)
    
    fig_bottom = px.bar(df_bottom10, x='Faturamento', y='Loja', orientation='h',
                        title='Faturamento das 10 Piores Lojas', color_discrete_sequence=["#b92020"])
    fig_bottom.update_xaxes(tickprefix="R$ ")
    st.plotly_chart(fig_bottom, use_container_width=True)

#análise detalhada de unidade
def exibir_analise_unidade(df):
    df = df.copy()
    st.header("KPIs Principais")
    
    
    st.subheader("Evolução Diária do Faturamento e do Ticket Médio")
    
    df_fat = df.groupby('sale_date')['total_amount'].sum().reset_index(name='Faturamento')
    fig_fat = px.line(df_fat, x='sale_date', y='Faturamento', title='Tendência de Faturamento',
                      line_shape='spline', color_discrete_sequence=['#4A148C'])
    fig_fat.update_yaxes(tickprefix='R$ ')
    st.plotly_chart(fig_fat, use_container_width=True)
    
    df_ticket = df.groupby('sale_date').agg(
        Total_Faturamento=('total_amount', 'sum'),
        Total_Vendas=('sale_date', 'size')
    ).reset_index()
    df_ticket['Ticket Médio'] = df_ticket['Total_Faturamento'] / df_ticket['Total_Vendas']
    
    fig_ticket = px.line(df_ticket, x='sale_date', y='Ticket Médio', title='Evolução do Ticket Médio',
                         line_shape='spline', color_discrete_sequence=['#FF7F0E'])
    fig_ticket.update_yaxes(tickprefix='R$ ')
    st.plotly_chart(fig_ticket, use_container_width=True)
    
    st.markdown("---")
    
    #canais
    st.subheader("Distribuição do Mix de Vendas")
    df_canais = df.groupby('channel_id')['total_amount'].sum().reset_index(name='Faturamento')
    df_canais['Nome do Canal'] = df_canais['channel_id'].map(MAPA_NOMES_CANAIS)
    
    fig_canais = px.pie(df_canais, names='Nome do Canal', values='Faturamento',
                        title='Proporção de Faturamento por Canal', hole=0.5,
                        color='Nome do Canal', color_discrete_map=MAPA_CORES_CANAIS)
    fig_canais.update_traces(textinfo='percent+label')
    st.plotly_chart(fig_canais, use_container_width=True)
    
    st.markdown("---")
    
    # dia da semana
    st.subheader("Sazonalidade: Faturamento por Dia da Semana")
    df.loc[:, 'day_of_week'] = df['created_at'].dt.dayofweek
    df.loc[:, 'Dia da Semana'] = df['day_of_week'].map(MAPA_DIAS_SEMANA)
    
    df_sazonal = df.groupby('Dia da Semana')['total_amount'].sum().reset_index(name='Faturamento')
    df_sazonal['Dia da Semana'] = pd.Categorical(df_sazonal['Dia da Semana'], categories=list(MAPA_DIAS_SEMANA.values()), ordered=True)
    df_sazonal = df_sazonal.sort_values('Dia da Semana')
    
    fig_dias = px.bar(df_sazonal, x='Dia da Semana', y='Faturamento',
                      title='Faturamento por Dia da Semana', color_discrete_sequence=['#2C3E50'])
    fig_dias.update_yaxes(tickprefix='R$ ')
    st.plotly_chart(fig_dias, use_container_width=True)


def app():
    st.sidebar.header("Filtros de Análise")
    
    df = carregar_dados()
    df_filtrado_data, _, _ = aplicar_filtro_data(df)
    df_final, titulo_analise = aplicar_filtros_unidade(df_filtrado_data)
    
    st.sidebar.markdown("---")
    st.title("Análise de Performance por Unidade")
    st.subheader(titulo_analise)
    
    kpis = calcular_kpis(df_final)
    exibir_kpis(kpis)
    st.markdown("---")
    
    if "Comparativo" in titulo_analise or "Rede Total" in titulo_analise:
        df_ranking = preparar_ranking_lojas(df_final)
        exibir_ranking_lojas(df_ranking)
    else:
        exibir_analise_unidade(df_final)


if __name__ == "__main__":
    app()
