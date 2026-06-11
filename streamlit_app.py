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
# Timeout (segundos) para chamadas ao agente. Modelos locais em CPU (ex.: Qwen 7B)
# podem levar mais de 120s na primeira resposta; ajustável via env.
AGENT_API_TIMEOUT = float(os.getenv("AGENT_API_TIMEOUT", "300"))

# URL da UI do Phoenix (deriva do endpoint OTEL).
PHOENIX_UI_URL = os.getenv(
    "PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces"
).replace("/v1/traces", "")

# Prompts de um clique para o demo (evita digitar ao vivo).
SUGGESTED_PROMPTS = {
    "retailer_app": [
        "Quero 3 cervejas Amstel Ultra",
        "Adiciona 1 Torcida Cebola",
        "Pode fechar o pedido",
    ],
    "inventory_app": [
        "Quais produtos estão em ruptura?",
        "Produtos com excesso de estoque",
        "Quais os mais vendidos?",
    ],
}


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


def render_table(df: pd.DataFrame, badge: str) -> None:
    # Apenas o selo verde explicando a seção (sem card branco vazio nem
    # subtítulo redundante — a aba já nomeia a seção).
    st.markdown(f'<span class="badge">{badge}</span>', unsafe_allow_html=True)

    available_columns = [
        column for column in product_columns() if column in df.columns
    ]
    st.dataframe(
        df[available_columns].head(30),
        use_container_width=True,
        hide_index=True,
    )


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
            groups["rupture"],
            "Ruptura — vende mas está perto de acabar",
        )

    with tab_obsolete:
        render_table(
            groups["obsolete"],
            "Obsoletos — baixo giro, inativo ou vencido",
        )

    with tab_excess:
        render_table(
            groups["excess"],
            "Excesso — cobertura alta, parado há muito tempo",
        )

    with tab_table:
        render_table(filtered, f"Base filtrada — {len(filtered)} produtos")

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
        timeout=AGENT_API_TIMEOUT,
    )
    response.raise_for_status()

    text = extract_adk_text(response.json())
    return text or "Não consegui extrair a resposta do agente."


def active_model_label() -> str:
    """Rótulo curto do provider/modelo ativo (talking point do demo)."""
    provider = os.getenv("MODEL_PROVIDER", "gemini").lower()
    if provider in {"openai", "litellm"}:
        return f"openai · {os.getenv('LITELLM_MODEL', '?')}"
    if provider in {"gemini", "google"}:
        return f"gemini · {os.getenv('MODEL', '?')}"
    if provider == "ollama":
        return f"ollama · {os.getenv('OLLAMA_MODEL', '?')}"
    return provider


def reset_chat() -> None:
    """Zera a conversa: nova sessão (carrinho/estado do agente do zero)."""
    st.session_state.chat_session_id = f"demo-{uuid.uuid4().hex[:8]}"
    st.session_state.chat_messages = []


def fetch_cart(
    api_url: str,
    app_name: str,
    user_id: str,
    session_id: str,
) -> list[dict[str, Any]]:
    """Só o carrinho da sessão do agente. Extrai exclusivamente a chave 'cart' —
    o restante do estado interno (seleção, buscas, etc.) nunca é exposto."""
    try:
        response = requests.get(
            f"{api_url}/apps/{app_name}/users/{user_id}/sessions/{session_id}",
            timeout=10,
        )
        if response.status_code != 200:
            return []
        return response.json().get("state", {}).get("cart", []) or []
    except Exception:
        return []


def render_cart_panel(cart: list[dict[str, Any]]) -> None:
    """Resumo de pedido voltado ao cliente: itens e total, nada além disso."""
    with st.container(border=True):
        st.markdown('<span class="badge">🛒 Pedido</span>', unsafe_allow_html=True)

        if not cart:
            st.caption(
                "Nenhum item ainda. Os produtos aparecem aqui durante a conversa."
            )
            return

        total = 0.0
        for item in cart:
            quantity = item.get("quantidade") or 0
            price = item.get("preco_unitario") or 0.0
            subtotal = quantity * price
            total += subtotal
            st.markdown(
                f"**{quantity}×** {item.get('descricao_completa', '')}"
                f"<br><span style='color:#64748b;font-size:13px'>{money(subtotal)}</span>",
                unsafe_allow_html=True,
            )
        st.divider()
        st.markdown(
            "<span style='color:#64748b;font-size:12px;font-weight:700;"
            "text-transform:uppercase'>Total</span><br>"
            f"<span style='font-size:24px;font-weight:800;color:#0f766e'>"
            f"{money(total)}</span>",
            unsafe_allow_html=True,
        )


def render_agent_chat() -> None:
    head_left, head_right = st.columns([3, 1])
    with head_left:
        st.subheader("Converse com o agente")
    with head_right:
        st.markdown(
            f'<div style="text-align:right;margin-top:10px">'
            f'<span class="badge">{active_model_label()}</span></div>',
            unsafe_allow_html=True,
        )

    sel_col, url_col = st.columns([1, 2])
    with sel_col:
        app_name = st.selectbox(
            "Agente",
            ["retailer_app", "inventory_app"],
            key="agent_select",
        )
    with url_col:
        api_url = st.text_input("ADK API URL", value=DEFAULT_API_URL).rstrip("/")

    # Trocar de agente começa uma conversa nova (evita vazar sessão).
    if st.session_state.get("active_app") != app_name:
        st.session_state.active_app = app_name
        reset_chat()

    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = f"demo-{uuid.uuid4().hex[:8]}"
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    act_col, info_col = st.columns([1, 3])
    with act_col:
        if st.button("🗑️ Nova conversa", use_container_width=True):
            reset_chat()
            st.rerun()
    with info_col:
        st.caption(f"Observabilidade: [Phoenix]({PHOENIX_UI_URL})")

    # Prompts de um clique (roteiro do demo).
    pending: str | None = None
    suggestions = SUGGESTED_PROMPTS.get(app_name, [])
    if suggestions:
        st.caption("Sugestões:")
        for col, text in zip(st.columns(len(suggestions)), suggestions):
            if col.button(text, key=f"sugg-{app_name}-{text}", use_container_width=True):
                pending = text

    chat_col, cart_col = st.columns([2, 1])

    with chat_col:
        if not st.session_state.chat_messages:
            hint = (
                "👋 Comece um pedido — ex.: peça uma cerveja e eu sugiro o que levar junto."
                if app_name == "retailer_app"
                else "👋 Pergunte sobre o estoque — ruptura, excesso, obsoletos ou mais vendidos."
            )
            st.info(hint)

        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    with cart_col:
        if app_name == "retailer_app":
            render_cart_panel(
                fetch_cart(
                    api_url,
                    app_name,
                    "streamlit-user",
                    st.session_state.chat_session_id,
                )
            )

    prompt = st.chat_input(
        "Pergunte sobre estoque, vendas, ou faça um pedido"
    ) or pending

    if prompt:
        st.session_state.chat_messages.append(
            {"role": "user", "content": prompt}
        )
        try:
            with st.spinner("Consultando agente..."):
                answer = call_agent(
                    api_url=api_url,
                    app_name=app_name,
                    user_id="streamlit-user",
                    session_id=st.session_state.chat_session_id,
                    message=prompt,
                )
        except Exception as exc:
            answer = f"Erro ao chamar o agente: {exc}"

        st.session_state.chat_messages.append(
            {"role": "assistant", "content": answer}
        )
        st.rerun()


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
