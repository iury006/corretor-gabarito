import streamlit as st
import pandas as pd
import numpy as np
import cv2
import io

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Corretor de Gabarito", layout="centered", initial_sidebar_state="expanded")

st.title("📝 Corretor de Gabarito")

# --- CONFIGURAÇÕES DA PROVA ---
st.sidebar.header("⚙️ Configurações da Prova")
num_questoes = st.sidebar.number_input("Número de Questões", min_value=1, max_value=50, value=10, key="cfg_num_q")
num_opcoes = st.sidebar.selectbox("Quantidade de Alternativas", [4, 5], index=1, format_func=lambda x: "A-D (4)" if x == 4 else "A-E (5)", key="cfg_num_opt")

letras = ['A', 'B', 'C', 'D', 'E'][:num_opcoes]

# --- FUNÇÃO PARA GERAR O PDF DO GABARITO ---
def gerar_pdf_gabarito(q_total, opt_total):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter # 612 x 792 pontos

    anchor_size = 18

    # 1. Âncoras nos 4 cantos (Quadrados pretos síncronos)
    c.setFillColorRGB(0, 0, 0)
    c.rect(35, height - 53, anchor_size, anchor_size, fill=True, stroke=False)        # Topo Esquerdo
    c.rect(width - 53, height - 53, anchor_size, anchor_size, fill=True, stroke=False) # Topo Direito
    c.rect(35, 35, anchor_size, anchor_size, fill=True, stroke=False)                  # Base Esquerda
    c.rect(width - 53, 35, anchor_size, anchor_size, fill=True, stroke=False)           # Base Direita

    # 2. Cabeçalho
    c.setFont("Helvetica-Bold", 16)
    c.drawString(70, height - 42, "CARTÃO RESPOSTA")
    c.setFont("Helvetica", 9)
    c.drawString(70, height - 55, "Preencha completamente os círculos com caneta preta ou azul.")

    # 3. Campos de Nome do Estudante e Turma
    c.setFont("Helvetica-Bold", 10)
    c.drawString(70, height - 78, "NOME:")
    c.line(110, height - 80, 380, height - 80)
    
    c.drawString(400, height - 78, "TURMA:")
    c.line(450, height - 80, 530, height - 80)

    # 4. Grade de Frequência (Nº do Aluno: 2 dígitos - 0 a 9)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(70, height - 108, "Nº FREQUÊNCIA:")
    
    start_x = 70
    start_y = height - 128
    for col in range(2): # 2 dígitos
        for digit in range(10):
            x = start_x + (col * 35)
            y = start_y - (digit * 15)
            c.circle(x, y, 5, fill=False)
            c.setFont("Helvetica", 7)
            c.drawString(x - 2, y - 2, str(digit))

    # 5. Questões e Alternativas
    c.setFont("Helvetica-Bold", 10)
    c.drawString(200, height - 108, "RESPOSTAS:")

    y_q = height - 128
    x_q = 200
    for q in range(1, q_total + 1):
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x_q, y_q, f"{q:02d}:")

        for opt_idx in range(opt_total):
            x_circle = x_q + 25 + (opt_idx * 22)
            c.circle(x_circle, y_q + 3, 5, fill=False)
            c.setFont("Helvetica", 7)
            c.drawString(x_circle - 2, y_q + 1, letras[opt_idx])

        y_q -= 18
        if q % 25 == 0 and q < q_total:
            y_q = height - 128
            x_q += 150

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- BOTÃO DE GERAR GABARITO IMPRESSO ---
st.sidebar.divider()
st.sidebar.subheader("🖨️ Modelo da Folha")
pdf_bytes = gerar_pdf_gabarito(num_questoes, num_opcoes)
st.sidebar.download_button(
    label="📄 Baixar PDF do Gabarito",
    data=pdf_bytes,
    file_name=f"gabarito_{num_questoes}Q.pdf",
    mime="application/pdf",
    key="btn_download_pdf"
)

# --- DEFINIÇÃO DO GABARITO OFICIAL (LISTA VERTICAL ÚNICA) ---
st.subheader("1. Gabarito Oficial")
gabarito_oficial = []

for i in range(num_questoes):
    resp = st.selectbox(
        f"Questão {i+1:02d}", 
        letras, 
        key=f"gabarito_q_{i+1}"
    )
    gabarito_oficial.append(resp)

# --- INICIALIZAÇÃO DA SESSÃO ---
if "resultados" not in st.session_state:
    st.session_state.resultados = []

st.divider()

# --- LEITURA DO GABARITO DO ALUNO ---
st.subheader("2. Corrigir Cartão Resposta")

st.write("📌 *Ao abrir a câmera pela primeira vez, permita o acesso no seu navegador.*")
foto = st.camera_input("Capturar Gabarito", key="camera_input_aluno")

if foto is not None:
    bytes_data = foto.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

    numero_aluno = st.text_input("Nº Frequência:", key="input_num_aluno")
    nome_aluno = st.text_input("Nome do Aluno (Opcional):", key="input_nome_aluno")

    if st.button("💾 Salvar Correção", key="btn_salvar_nota"):
        if not numero_aluno:
            st.warning("Insira o número da frequência antes de salvar.")
        else:
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
