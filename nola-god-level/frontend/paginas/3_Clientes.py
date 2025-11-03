import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from backend.carregador_dados import dados_vendas_cache



def carregar_dados():
    df = dados_vendas_cache()
    df = df.copy()
    df.loc[:, 'sale_date'] = df['created_at'].dt.date
    return df[df['sale_status_desc'] == 'COMPLETED'].copy()


def aplicar_filtros(df):
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

# Função para calcular métricas de clientes
def calcular_metricas_clientes(df, data_inicio, data_fim):
    # primeira compra global
    df_primeira_compra = (
        df.dropna(subset=['customer_id'])
        .groupby('customer_id')['sale_date']
        .min()
        .reset_index(name='primeira_compra_global')
    )
    
  
    df = pd.merge(df, df_primeira_compra, on='customer_id', how='left')
    df['Status_Cadastro'] = np.where(
        df['customer_id'].notna(),
        'Com Cadastro (Identificado)',
        'Sem Cadastro (Não Identificado)'
    )
    
    is_identified = df['customer_id'].notna()
    is_new = (
        (df['primeira_compra_global'] >= data_inicio) &
        (df['primeira_compra_global'] <= data_fim) &
        is_identified
    )
    is_first_purchase = df['sale_date'] == df['primeira_compra_global']
    
    df['Tipo_Cliente'] = np.select(
        [is_identified & is_first_purchase, is_identified],
        ['Novo', 'Recorrente'],
        default='N/A'
    )
    
    return df

# Função para calcular KPIs
def calcular_kpis(df):
    total_transacoes = len(df)
    total_faturamento = df['total_amount'].sum()
    aov = total_faturamento / total_transacoes
    
    df_identificados = df[df['Status_Cadastro'] == 'Com Cadastro (Identificado)']
    clientes_unicos = df_identificados['customer_id'].nunique()
    
    
    pedidos_por_cliente = df_identificados.groupby('customer_id').size()
    clientes_recorrentes = (pedidos_por_cliente > 1).sum()
    taxa_recompra = (clientes_recorrentes / clientes_unicos) * 100
   
    
    vendas_sem_cadastro = len(df[df['Status_Cadastro'] == 'Sem Cadastro (Não Identificado)'])
    
    return {
        'total_transacoes': total_transacoes,
        'total_faturamento': total_faturamento,
        'aov': aov,
        'clientes_unicos': clientes_unicos,
        'taxa_recompra': taxa_recompra,
        'vendas_sem_cadastro': vendas_sem_cadastro,
        'df_identificados': df_identificados
    }


def exibir_kpis_e_distribuicao(df, kpis):
    st.header("1. KPIs Estratégicos")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Clientes Únicos (Identificados)", f"{kpis['clientes_unicos']:,}")
    with col2:
        st.metric("Taxa de Recompra (Identificados)", f"{kpis['taxa_recompra']:.1f}%")
    with col3:
        st.metric("Valor Médio de Transação (AOV)", f"R$ {kpis['aov']:.2f}")
    
    #cadastros
    df_cadastro = df.groupby('Status_Cadastro').size().reset_index(name='Pedidos')
    
    col_kpis, col_grafico = st.columns([1, 1])
    with col_kpis:
        st.metric("Vendas Com Cadastro", f"{len(kpis['df_identificados']):,}")
        st.metric("Vendas Sem Cadastro", f"{kpis['vendas_sem_cadastro']:,}")
        percentual = (len(kpis['df_identificados']) / kpis['total_transacoes']) * 100 if kpis['total_transacoes'] > 0 else 0
        st.metric("% Vendas Identificadas", f"{percentual:.1f}%")
    
    with col_grafico:
        fig = px.pie(
            df_cadastro, values='Pedidos', names='Status_Cadastro',
            title='Distribuição de Vendas por Status de Cadastro',
            hole=0.3, color_discrete_map={'Com Cadastro (Identificado)': '#4A148C', 'Sem Cadastro (Não Identificado)': '#F97316'}
        )
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

