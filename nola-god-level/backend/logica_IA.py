import pandas as pd
import json

# Descrição do schema do banco de dados (contexto para IA)
SCHEMA_DB_DESCRIPTION = """
A base de dados inclui tabelas como 'sales', 'product_sales', 'products', etc., relacionadas por IDs.
Foco em vendas e produtos para análises.
"""

def _filtrar_por_periodo(df, data_inicio, data_fim, coluna_data='sale_date'):
    """Filtra DataFrame por período de datas."""
    df[coluna_data] = pd.to_datetime(df[coluna_data]).dt.date
    return df[(df[coluna_data] >= data_inicio) & (df[coluna_data] <= data_fim)].copy()

def _calcular_kpis_gerais(df_vendas):
    """Calcula KPIs gerais: faturamento, transações e ticket médio."""
    total_faturamento = df_vendas['total_amount'].sum()
    total_transacoes = len(df_vendas)
    aov = total_faturamento / total_transacoes if total_transacoes > 0 else 0
    return total_faturamento, total_transacoes, aov

def _analisar_clientes(df_vendas, df_vendas_concluidas):
    """Analisa clientes: novos, recorrentes e não identificados."""
    df_primeira_compra = df_vendas.dropna(subset=['customer_id']).groupby('customer_id')['sale_date'].min().reset_index()
    df_primeira_compra.rename(columns={'sale_date': 'primeira_compra_global'}, inplace=True)
    
    df_temp = pd.merge(df_vendas_concluidas, df_primeira_compra, on='customer_id', how='left')
    is_identified = df_temp['customer_id'].notna()
    is_first = (df_temp['sale_date'] == df_temp['primeira_compra_global']) & is_identified
    
    pedidos_novo = is_first.sum()
    pedidos_recorrente = (is_identified & ~is_first).sum()
    vendas_identificadas = pedidos_novo + pedidos_recorrente
    pedidos_nao_identificados = (~is_identified).sum()
    pct_identificados = (vendas_identificadas / len(df_temp)) * 100 if len(df_temp) > 0 else 0
    
    return pedidos_novo, pedidos_recorrente, pct_identificados, pedidos_nao_identificados

def _analisar_lojas(df_vendas):
    """Analisa performance de lojas: top e piores 5."""
    df_lojas = df_vendas.groupby('store_id')['total_amount'].sum().reset_index()
    top_5 = df_lojas.nlargest(5, 'total_amount').to_dict('records')
    bottom_5 = df_lojas.nsmallest(5, 'total_amount').to_dict('records')
    return top_5, bottom_5

def _analisar_produtos(df_itens):
    """Analisa produtos: top/bottom por quantidade e faturamento."""
    df_qnt = df_itens.groupby(['product_id', 'product_name'])['quantity'].sum().reset_index()
    top_qnt = df_qnt.nlargest(5, 'quantity').to_dict('records')
    bottom_qnt = df_qnt.nsmallest(5, 'quantity').to_dict('records')
    
    df_fat = df_itens.groupby(['product_id', 'product_name'])['item_total_amount'].sum().reset_index()
    top_fat = df_fat.nlargest(5, 'item_total_amount').to_dict('records')
    bottom_fat = df_fat.nsmallest(5, 'item_total_amount').to_dict('records')
    
    return top_qnt, bottom_qnt, top_fat, bottom_fat

def _analisar_canais(df_vendas):
    """Analisa canais de venda: faturamento e percentuais."""
    df_canais = df_vendas.groupby(['channel_id', 'channel_name']).agg(
        Nro_Vendas=('id', 'nunique'),
        Faturamento_Total=('total_amount', 'sum')
    ).reset_index()
    
    total_faturamento = df_canais['Faturamento_Total'].sum()
    df_canais['Percentual_Faturamento'] = (df_canais['Faturamento_Total'] / total_faturamento * 100).round(2) if total_faturamento > 0 else 0
    top_canais = df_canais.nlargest(7, 'Faturamento_Total').rename(columns={
        'channel_id': 'Canal_ID', 'channel_name': 'Canal_Nome'
    }).to_dict('records')
    
    return total_faturamento, top_canais

def gerar_contexto_analise(df_vendas, df_itens, data_inicio, data_fim):
    """
    Gera contexto JSON estruturado para IA a partir de DataFrames de vendas e itens.
    
    Args:
        df_vendas (pd.DataFrame): DataFrame de vendas.
        df_itens (pd.DataFrame): DataFrame de itens.
        data_inicio (date): Data de início.
        data_fim (date): Data de fim.
    
    Returns:
        str: JSON com KPIs e análises.
    """
    df_vendas_concluidas = df_vendas[df_vendas['sale_status_desc'] == 'COMPLETED'].copy()
    df_itens_final = _filtrar_por_periodo(df_itens, data_inicio, data_fim)
    
    total_faturamento, total_transacoes, aov = _calcular_kpis_gerais(df_vendas_concluidas)
    pedidos_novo, pedidos_recorrente, pct_identificados, pedidos_nao_identificados = _analisar_clientes(df_vendas, df_vendas_concluidas)
    top_lojas, bottom_lojas = _analisar_lojas(df_vendas_concluidas)
    top_qnt, bottom_qnt, top_fat, bottom_fat = _analisar_produtos(df_itens_final)
    total_fat_canais, top_canais = _analisar_canais(df_vendas_concluidas)
    
    contexto = {
        "Periodo_Analise": f"De {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}",
        "KPIs_Gerais": {
            "Total_Faturamento": f"R$ {total_faturamento:,.2f}",
            "Total_Pedidos": f"{total_transacoes:,}",
            "Ticket_Medio": f"R$ {aov:,.2f}",
        },
        "Analise_Clientes": {
            "Pedidos_Novo": f"{pedidos_novo:,}",
            "Pedidos_Recorrente": f"{pedidos_recorrente:,}",
            "Pct_Pedidos_Identificados": f"{pct_identificados:.1f}%",
            "Pedidos_Nao_Identificados": f"{pedidos_nao_identificados:,}"
        },
        "Lojas_Performance": {
            "Top_5_Lojas": top_lojas,
            "Piores_5_Lojas": bottom_lojas
        },
        "Produtos_Performance": {
            "Top_5_Quantidade": top_qnt,
            "Top_5_Faturamento": top_fat,
            "Bottom_5_Quantidade": bottom_qnt,
            "Bottom_5_Faturamento": bottom_fat
        },
        "Analise_Canais_de_Venda": {
            "Total_Faturamento_Geral_Periodo": round(total_fat_canais, 2),
            "Top_Canais_por_Faturamento": top_canais
        }
    }
    return json.dumps(contexto, indent=2, ensure_ascii=False)