python3 -m pip install basedosdados

import os
import pandas as pd
from collections import Counter
import streamlit as st
import unicodedata
import basedosdados as bd

# ============================
# CONFIGURAÇÕES
# ============================

st.set_page_config(page_title="Análise de Temas Jurídicos - STF", page_icon="⚖️", layout="wide")

# 🔹 Insira seu billing_id da Base dos Dados
BILLING_ID = "basedosdados"

YEARS = list(range(2020, 2026))
YOUTUBE_API_KEY = os.environ.get("AIzaSyASTN-AAwkkQMnpxDkzLCW4m-x8FH8n340")

# ============================
# FUNÇÕES AUXILIARES
# ============================

def normalizar_texto(texto):
    """Remove acentos e coloca tudo em minúsculas."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto.lower())
        if unicodedata.category(c) != 'Mn'
    )

def buscar_decisoes(tema):
    """Busca decisões no STF que contenham o tema no assunto_processo."""
    tema_norm = normalizar_texto(tema)

    query = f"""
        SELECT
            dados.ano as ano,
            dados.assunto_processo as assunto_processo,
            dados.ramo_direito as ramo_direito
        FROM `basedosdados.br_stf_corte_aberta.decisoes` AS dados
        WHERE LOWER(REGEXP_REPLACE(dados.assunto_processo, r'[^\w\s]', '')) LIKE '%{tema_norm}%'
          AND dados.ano BETWEEN 2020 AND 2025
    """

    df = bd.read_sql(query=query, billing_project_id=BILLING_ID)
    return df

def contar_por_ano(df):
    contagem = df['ano'].value_counts().to_dict()
    return {ano: contagem.get(ano, 0) for ano in YEARS}

def buscar_videos_youtube(tema, max_results=5):
    """Busca vídeos no YouTube relacionados ao tema."""
    if not YOUTUBE_API_KEY:
        return []

    try:
        service = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        query = f"{tema} STF Brasil"
        request = service.search().list(q=query, part="snippet", maxResults=max_results, type="video")
        response = request.execute()

        videos = []
        for item in response.get("items", []):
            videos.append({
                "title": item["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            })
        return videos
    except Exception as e:
        st.warning(f"⚠️ Erro ao buscar vídeos no YouTube: {e}")
        return []

# ============================
# INTERFACE STREAMLIT
# ============================

st.title("⚖️ Análise de Decisões do STF por Tema (2020–2025)")
st.markdown("Pesquise decisões do STF e visualize a evolução de um tema ao longo do tempo.")

tema = st.text_input("Digite o tema que deseja analisar:", placeholder="ex: educação, saúde, meio ambiente...")

if st.button("🔍 Buscar decisões"):
    if not tema.strip():
        st.warning("Por favor, insira um tema para continuar.")
    else:
        with st.spinner("Consultando Base dos Dados (STF)..."):
            df = buscar_decisoes(tema)

        if df.empty:
            st.error("❌ Nenhuma decisão encontrada para esse tema.")
        else:
            st.success(f"✅ {len(df)} decisões encontradas!")

            # Exibir tabela
            st.dataframe(df)

            # --- Gráfico ---
            contagem = contar_por_ano(df)
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(contagem.keys(), contagem.values(), color="#1f77b4")
            ax.set_xlabel("Ano")
            ax.set_ylabel("Número de decisões")
            ax.set_title(f"Evolução de decisões sobre '{tema}' (2020–2025)")
            st.pyplot(fig)

            # --- Vídeos do YouTube ---
            st.subheader("🎥 Vídeos recomendados sobre o tema")
            videos = buscar_videos_youtube(tema)
            if videos:
                for v in videos:
                    st.markdown(f"- [{v['title']}]({v['url']})")
            else:
                st.info("Nenhum vídeo encontrado ou chave da API do YouTube não configurada.")