#retenção
def exibir_analise_retencao(df):
    st.header("2. Análise de Retenção e Aquisição")
    
    df_retencao = df[df['Tipo_Cliente'] != 'N/A']
    
    df_fat = df_retencao.groupby('Tipo_Cliente')['total_amount'].sum().reset_index(name='Faturamento')
    df_ped = df_retencao.groupby('Tipo_Cliente').size().reset_index(name='Pedidos')
    
    col1, col2 = st.columns(2)
    with col1:
        fig_fat = px.bar(df_fat, x='Tipo_Cliente', y='Faturamento', color='Tipo_Cliente',
                         title='Faturamento: Novos vs. Recorrentes', color_discrete_map={'Novo': '#3498DB', 'Recorrente': '#4A148C'})
        fig_fat.update_yaxes(tickprefix='R$ ')
        st.plotly_chart(fig_fat, use_container_width=True)
    
    with col2:
        fig_ped = px.bar(df_ped, x='Tipo_Cliente', y='Pedidos', color='Tipo_Cliente',
                         title='Pedidos: Novos vs. Recorrentes', color_discrete_map={'Novo': '#3498DB', 'Recorrente': '#4A148C'})
        st.plotly_chart(fig_ped, use_container_width=True)

#curva de lealdade e top clientes
def exibir_curva_e_top_clientes(df):
    st.header("3. Curva de Lealdade e Clientes de Alto Valor")
    
    df_trabalho = df.copy()
    df_frequencia = df_trabalho.groupby('customer_id').size().reset_index(name='Contagem_Pedidos')
    bins = [0, 1, 2, 3, 5, df_frequencia['Contagem_Pedidos'].max() + 1]
    labels = ['<1 Compra', '1 Compra', '2 Compras', '3 a 5 Compras', '5+ Compras']
    
    df_frequencia['Faixa'] = pd.cut(df_frequencia['Contagem_Pedidos'], bins=bins, labels=labels, right=False)
    df_curva = df_frequencia.groupby('Faixa', observed=True).size().reset_index(name='Clientes')
    
    fig_curva = px.bar(df_curva, x='Faixa', y='Clientes', title='Distribuição de Clientes por Frequência')
    st.plotly_chart(fig_curva, use_container_width=True)
    
    df_identificados = df_trabalho[df_trabalho['customer_id'].notna()].copy()
    df_identificados[['customer_name', 'customer_phone']] = df_identificados[['customer_name', 'customer_phone']].fillna({
    'customer_name': 'Sem cadastro',
    'customer_phone': 'Não informado'
    })
# Agrupar por cliente, somar gastos e obter top 10
    df_top10 = (
        df_identificados
        .groupby(['customer_id', 'customer_name', 'customer_phone'])['total_amount']
        .sum()
        .reset_index(name='Gasto Total')
        .sort_values('Gasto Total', ascending=False)
        .head(10)
    )
    
    df_top10 = df_top10.rename(columns={
        'customer_id': 'ID Cliente',
        'customer_name': 'Nome',
        'customer_phone': 'Telefone'
    })
    df_top10['Gasto Total (R$)'] = df_top10['Gasto Total'].map('R$ {:,.2f}'.format)
    df_top10 = df_top10.drop(columns=['Gasto Total'])
    # Exibir no Streamlit
    st.subheader("Top 10 Clientes por Faturamento")
    st.dataframe(df_top10, use_container_width=True, hide_index=True)

    
    
def app():
    st.sidebar.header("Filtros de Análise")
    
    df = carregar_dados()
    df_filtrado, data_inicio, data_fim = aplicar_filtros(df)
    
    st.title("Análise e Segmentação de Clientes (CRM)")
    st.subheader(f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    st.markdown("---")
    
    df_com_metricas = calcular_metricas_clientes(df_filtrado, data_inicio, data_fim)
    kpis = calcular_kpis(df_com_metricas)
    
    exibir_kpis_e_distribuicao(df_com_metricas, kpis)
    st.markdown("---")
    exibir_analise_retencao(df_com_metricas)
    st.markdown("---")
    exibir_curva_e_top_clientes(df_com_metricas[df_com_metricas['Tipo_Cliente'] != 'N/A'])


if __name__ == "__main__":
    app()
