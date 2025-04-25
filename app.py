
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from sqlalchemy import create_engine

# ---------------- CONFIGURAÇÃO INICIAL ----------------
st.set_page_config(page_title="Dashboard Pizzaria", layout="wide")

sns.set_theme(style="darkgrid")
plt.rcParams["figure.figsize"] = (4, 2.3)
plt.rcParams["axes.labelsize"] = 9
plt.rcParams["axes.titlesize"] = 11

# ---------------- CONEXÃO SUPABASE ----------------
SUPABASE_URL = "postgresql://postgres:vilahoa20001@db.dsejbxatmyeosjihywrk.supabase.co:5432/postgres"  # Substitua 
engine = create_engine(SUPABASE_URL)

def ler_clientes():
    return pd.read_sql("SELECT * FROM clientes", con=engine)

def ler_campanhas():
    return pd.read_sql("SELECT * FROM campanhas", con=engine)

def salvar_campanhas(df):
    df.to_sql("campanhas", con=engine, if_exists="replace", index=False)

# ---------------- NAVEGAÇÃO ----------------
st.sidebar.title("📂 Navegação")
page = st.sidebar.selectbox("Escolha a página", ["Dashboard", "Gráficos", "📣 Campanhas"])

# ---------------- LEITURA DE DADOS ----------------
df = ler_clientes()
campanhas_df = ler_campanhas()
hoje = pd.to_datetime(datetime.today().date())
df['ultimo_pedido'] = pd.to_datetime(df['ultimo_pedido'])
df['dias_sem_pedido'] = (hoje - df['ultimo_pedido']).dt.days

def classificar_grupo(dias):
    if dias <= 10: return '0-10 dias'
    elif dias <= 20: return '11-20 dias'
    elif dias <= 30: return '21-30 dias'
    else: return '31+ dias'

df['grupo'] = df['dias_sem_pedido'].apply(classificar_grupo)
mensagem_por_grupo = dict(zip(campanhas_df['grupo_alvo'], campanhas_df['mensagem']))
df['mensagem_campanha'] = df['grupo'].map(mensagem_por_grupo)

# ---------------- DASHBOARD ----------------
if page == "Dashboard":
    st.title("📊 Dashboard de Clientes - Pizzaria 🍕")
    st.dataframe(df[['nome', 'telefone', 'email', 'ultimo_pedido', 'dias_sem_pedido', 'grupo', 'qtd_pedidos', 'mensagem_campanha']], use_container_width=True)

# ---------------- GRÁFICOS ----------------
elif page == "Gráficos":
    st.title("📈 Análises Visuais")
    grupo_df = df['grupo'].value_counts().reset_index()
    grupo_df.columns = ['Grupo', 'Clientes']
    fig1, ax1 = plt.subplots()
    sns.barplot(data=grupo_df, x='Grupo', y='Clientes', ax=ax1)
    ax1.set_title("Distribuição por Grupo")
    st.pyplot(fig1)

# ---------------- CAMPANHAS ----------------
elif page == "📣 Campanhas":
    st.title("📣 Cadastro de Campanhas")
    st.subheader("Nova campanha")

    with st.form("form_campanha"):
        nome = st.text_input("Nome")
        grupo_alvo = st.selectbox("Grupo-alvo", sorted(df['grupo'].unique()))
        mensagem = st.text_area("Mensagem")
        data_envio = st.date_input("Data envio")
        enviar = st.form_submit_button("Salvar")

    if enviar:
        nova = pd.DataFrame([{
            "nome": nome,
            "grupo_alvo": grupo_alvo,
            "mensagem": mensagem,
            "data_envio": data_envio
        }])
        campanhas_df = pd.concat([campanhas_df, nova], ignore_index=True)
        salvar_campanhas(campanhas_df)
        st.success("✅ Campanha salva com sucesso!")

    st.subheader("📋 Campanhas existentes")
    st.dataframe(campanhas_df, use_container_width=True)
