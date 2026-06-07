from __future__ import annotations

import os
import uuid
from typing import Any

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()

PAGE_TITLE = "Future AI Agent"
DEFAULT_API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000")


st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon="📦",
    layout="wide",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .main { background: #f7faf9; }
        .metric-card {
            background: #ffffff;
            border: 1px solid #dbe5ec;
            border-left: 5px solid #0f766e;
            border-radius: 8px;
            padding: 16px 18px;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
            min-height: 108px;
        }
        .metric-label {
            color: #64748b;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: .04em;
            text-transform: uppercase;
        }
        .metric-value {
            color: #0f172a;
            font-size: 28px;
            font-weight: 800;
            line-height: 1.2;
            margin-top: 8px;
        }
        .metric-help {
            color: #64748b;
            font-size: 13px;
            margin-top: 4px;
        }
        .section-card {
            background: #ffffff;
            border: 1px solid #dbe5ec;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
        }
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            background: #ccfbf1;
            color: #0f766e;
            font-size: 12px;
            font-weight: 700;
            margin-bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_products_collection():
    mongo_uri = os.getenv("MONGO_READ_URI")
    db_name = os.getenv("MONGO_DB_NAME")
    collection_name = os.getenv("MONGO_PRODUCTS_COLLECTION")

    if not mongo_uri or not db_name or not collection_name:
        raise RuntimeError(
            "Configure MONGO_READ_URI, MONGO_DB_NAME e "
            "MONGO_PRODUCTS_COLLECTION no .env."
        )

    client = MongoClient(mongo_uri)
    return client[db_name][collection_name]


@st.cache_data(ttl=60)
def load_products() -> pd.DataFrame:
    collection = get_products_collection()
    docs = list(collection.find({}, {"_id": 0}))

    if not docs:
        return pd.DataFrame()

    df = pd.DataFrame(docs)

    for column in [
        "quantidade",
        "estoque_minimo",
        "preco_sintetico",
        "cobertura_meses",
        "venda_ult_13s",
        "venda_ult_52s",
        "media_semanal_13",
        "semanas_com_venda_13",
    ]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    for column in [
        "codigo_produto",
        "descricao_completa",
        "familia_produto",
        "status_estoque",
        "perfil_venda",
        "produto_inativo",
    ]:
        if column not in df.columns:
            df[column] = ""
        df[column] = df[column].fillna("").astype(str)

    return df


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.header("Filtros")

        families = ["Todas"] + sorted(
            value
            for value in df["familia_produto"].unique().tolist()
            if value and value.lower() != "nan"
        )
        statuses = ["Todos"] + sorted(
            value
            for value in df["status_estoque"].unique().tolist()
            if value and value.lower() != "nan"
        )
        profiles = ["Todos"] + sorted(
            value
            for value in df["perfil_venda"].unique().tolist()
            if value and value.lower() != "nan"
        )

        family = st.selectbox("Família", families)
        status = st.selectbox("Status estoque", statuses)
        profile = st.selectbox("Perfil", profiles)
        search = st.text_input("Buscar produto")

    filtered = df.copy()

    if family != "Todas":
        filtered = filtered[filtered["familia_produto"] == family]
    if status != "Todos":
        filtered = filtered[filtered["status_estoque"] == status]
    if profile != "Todos":
        filtered = filtered[filtered["perfil_venda"] == profile]
    if search.strip():
        term = search.strip().lower()
        filtered = filtered[
            filtered["descricao_completa"].str.lower().str.contains(
                term,
                na=False,
            )
            | filtered["codigo_produto"].str.lower().str.contains(
                term,
                na=False,
            )
        ]

    return filtered


def classify_inventory(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    rupture = df[
        (
            df["status_estoque"].str.upper().str.contains(
                "RUPTURA",
                na=False,
            )
        )
        | (
            (df["venda_ult_13s"] > 0)
            & (df["quantidade"] <= df["estoque_minimo"])
        )
        | (
            (df["venda_ult_13s"] > 0)
            & (df["cobertura_meses"] <= 1)
        )
    ].copy()

    obsolete = df[
        (
            df["produto_inativo"].str.upper().isin(
                ["SIM", "S", "TRUE", "1"]
            )
        )
        | (df["perfil_venda"].str.upper() == "SLOW")
        | (
            (df["media_semanal_13"] <= 1)
            & (df["semanas_com_venda_13"] <= 2)
        )
        | (
            df["status_estoque"].str.upper().str.contains(
                "OBSOLETO|VENC",
                na=False,
            )
        )
    ].copy()

    excess = df[
        (
            df["status_estoque"].str.upper().str.contains(
                "EXCESSO",
                na=False,
            )
        )
        | (df["cobertura_meses"] >= 6)
    ].copy()

    return {
        "rupture": rupture.sort_values(
            ["venda_ult_13s", "cobertura_meses"],
            ascending=[False, True],
        ),
        "obsolete": obsolete.sort_values(
            ["media_semanal_13", "venda_ult_13s"],
            ascending=[True, True],
        ),
        "excess": excess.sort_values(
            ["cobertura_meses", "quantidade"],
            ascending=[False, False],
        ),
    }


def metric_card(label: str, value: str, help_text: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-help">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def money(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def render_overview(df: pd.DataFrame, groups: dict[str, pd.DataFrame]) -> None:
    total_skus = len(df)
    active_skus = len(
        df[~df["produto_inativo"].str.upper().isin(["SIM", "S", "TRUE", "1"])]
    )
    total_stock_value = (
        df["quantidade"].fillna(0) * df["preco_sintetico"].fillna(0)
    ).sum()

    cols = st.columns(6)
    with cols[0]:
        metric_card("SKUs", str(total_skus), "Produtos filtrados")
    with cols[1]:
        metric_card("SKUs ativos", str(active_skus), "Produtos em operação")
    with cols[2]:
        metric_card("Ruptura", str(len(groups["rupture"])), "Vende e está perto de acabar")
    with cols[3]:
        metric_card("Obsoletos", str(len(groups["obsolete"])), "Baixo giro ou inativo")
    with cols[4]:
        metric_card("Excesso", str(len(groups["excess"])), "Cobertura alta")
    with cols[5]:
        metric_card("Valor estoque", money(total_stock_value), "Estimativa atual")


def product_columns() -> list[str]:
    return [
        "codigo_produto",
        "descricao_completa",
        "familia_produto",
        "status_estoque",
        "perfil_venda",
        "quantidade",
        "estoque_minimo",
        "cobertura_meses",
        "venda_ult_13s",
        "media_semanal_13",
        "preco_sintetico",
    ]


def render_table(title: str, df: pd.DataFrame, badge: str) -> None:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f'<span class="badge">{badge}</span>', unsafe_allow_html=True)
    st.subheader(title)

    available_columns = [
        column for column in product_columns() if column in df.columns
    ]
    st.dataframe(
        df[available_columns].head(30),
        use_container_width=True,
        hide_index=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_dashboard(df: pd.DataFrame) -> None:
    st.title("Dashboard de Inventário")
    st.caption("Leituras operacionais: ruptura, obsoletos e excesso.")

    filtered = apply_filters(df)
    groups = classify_inventory(filtered)

    render_overview(filtered, groups)

    st.divider()

    tab_overview, tab_rupture, tab_obsolete, tab_excess, tab_table, tab_agent = st.tabs(
        [
            "Visão Geral",
            "Ruptura",
            "Obsoletos",
            "Excesso",
            "Tabela Detalhada",
            "Agente",
        ]
    )

    with tab_overview:
        left, right = st.columns(2)
        with left:
            st.subheader("Distribuição por status")
            status_counts = (
                filtered["status_estoque"]
                .replace("", "Sem status")
                .value_counts()
                .head(12)
            )
            st.bar_chart(status_counts)
        with right:
            st.subheader("Top famílias por SKUs")
            family_counts = (
                filtered["familia_produto"]
                .replace("", "Sem família")
                .value_counts()
                .head(12)
            )
            st.bar_chart(family_counts)

    with tab_rupture:
        render_table(
            "Produtos em ruptura",
            groups["rupture"],
            "vende mas está perto de acabar",
        )

    with tab_obsolete:
        render_table(
            "Produtos obsoletos",
            groups["obsolete"],
            "baixo giro, inativo ou vencido",
        )

    with tab_excess:
        render_table(
            "Produtos com excesso",
            groups["excess"],
            "cobertura por muito tempo",
        )

    with tab_table:
        render_table("Base filtrada", filtered, f"{len(filtered)} produtos")

    with tab_agent:
        render_agent_chat()


def ensure_session(api_url: str, app_name: str, user_id: str, session_id: str) -> None:
    url = f"{api_url}/apps/{app_name}/users/{user_id}/sessions/{session_id}"
    requests.post(url, timeout=10)


def extract_adk_text(events: Any) -> str:
    if not isinstance(events, list):
        return ""

    for event in reversed(events):
        content = event.get("content", {})
        parts = content.get("parts", [])
        chunks = [
            part.get("text", "")
            for part in parts
            if part.get("text")
        ]
        if chunks:
            return "\n".join(chunks).strip()

    return ""


def call_agent(
    api_url: str,
    app_name: str,
    user_id: str,
    session_id: str,
    message: str,
) -> str:
    ensure_session(api_url, app_name, user_id, session_id)

    payload = {
        "appName": app_name,
        "userId": user_id,
        "sessionId": session_id,
        "newMessage": {
            "role": "user",
            "parts": [{"text": message}],
        },
    }

    response = requests.post(
        f"{api_url}/run",
        json=payload,
        timeout=120,
    )
    response.raise_for_status()

    text = extract_adk_text(response.json())
    return text or "Não consegui extrair a resposta do agente."


def render_agent_chat() -> None:
    st.subheader("Converse com o agente")
    st.caption("Requer `adk api_server` rodando em paralelo.")

    api_url = st.text_input(
        "ADK API URL",
        value=DEFAULT_API_URL,
    )
    app_name = st.selectbox(
        "Agente",
        ["inventory_app", "retailer_app"],
    )

    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = f"demo-{uuid.uuid4().hex[:8]}"
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Pergunte sobre estoque, ruptura, excesso ou vendas")

    if prompt:
        st.session_state.chat_messages.append(
            {"role": "user", "content": prompt}
        )
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Consultando agente..."):
                try:
                    answer = call_agent(
                        api_url=api_url.rstrip("/"),
                        app_name=app_name,
                        user_id="streamlit-user",
                        session_id=st.session_state.chat_session_id,
                        message=prompt,
                    )
                except Exception as exc:
                    answer = f"Erro ao chamar o agente: {exc}"

                st.markdown(answer)

        st.session_state.chat_messages.append(
            {"role": "assistant", "content": answer}
        )


def main() -> None:
    inject_styles()

    try:
        products = load_products()
    except Exception as exc:
        st.error(f"Erro ao carregar produtos do MongoDB: {exc}")
        return

    if products.empty:
        st.warning("Nenhum produto encontrado no MongoDB.")
        return

    render_dashboard(products)


if __name__ == "__main__":
    main()
