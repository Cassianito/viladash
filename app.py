import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

st.set_page_config(page_title="Dashboard Pizzaria", layout="wide")

# Estilo de gráficos e layout visual
sns.set_theme(style="darkgrid")
plt.rcParams["figure.figsize"] = (4, 2.3)
plt.rcParams["axes.labelsize"] = 9
plt.rcParams["axes.titlesize"] = 11
plt.rcParams["xtick.labelsize"] = 8
plt.rcParams["ytick.labelsize"] = 8

# Estilo dos cards e blocos
st.markdown("""
    <style>
        .card {
            background-color: #111827;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.15);
        }
        .card h2 { font-size: 2.2rem; margin: 0; }
        .msg-box {
            background-color: #1e293b;
            color: white;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 10px;
            border-left: 4px solid #4CAF50;
        }
        .msg-text {
            background: #0f172a;
            color: #a3e635;
            font-family: monospace;
            padding: 10px;
            border-radius: 6px;
            margin-top: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# Funções auxiliares
def classificar_grupo(dias):
    if dias <= 10: return '0-10 dias'
    elif dias <= 20: return '11-20 dias'
    elif dias <= 30: return '21-30 dias'
    else: return '31+ dias'

def gerar_mensagem(nome, grupo):
    return f"Olá {nome}, sentimos sua falta! 🍕 Faz {grupo} que você não pede. Aproveite uma promoção especial!"

# Página lateral
st.sidebar.title("📂 Navegação e dados")
page = st.sidebar.selectbox("Escolha a página", ["Dashboard", "Gráficos", "📣 Campanhas"])
uploaded_file = st.sidebar.file_uploader("📥 Upload de CSV", type=["csv"])

# Carregar base de clientes
try:
    df = pd.read_csv(uploaded_file) if uploaded_file else pd.read_csv("clientes_com_dados_para_graficos.csv")
except FileNotFoundError:
    st.error("❌ CSV de clientes não encontrado.")
    st.stop()

df['ultimo_pedido'] = pd.to_datetime(df['ultimo_pedido'])
hoje = pd.to_datetime(datetime.today().date())
df['dias_sem_pedido'] = (hoje - df['ultimo_pedido']).dt.days
df['grupo'] = df['dias_sem_pedido'].apply(classificar_grupo)

# Lê campanhas e associa mensagem por grupo
try:
    campanhas_df = pd.read_csv("campanhas.csv")
except FileNotFoundError:
    campanhas_df = pd.DataFrame(columns=["nome", "grupo_alvo", "mensagem", "data_envio"])

mensagem_por_grupo = dict(zip(campanhas_df['grupo_alvo'], campanhas_df['mensagem']))
df['mensagem_campanha'] = df['grupo'].map(mensagem_por_grupo)

# ---------------- DASHBOARD ----------------
if page == "Dashboard":
    st.title("📊 Dashboard de Clientes - Pizzaria 🍕")

    ativos_30 = df[df['dias_sem_pedido'] <= 30]
    inativos_30 = df[df['dias_sem_pedido'] > 30]
    ativos_60 = df[(df['ultimo_pedido'] >= hoje - timedelta(days=60)) & (df['ultimo_pedido'] <= hoje - timedelta(days=31))]
    var_pct = ((len(ativos_30) - len(ativos_60)) / len(ativos_60) * 100) if len(ativos_60) > 0 else 0
    seta = "🔺" if var_pct >= 0 else "🔻"

    if "filtro_card" not in st.session_state:
        st.session_state.filtro_card = None

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🧍 Total"):
            st.session_state.filtro_card = "todos"
        st.markdown(f"<div class='card'><h4>Total</h4><h2>{len(df)}</h2></div>", unsafe_allow_html=True)
    with col2:
        if st.button("🔁 Ativos"):
            st.session_state.filtro_card = "ativos"
        st.markdown(f"<div class='card'><h4>Ativos (30d)</h4><h2>{len(ativos_30)} {seta} {abs(var_pct):.1f}%</h2></div>", unsafe_allow_html=True)
    with col3:
        if st.button("😴 Inativos"):
            st.session_state.filtro_card = "inativos"
        st.markdown(f"<div class='card'><h4>Inativos</h4><h2>{len(inativos_30)}</h2></div>", unsafe_allow_html=True)

    st.sidebar.title("🔍 Filtros")
    grupo_opcao = st.sidebar.selectbox("Grupo:", ["Todos"] + sorted(df['grupo'].unique()))
    intervalo_data = st.sidebar.date_input("Data último pedido:", (df['ultimo_pedido'].min().date(), df['ultimo_pedido'].max().date()))
    busca = st.sidebar.text_input("Buscar por nome, telefone ou e-mail:")

    df_filtrado = df.copy()
    if grupo_opcao != "Todos":
        df_filtrado = df_filtrado[df_filtrado['grupo'] == grupo_opcao]
    if isinstance(intervalo_data, tuple) and len(intervalo_data) == 2:
        ini, fim = intervalo_data
        df_filtrado = df_filtrado[df_filtrado['ultimo_pedido'].dt.date.between(ini, fim)]
    if busca:
        busca = busca.lower()
        df_filtrado = df_filtrado[
            df_filtrado['nome'].str.lower().str.contains(busca) |
            df_filtrado['telefone'].str.contains(busca) |
            df_filtrado['email'].str.lower().str.contains(busca)
        ]
    if st.session_state.filtro_card == "ativos":
        df_filtrado = df_filtrado[df_filtrado['dias_sem_pedido'] <= 30]
    elif st.session_state.filtro_card == "inativos":
        df_filtrado = df_filtrado[df_filtrado['dias_sem_pedido'] > 30]

    st.markdown(f"### 📋 Clientes encontrados: {len(df_filtrado)}")
    st.dataframe(df_filtrado[['nome', 'telefone', 'email', 'ultimo_pedido', 'dias_sem_pedido', 'grupo', 'qtd_pedidos', 'mensagem_campanha']], use_container_width=True)

    st.download_button("📥 Baixar CSV com mensagens", df_filtrado.to_csv(index=False).encode('utf-8'), "clientes_filtrados.csv", "text/csv")

    st.markdown("## ⭐ Mais Fiéis")
    st.dataframe(df.sort_values("qtd_pedidos", ascending=False).head(10)[['nome', 'telefone', 'qtd_pedidos']], use_container_width=True)

    st.markdown("## ⏱️ Maior Intervalo")
    st.dataframe(df.sort_values("dias_sem_pedido", ascending=False).head(10)[['nome', 'telefone', 'dias_sem_pedido']], use_container_width=True)

# ---------------- GRÁFICOS ----------------
elif page == "Gráficos":
    st.title("📈 Análises Visuais - Comportamento dos Clientes")

    st.markdown("### 📌 Distribuição por grupo de inatividade")
    st.markdown("""
Este gráfico mostra quantos clientes estão em cada faixa de tempo desde o último pedido.
**Exemplo:** Um grande número em '31+ dias' pode indicar necessidade de campanhas de recuperação.
""")
    grupo_df = df['grupo'].value_counts().reset_index()
    grupo_df.columns = ['Grupo', 'Clientes']
    fig1, ax1 = plt.subplots()
    sns.barplot(data=grupo_df, x='Grupo', y='Clientes', ax=ax1)
    ax1.set_title("Distribuição por Grupo")
    st.pyplot(fig1)

    st.markdown("### 📦 Fidelidade por grupo")
    st.markdown("""
Este boxplot mostra a distribuição da quantidade de pedidos em cada grupo de inatividade.
**Exemplo:** Se os clientes com mais pedidos estão ficando inativos, pode ser hora de reativar com vantagens exclusivas.
""")
    fig2, ax2 = plt.subplots()
    sns.boxplot(data=df, x='grupo', y='qtd_pedidos', ax=ax2)
    ax2.set_xlabel("Grupo")
    ax2.set_ylabel("Qtd de Pedidos")
    ax2.set_title("Pedidos por Grupo")
    st.pyplot(fig2)

    st.markdown("### 📉 Inatividade média por faixa de fidelidade")
    st.markdown("""
Este gráfico mostra a média de dias sem pedido por grupos de fidelidade.
**Exemplo:** Se clientes com 10+ pedidos têm baixa inatividade, é sinal de boa retenção.
""")
    df['faixa_pedidos'] = pd.cut(df['qtd_pedidos'], bins=[0, 3, 6, 9, 12, 15], labels=["1-3", "4-6", "7-9", "10-12", "13-15"])
    faixa_df = df.groupby("faixa_pedidos")["dias_sem_pedido"].mean().reset_index()
    fig3, ax3 = plt.subplots()
    sns.barplot(data=faixa_df, x="faixa_pedidos", y="dias_sem_pedido", ax=ax3)
    ax3.set_xlabel("Faixa de Fidelidade")
    ax3.set_ylabel("Média de Dias sem Pedido")
    ax3.set_title("Inatividade por Fidelidade")
    st.pyplot(fig3)

# ---------------- CAMPANHAS ----------------
elif page == "📣 Campanhas":
    st.title("📣 Cadastro e Gestão de Campanhas por Grupo")

    campanha_path = "campanhas.csv"

    try:
        campanhas_df = pd.read_csv(campanha_path)
    except FileNotFoundError:
        campanhas_df = pd.DataFrame(columns=["nome", "grupo_alvo", "mensagem", "data_envio"])

    st.subheader("➕ Criar nova campanha")

    with st.form("form_campanha"):
        nome = st.text_input("Nome da campanha")
        grupo_alvo = st.selectbox("Grupo de clientes", sorted(df['grupo'].unique()))
        mensagem = st.text_area("Mensagem da campanha")
        data_envio = st.date_input("Data planejada para envio")
        enviar = st.form_submit_button("Salvar campanha")

    if enviar:
        nova = pd.DataFrame([{
            "nome": nome,
            "grupo_alvo": grupo_alvo,
            "mensagem": mensagem,
            "data_envio": data_envio
        }])
        campanhas_df = pd.concat([campanhas_df, nova], ignore_index=True)
        campanhas_df.to_csv(campanha_path, index=False)
        st.success("✅ Campanha cadastrada com sucesso!")

    st.markdown("### 📋 Campanhas cadastradas")
    st.dataframe(campanhas_df, use_container_width=True)
