import streamlit as st
import pandas as pd
import plotly.express as px
from backend.carregador_dados import dados_vendas_cache

# Mapeamentos
MAPA_NOMES_CANAIS = {
    7: 'Presencial', 8: 'iFood', 9: 'Rappi',
    10: 'Uber Eats', 11: 'WhatsApp', 12: 'App Próprio'
}
MAPA_CORES_CANAIS = {
    'WhatsApp': '#25D366', 'iFood': '#EA1D2C', 'Rappi': '#FF5722',
    'Uber Eats': '#000000', 'App Próprio': '#3498DB', 'Presencial': '#7F8C8D'
}


def carregar_dados():
    df = dados_vendas_cache()
    df = df.copy()
    df.loc[:, 'sale_date'] = df['created_at'].dt.date
    return df[df['sale_status_desc'] == 'COMPLETED'].copy()

#filtro de data
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
    
    return df_filtrado


def calcular_kpis(df):
    faturamento = df['total_amount'].sum()
    vendas = len(df)
    ticket_medio = faturamento / vendas 
    
    return {'faturamento': faturamento, 'vendas': vendas, 'ticket_medio': ticket_medio}


def exibir_kpis(kpis):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Faturamento Total", f"R$ {kpis['faturamento']:,.2f}")
    with col2:
        st.metric("Total de Vendas", f"{kpis['vendas']:,}")
    with col3:
        st.metric("Ticket Médio", f"R$ {kpis['ticket_medio']:,.2f}")

# faturamento diário
def exibir_tendencia_faturamento(df):
    st.subheader("Faturamento Diário ao Longo do Tempo")
    
    df_tendencia = df.groupby('sale_date')['total_amount'].sum().reset_index(name='Faturamento')
    
    fig = px.line(df_tendencia, x='sale_date', y='Faturamento',
                  title='Tendência Diária da Rede', template='plotly_white')
    fig.update_yaxes(tickprefix='R$ ')
    st.plotly_chart(fig, use_container_width=True)

#horário de pico
def exibir_horario_pico(df):
    st.subheader("Horário de Pico de Vendas (Análise Operacional)")

    df_local = df.copy()
    df_local.loc[:, 'hora_venda'] = df_local['created_at'].dt.hour
    df_por_hora = df_local.groupby('hora_venda')['total_amount'].count().reset_index(name='Número de Vendas')
    
    fig = px.bar(df_por_hora, x='hora_venda', y='Número de Vendas',
                 title='Distribuição de Vendas por Hora do Dia', template='plotly_white')
    fig.update_xaxes(tick0=0, dtick=1, range=[-0.5, 23.5])
    st.plotly_chart(fig, use_container_width=True)

#distribuição por canal e estado
def exibir_distribuicao_canal_estado(df):
    st.subheader("Distribuição de Receita por Canal e Localidades")
    
    col_canais, col_estados = st.columns(2)
    
    with col_canais:
        st.markdown("##### Faturamento por Canal")
    
        # Agrupando por canal e somando o faturamento
        faturamento_canal = df.groupby('channel_name')['total_amount'].sum().reset_index()
        
        # Gráfico de pizza para a proporção do faturamento
        fig = px.pie(faturamento_canal, values='total_amount', names='channel_name',
                     title='Proporção do Faturamento por Canal',
                     color='channel_name',
                     color_discrete_map=MAPA_CORES_CANAIS,  # <-- APLICA O MAPA DE CORES
                     hole=0.5)
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col_estados:
        st.markdown("##### Faturamento por Estado (Top 5 + Outros)")
        df_estados = df.dropna(subset=['state']).groupby('state')['total_amount'].sum().reset_index(name='Faturamento')
        df_estados.rename(columns={'state': 'Estado'}, inplace=True) 
        
        df_top5 = df_estados.nlargest(5, 'Faturamento')
        estados_top5 = df_top5['Estado'].tolist()  
        
        faturamento_outros = df_estados[~df_estados['Estado'].isin(estados_top5)]['Faturamento'].sum()
        
        df_outros = pd.DataFrame([{'Estado': 'Outros Estados', 'Faturamento': faturamento_outros}])
        df_final_pizza = pd.concat([df_top5, df_outros], ignore_index=True)
        
        fig_estados = px.pie(df_final_pizza, names='Estado', values='Faturamento',
                             title='Proporção do Faturamento por Estado (Top 5)', hole=0.5,
                             template='plotly_white', height=450,
                             color_discrete_sequence=px.colors.qualitative.Bold)
        fig_estados.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_estados, use_container_width=True)



# Função para exibir tendência do ticket médio
def exibir_ticket_medio(df):
    st.subheader("Tendência Diária do Ticket Médio")
    
    df_ticket = df.groupby('sale_date').agg(
        Total_Faturamento=('total_amount', 'sum'),
        Total_Vendas=('sale_date', 'size')
    ).reset_index()
    df_ticket['Ticket Médio'] = df_ticket['Total_Faturamento'] / df_ticket['Total_Vendas']
    
    fig = px.line(df_ticket, x='sale_date', y='Ticket Médio',
                  title='Evolução do Ticket Médio no Período', template='plotly_white',
                  line_shape='spline', color_discrete_sequence=['#FF7F0E'])
    fig.update_yaxes(tickprefix='R$ ')
    st.plotly_chart(fig, use_container_width=True)

#app
def app():
    st.sidebar.header("Filtros de Análise")
    
    df = carregar_dados()
    df_final = aplicar_filtro_data(df)
    
    st.title("Performance Global da Marca")
    st.markdown("Análise de KPIs e Tendências de Vendas para toda a rede.")
    
    kpis = calcular_kpis(df_final)
    exibir_kpis(kpis)
    st.markdown("---")
    
    exibir_tendencia_faturamento(df_final)
    exibir_horario_pico(df_final)
    exibir_distribuicao_canal_estado(df_final)
    exibir_ticket_medio(df_final)
    st.markdown("---")

# Executa
if __name__ == "__main__":
    app()
