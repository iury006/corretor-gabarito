import streamlit as st
import pandas as pd
import numpy as np
import cv2

st.set_page_config(page_title="Corretor de Gabarito", layout="centered", initial_sidebar_state="expanded")

st.title("📝 Corretor de Gabarito")

# --- CONFIGURAÇÕES DA PROVA ---
st.sidebar.header("⚙️ Configurações da Prova")
num_questoes = st.sidebar.number_input("Número de Questões", min_value=1, max_value=50, value=10, key="cfg_num_q")
num_opcoes = st.sidebar.selectbox("Quantidade de Alternativas", [4, 5], index=1, format_func=lambda x: "A-D (4)" if x == 4 else "A-E (5)", key="cfg_num_opt")

letras = ['A', 'B', 'C', 'D', 'E'][:num_opcoes]

# --- DEFINIÇÃO DO GABARITO OFICIAL (ORDEM FIXA) ---
st.subheader("1. Gabarito Oficial")
gabarito_oficial = []

# Layout em container fixo e sequencial para evitar reorganização/embaralhamento no celular
with st.container():
    # Em telas pequenas/celular, exibe 2 por linha de forma sequencial limpa
    c1, c2 = st.columns(2)
    for i in range(num_questoes):
        col = c1 if i % 2 == 0 else c2
        with col:
            resp = st.selectbox(
                f"Questão {i+1:02d}", 
                letras, 
                key=f"gabarito_q_{i+1}"  # Chave estática única atrelada ao número da questão
            )
            gabarito_oficial.append(resp)

# --- INICIALIZAÇÃO DA SESSÃO ---
if "resultados" not in st.session_state:
    st.session_state.resultados = []

st.divider()

# --- LEITURA DO GABARITO DO ALUNO ---
st.subheader("2. Corrigir Cartão Resposta")

# Captura de foto usando câmera nativa
st.write("📌 *Ao abrir a câmera pela primeira vez, permita o acesso à câmera no seu navegador.*")
foto = st.camera_input("Capturar Gabarito", key="camera_input_aluno")

if foto is not None:
    # Converter imagem para OpenCV
    bytes_data = foto.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

    c_num, c_nome = st.columns([1, 2])
    with c_num:
        numero_aluno = st.text_input("Nº Frequência:", key="input_num_aluno")
    with c_nome:
        nome_aluno = st.text_input("Nome do Aluno (Opcional):", key="input_nome_aluno")

    if st.button("💾 Salvar Correção", key="btn_salvar_nota"):
        if not numero_aluno:
            st.warning("Insira o número da frequência antes de salvar.")
        else:
            # Lógica simulada de acertos
            acertos_simulados = np.random.randint(0, num_questoes + 1)
            nota = round((acertos_simulados / num_questoes) * 10, 1)

            st.session_state.resultados.append({
                "Número": numero_aluno,
                "Nome": nome_aluno if nome_aluno else "Não informado",
                "Acertos": f"{acertos_simulados}/{num_questoes}",
                "Nota": nota
            })
            st.success(f"✅ Salvo! Aluno Nº {numero_aluno} — Nota: {nota}")

# --- TABELA DE RESULTADOS E EXPORTAÇÃO ---
st.divider()
st.subheader("3. Notas Registradas")

if st.session_state.resultados:
    df = pd.DataFrame(st.session_state.resultados)
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📊 Gerar Planilha (CSV)",
        data=csv,
        file_name="notas_gabarito.csv",
        mime="text/csv",
        key="btn_download_csv"
    )
else:
    st.info("Nenhuma nota registrada ainda.")
