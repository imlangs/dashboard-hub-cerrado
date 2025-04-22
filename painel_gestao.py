import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import calendar
from datetime import datetime
from plotly.subplots import make_subplots
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title=os.getenv("STREAMLIT_APP_NAME", "Painel de Gestão Hub Cerrado"),
    layout="wide",
    initial_sidebar_state="expanded"
)

with open(os.getenv("CONFIG_PATH", "config.yaml")) as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    "hub_cerrado_dashboard",
    "auth_key",
    cookie_expiry_days=30
)

with st.sidebar:
    st.title("Login")
    name, authentication_status, username = authenticator.login("Login")

if authentication_status == False:
    st.sidebar.error("Username/password is incorrect")
    st.stop()
elif authentication_status == None:
    st.sidebar.warning("Please enter your username and password")
    st.stop()
elif authentication_status:
    st.sidebar.success(f"Welcome *{name}*")
    with st.sidebar:
        authenticator.logout("Logout")

    # Carregar logo
    logo_path = "Logo-Hub-Cerrado_350x100-1.png.webp"
    if Path(logo_path).exists():
        st.image(logo_path, width=350)

    try:
        # Carregar dados
        st.title("Dashboard Hub Cerrado")

        # Upload do arquivo pelo usuário
        uploaded_file = st.file_uploader("Faça upload do arquivo Excel (.xlsx)", type=["xlsx"])

        if uploaded_file is not None:
            @st.cache_data(ttl=3600)
            def load_data(file):
                df = pd.read_excel(file)
                df.columns = df.columns.str.strip()
                df["Data"] = pd.to_datetime(df["Data"])
                return df

            df = load_data(uploaded_file)

            st.success("Arquivo carregado com sucesso!")
            st.write(df.head())  # Exibe um preview dos dados

        else:
            st.warning("Por favor, faça upload do arquivo Excel para continuar.")
        
        df["Ano"] = df["Data"].dt.year
        df["Mês"] = df["Data"].dt.month

        anos_disponiveis = sorted(df["Ano"].unique(), reverse=True)
        meses_disponiveis = sorted(df["Mês"].unique())

        col_filtro_ano, col_filtro_mes = st.columns(2)
        ano_selecionado = col_filtro_ano.selectbox("Ano", anos_disponiveis, index=0)
        mes_selecionado = col_filtro_mes.selectbox("Mês", meses_disponiveis, index=len(meses_disponiveis)-1, format_func=lambda m: calendar.month_name[m])

        df_filtrado = df[(df["Ano"] == ano_selecionado) & (df["Mês"] == mes_selecionado)]
        st.title("Painel de Indicadores Estratégicos")

        # Criar abas
        aba_clientes, aba_financeiro, aba_ocupacao = st.tabs(["Indicadores de Clientes", "Indicadores Financeiros", "Ocupação do Habitat"])

        # ========================================
        # Aba de Indicadores de Clientes
        # ========================================
        with aba_clientes:
            def formatar_moeda(valor):
                return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            def formatar_percentual(valor):
                return f"{valor:.2%}".replace(".", ",")

            pivot_mix = df.copy()

            ltv_total = df_filtrado[df_filtrado['Indicador'] == 'LTV']['Valor'].sum()
            cac_total = df_filtrado[df_filtrado['Indicador'] == 'CAC']['Valor'].sum()
            churn_total = df_filtrado[df_filtrado['Indicador'] == 'Churn Rate']['Valor'].sum()

            st.subheader("Indicadores Gerais - LTV, CAC e Churn")
            col1, col2, col3 = st.columns(3)
            col1.metric("LTV", formatar_moeda(ltv_total))
            col2.metric("CAC", f"R$ {cac_total:.2f}")
            col3.metric("Churn", formatar_percentual(churn_total))

            # =============================
            # EVOLUÇÃO DE CLIENTES COM CHURN RATE
            # =============================
            clientes_df = df[df["Indicador"].isin(["Clientes Novos", "Churn", "Clientes Ativos"])].copy()
            pivot_clientes = clientes_df.pivot_table(index="Data", columns="Indicador", values="Valor", aggfunc="sum").reset_index()

            if set(["Churn", "Clientes Ativos", "Clientes Novos"]).issubset(pivot_clientes.columns):
                pivot_clientes["Churn Rate (%)"] = (pivot_clientes["Churn"] / pivot_clientes["Clientes Ativos"]) * 100

                fig_evolucao = make_subplots(specs=[[{"secondary_y": True}]])

                fig_evolucao.add_trace(go.Bar(
                    x=pivot_clientes["Data"],
                    y=pivot_clientes["Clientes Novos"],
                    name="Clientes Novos",
                    marker_color="#FFB84D",
                    text=pivot_clientes["Clientes Novos"],
                    textposition="auto"
                ), secondary_y=False)

                fig_evolucao.add_trace(go.Bar(
                    x=pivot_clientes["Data"],
                    y=pivot_clientes["Clientes Ativos"],
                    name="Clientes Ativos",
                    marker_color="#FFD700",
                    text=pivot_clientes["Clientes Ativos"],
                    textposition="auto"
                ), secondary_y=False)

                fig_evolucao.add_trace(go.Scatter(
                    x=pivot_clientes["Data"],
                    y=pivot_clientes["Churn Rate (%)"],
                    name="Churn Rate (%)",
                    mode="lines+markers",
                    line=dict(color="#FF6F00", width=3),
                    text=[f"{val:.2f}%" for val in pivot_clientes["Churn Rate (%)"]],
                    textposition="top center"
                ), secondary_y=True)

                fig_evolucao.update_layout(
                    barmode='stack',
                    title="Evolução de Clientes: Novos, Ativos e Churn Rate",
                    xaxis_title="Data",
                    yaxis_title="Quantidade de Clientes",
                    legend_title="Indicador",
                    yaxis2_title="Churn Rate (%)",
                    shapes=[dict(
                        type="rect",
                        xref="x",
                        yref="paper",
                        x0=datetime(2025, 1, 1),
                        x1=datetime(2025, 12, 31),
                        y0=0,
                        y1=1,
                        fillcolor="LightGrey",
                        opacity=0.3,
                        layer="below",
                        line_width=0,
                    )]
                )

                st.plotly_chart(fig_evolucao, use_container_width=True)
            else:
                st.error("As colunas esperadas ('Clientes Novos', 'Churn', 'Clientes Ativos') não estão presentes no DataFrame após o pivot.")

        # ========================================
        # Aba de Indicadores Financeiros
        # ========================================
        with aba_financeiro:
            st.subheader("💰 Indicadores Financeiros - Receita Total, Resultado Operacional e MRR")

            receita_mes = df_filtrado[df_filtrado["Indicador"] == "Receita Total"]["Valor"].sum()
            resultado_operacional_mes = df_filtrado[df_filtrado["Indicador"] == "Resultado Operacional"]["Valor"].sum()
            mrr_total = df_filtrado[df_filtrado["Indicador"] == "MRR"]["Valor"].sum()

            col1, col2, col3 = st.columns(3)
            col1.metric("Receita do Mês", formatar_moeda(receita_mes))
            col2.metric("Resultado Operacional do Mês", formatar_moeda(resultado_operacional_mes))
            col3.metric("MRR", formatar_moeda(mrr_total))

            df_tidy = df.copy()
            df_tidy["Data"] = pd.to_datetime(df_tidy["Data"])
            df_tidy["Ano"] = df_tidy["Data"].dt.year
            df_tidy["Mês"] = df_tidy["Data"].dt.month
            df_tidy["Nome_Mês"] = df_tidy["Data"].dt.strftime("%b")

            indicadores = ["Receita Total", "Resultado Operacional"]
            df_fin = df_tidy[df_tidy["Indicador"].isin(indicadores)]

            for indicador in indicadores:
                st.markdown(f"### {indicador}")
                df_ind = df_fin[df_fin["Indicador"] == indicador].copy()
                df_ind.sort_values(["Mês", "Ano"], inplace=True)

                fig = go.Figure()

                for ano in sorted(df_ind["Ano"].unique()):
                    df_ano = df_ind[df_ind["Ano"] == ano]
                    fig.add_trace(go.Scatter(
                        x=df_ano["Nome_Mês"],
                        y=df_ano["Valor"],
                        name=f"{ano}",
                        mode="lines+markers",
                        line=dict(color="#FFA500") if ano == 2025 else dict(color="#FFCC80")
                    ))

                # Linha de meta (se disponível)
                if df_ind["Meta"].notna().any():
                    metas = df_ind.dropna(subset=["Meta"])
                    metas_grouped = metas.groupby("Mês")["Meta"].mean().reset_index()
                    metas_grouped["Nome_Mês"] = metas_grouped["Mês"].apply(lambda x: calendar.month_abbr[x])
                    fig.add_trace(go.Scatter(
                        x=metas_grouped["Nome_Mês"],
                        y=metas_grouped["Meta"],
                        name="Meta",
                        line=dict(dash="dot", color="black"),
                        mode="lines"
                    ))

                # Linha de tendência (média mensal)
                media_mensal = df_ind.groupby("Mês")["Valor"].mean().reset_index()
                media_mensal["Nome_Mês"] = media_mensal["Mês"].apply(lambda x: calendar.month_abbr[x])
                fig.add_trace(go.Scatter(
                    x=media_mensal["Nome_Mês"],
                    y=media_mensal["Valor"],
                    name="Tendência",
                    line=dict(dash="dot", color="gray"),
                    mode="lines"
                ))

                fig.update_layout(
                    xaxis_title="Mês",
                    yaxis_title="R$",
                    title=f"Evolução de {indicador}",
                    legend_title="Linha",
                    hovermode="x unified"
                )

                st.plotly_chart(fig, use_container_width=True)

        # ========================================
        # Aba de Ocupação do Habitat
        # ========================================
        with aba_ocupacao:
            st.markdown("## 🏢 Ocupação do Habitat")
            st.markdown("### Ocupação mensal das áreas do Hub Cerrado")

            indicadores_ocupacao = [
                "Ocupação do Habitat",
                "Estações de Trabalho",
                "Salas Privativas",
                "Auditório Ipê"
            ]

            df_ocupacao = df[df["Indicador"].isin(indicadores_ocupacao)].copy()
            df_mes_atual_ocupacao = df_ocupacao[(df_ocupacao["Ano"] == ano_selecionado) & (df_ocupacao["Mês"] == mes_selecionado)]

            col1, col2, col3, col4 = st.columns(4)

            valor_ocupacao_habitat = df_mes_atual_ocupacao[df_mes_atual_ocupacao["Indicador"] == "Ocupação do Habitat"]["Valor"].values
            meta_ocupacao_habitat = df_mes_atual_ocupacao[df_mes_atual_ocupacao["Indicador"] == "Ocupação do Habitat"]["Meta"].values

            if len(valor_ocupacao_habitat) > 0:
                valor_ocupacao_habitat_fmt = f"{valor_ocupacao_habitat[0] * 100:.1f}%"  # Formatação de percentual
                meta_ocupacao_habitat_fmt = f"{meta_ocupacao_habitat[0] * 100:.1f}%" if len(meta_ocupacao_habitat) > 0 else "–"
            else:
                valor_ocupacao_habitat_fmt = "–"
                meta_ocupacao_habitat_fmt = "–"

            col1.metric(label="Ocupação do Habitat", value=valor_ocupacao_habitat_fmt, delta=f"Meta: {meta_ocupacao_habitat_fmt}")

            for col, indicador in zip([col2, col3, col4], indicadores_ocupacao[1:]):  # Começando do segundo indicador
                valor = df_mes_atual_ocupacao[df_mes_atual_ocupacao["Indicador"] == indicador]["Valor"].values
                meta = df_mes_atual_ocupacao[df_mes_atual_ocupacao["Indicador"] == indicador]["Meta"].values

                if len(valor) > 0:
                    valor_fmt = f"{valor[0] * 100:.1f}%"  # Formatação de percentual
                    meta_fmt = f"{meta[0] * 100:.1f}%" if len(meta) > 0 else "–"
                else:
                    valor_fmt = "–"
                    meta_fmt = "–"

                col.metric(label=indicador, value=valor_fmt, delta=f"Meta: {meta_fmt}")

            st.markdown("### 📈 Evolução da Ocupação")

            import plotly.express as px
            for indicador in indicadores_ocupacao:
                st.markdown(f"#### {indicador}")
                df_ind = df_ocupacao[df_ocupacao["Indicador"] == indicador].copy()
                df_ind["Nome_Mês"] = df_ind["Data"].dt.strftime("%b")
                df_ind.sort_values(["Mês", "Ano"], inplace=True)

                fig = go.Figure()

                # Linhas por ano
                for ano in sorted(df_ind["Ano"].unique()):
                    df_ano = df_ind[df_ind["Ano"] == ano]
                    fig.add_trace(go.Scatter(
                        x=df_ano["Nome_Mês"],
                        y=df_ano["Valor"] * 100,
                        name=f"{ano}",
                        mode="lines+markers",
                        line=dict(color="#FFA500") if ano == 2025 else dict(color="#FFCC80")
                    ))

                # Linha de meta (se disponível)
                if df_ind["Meta"].notna().any():
                    metas = df_ind.dropna(subset=["Meta"])
                    metas_grouped = metas.groupby("Mês")["Meta"].mean().reset_index()
                    metas_grouped["Nome_Mês"] = metas_grouped["Mês"].apply(lambda x: calendar.month_abbr[x])
                    fig.add_trace(go.Scatter(
                        x=metas_grouped["Nome_Mês"],
                        y=metas_grouped["Meta"] * 100,
                        name="Meta",
                        line=dict(dash="dot", color="black"),
                        mode="lines"
                    ))

                fig.update_layout(
                    xaxis_title="Mês",
                    yaxis_title="Ocupação (%)",
                    yaxis_range=[0, 110],
                    title=f"Evolução da Ocupação - {indicador}",
                    legend_title="Ano",
                    hovermode="x unified"
                )

                st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao carregar os dados: {str(e)}")
        st.stop()
