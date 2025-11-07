import pandas as pd
from sqlalchemy import text
from .db_config import get_db_engine
import streamlit as st

ENGINE = get_db_engine()

DADOS_VENDAS = """
    SELECT
        s.id,
        s.store_id,
        st.name AS store_name,
        st.city,
        st.state,
        s.channel_id,
        c.name AS channel_name,
        s.created_at,
        s.sale_status_desc,
        s.total_amount,
        s.total_discount,
        s.delivery_fee,
        s.customer_id AS customer_id,
        COALESCE(cust.customer_name, s.customer_name) AS customer_name,
        cust.phone_number AS customer_phone,
        st.sub_brand_id AS sub_brand_id, -- <<< ALTERAÇÃO 1: Mude de 's' para 'st'
        sb.name AS sub_brand_name
    FROM
        sales s
    JOIN
        stores st ON s.store_id = st.id
    LEFT JOIN
        channels c ON s.channel_id = c.id
    LEFT JOIN
        sub_brands sb ON st.sub_brand_id = sb.id -- <<< ALTERAÇÃO 2: Mude de 's' para 'st'
    LEFT JOIN
        customers cust ON s.customer_id = cust.id;
"""

DADOS_ITENS = """
SELECT
    ps.sale_id,
    ps.product_id,
    p.name AS product_name,
    ps.quantity,
    ps.total_price AS item_total_amount,
    s.sale_status_desc,
    s.created_at AS sale_date,
    p.sub_brand_id,
    sb.name AS product_sub_brand_name
FROM
    product_sales ps
JOIN
    products p ON ps.product_id = p.id
JOIN
    sales s ON ps.sale_id = s.id
LEFT JOIN
    sub_brands sb ON p.sub_brand_id = sb.id
"""


@st.cache_data(ttl=600)
def dados_vendas_cache():
    df = pd.read_sql_query(sql=text(DADOS_VENDAS), con=ENGINE)
    print(f"Dados carregados: {len(df)} linhas de vendas.")
    return df


@st.cache_data(ttl=600)
def dados_itens_cache():
    df = pd.read_sql_query(sql=text(DADOS_ITENS), con=ENGINE)
    print(f"Dados carregados: {len(df)} linhas de itens.")
    return df

