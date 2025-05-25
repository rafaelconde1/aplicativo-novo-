import streamlit as st
import pandas as pd
import numpy as np
import cv2
from pyzbar.pyzbar import decode
import datetime
import os
import csv
import base64
import json
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Genial Tech",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Diretórios e arquivos
DATA_DIR = Path("../data")
USERS_FILE = DATA_DIR / "users.json"
SCANS_FILE = DATA_DIR / "scans.csv"

# Garantir que os diretórios e arquivos existam
DATA_DIR.mkdir(exist_ok=True)

# Inicializar arquivos se não existirem
if not USERS_FILE.exists():
    with open(USERS_FILE, "w") as f:
        json.dump({
            "admin": {
                "password": "genial2025",
                "is_admin": True
            },
            "joao123": {
                "password": "senha123",
                "is_admin": False
            },
            "maria456": {
                "password": "senha456",
                "is_admin": False
            },
            "teste789": {
                "password": "senha789",
                "is_admin": False
            }
        }, f)

if not SCANS_FILE.exists():
    with open(SCANS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "barcode", "timestamp"])

# Funções de autenticação
def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def authenticate(username, password):
    users = load_users()
    if username in users and users[username]["password"] == password:
        return users[username]["is_admin"]
    return None

# Funções para manipulação de dados
def save_scan(username, barcode):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SCANS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([username, barcode, timestamp])

def get_scans():
    if not os.path.exists(SCANS_FILE) or os.path.getsize(SCANS_FILE) == 0:
        return pd.DataFrame(columns=["username", "barcode", "timestamp"])
    return pd.read_csv(SCANS_FILE)

def get_csv_download_link(df, filename="dados.csv"):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" style="color:#D4AF37; text-decoration:none; padding:10px 15px; background-color:#FFFFFF; border:2px solid #D4AF37; border-radius:5px;">Baixar CSV</a>'
    return href

# Estilo personalizado
def apply_custom_style():
    st.markdown("""
    <style>
    .main {
        background-color: #FFFFFF;
    }
    .st-bw {
        background-color: #FFFFFF;
    }
    .st-bb {
        border-color: #D4AF37;
    }
    .st-at {
        background-color: #D4AF37;
    }
    .st-af {
        background-color: #D4AF37;
    }
    .stButton>button {
        background-color: #D4AF37;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stTextInput>div>div>input {
        border-color: #D4AF37;
        border-radius: 5px;
    }
    h1, h2, h3 {
        color: #D4AF37;
    }
    .sidebar .sidebar-content {
        background-color: #FFFFFF;
    }
    .css-1d391kg {
        background-color: #FFFFFF;
    }
    .css-12oz5g7 {
        padding: 2rem 1rem;
    }
    .block-container {
        padding-top: 2rem;
    }
    .metric-container {
        background-color: #FFFFFF;
        border: 1px solid #D4AF37;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
    }
    .metric-value {
        color: #D4AF37;
        font-size: 24px;
        font-weight: bold;
    }
    .metric-label {
        color: #333333;
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

# Aplicar estilo personalizado
apply_custom_style()

# Inicializar estado da sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Função para logout
def logout():
    st.session_state.authenticated = False
    st.session_state.is_admin = False
    st.session_state.username = ""

# Tela de login
def login_page():
    col_logo, col_space = st.columns([1, 2])
    
    with col_logo:
        st.image("https://via.placeholder.com/150x150.png?text=GT", width=150)
    
    st.markdown("<h1 style='text-align: center; color: #D4AF37;'>Genial Tech</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #666666;'>Sistema de Leitura de Códigos de Barras</h3>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div style='background-color: #FFFFFF; padding: 20px; border-radius: 10px; border: 1px solid #D4AF37;'>", unsafe_allow_html=True)
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("Entrar", key="login_btn"):
                auth_result = authenticate(username, password)
                if auth_result is not None:
                    st.session_state.authenticated = True
                    st.session_state.is_admin = auth_result
                    st.session_state.username = username
                    st.experimental_rerun()
                else:
                    st.error("Usuário ou senha incorretos")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; color: #666666;'>© 2025 Genial Tech. Todos os direitos reservados.</div>", unsafe_allow_html=True)

# Função para processar imagem e detectar código de barras
def process_barcode_image(img):
    # Converter para escala de cinza para melhorar a detecção
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aplicar um leve desfoque para reduzir ruído
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Tentar decodificar o código de barras
    barcodes = decode(blurred)
    
    if not barcodes:
        # Se não encontrou, tentar na imagem original
        barcodes = decode(img)
    
    return barcodes

# Página do usuário para escanear códigos de barras
def user_page():
    st.title(f"Bem-vindo, {st.session_state.username}")
    
    # Menu lateral
    with st.sidebar:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.image("https://via.placeholder.com/100x100.png?text=GT", width=100)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #D4AF37;'>Menu</h3>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color: #D4AF37;'>", unsafe_allow_html=True)
        
        if st.button("Escanear Código", key="scan_menu"):
            st.session_state.page = "scan"
        
        if st.button("Meus Registros", key="history_menu"):
            st.session_state.page = "history"
        
        st.markdown("<hr style='border-color: #D4AF37;'>", unsafe_allow_html=True)
        if st.button("Logout", key="logout_menu"):
            logout()
            st.experimental_rerun()
    
    # Inicializar a página se não existir
    if "page" not in st.session_state:
        st.session_state.page = "scan"
    
    # Conteúdo principal
    if st.session_state.page == "scan":
        st.subheader("Escaneie um código de barras")
        
        # Opção para upload de imagem com código de barras
        uploaded_file = st.file_uploader("Faça upload de uma imagem com código de barras", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            # Converter o arquivo para um formato que o OpenCV possa ler
            file_bytes = uploaded_file.getvalue()
            nparr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Mostrar a imagem
            st.image(uploaded_file, caption="Imagem carregada", width=400)
            
            # Processar e decodificar o código de barras
            barcodes = process_barcode_image(img)
            
            if barcodes:
                for barcode in barcodes:
                    barcode_data = barcode.data.decode('utf-8')
                    barcode_type = barcode.type
                    
                    # Desenhar um retângulo em volta do código de barras
                    (x, y, w, h) = barcode.rect
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    # Mostrar o resultado
                    st.success(f"Código de barras detectado!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Tipo:** {barcode_type}")
                    with col2:
                        st.markdown(f"**Valor:** {barcode_data}")
                    
                    # Salvar o scan
                    save_scan(st.session_state.username, barcode_data)
                    
                    st.balloons()
            else:
                st.error("Nenhum código de barras detectado na imagem. Tente outra imagem ou ajuste o ângulo/iluminação.")
        
        # Adicionar instruções para usar a câmera
        st.markdown("### Dicas para escanear códigos de barras:")
        st.markdown("""
        1. Certifique-se de que o código de barras esteja bem iluminado
        2. Evite reflexos ou sombras sobre o código
        3. Mantenha a imagem focada e sem borrões
        4. Posicione o código de barras de forma que ocupe boa parte da imagem
        """)
        
    elif st.session_state.page == "history":
        st.subheader("Meus registros de leitura")
        
        # Obter os scans do usuário
        all_scans = get_scans()
        user_scans = all_scans[all_scans["username"] == st.session_state.username]
        
        if user_scans.empty:
            st.info("Você ainda não realizou nenhuma leitura de código de barras.")
        else:
            # Mostrar estatísticas
            total_scans = len(user_scans)
            
            st.markdown(f"<div class='metric-container'><div class='metric-value'>{total_scans}</div><div class='metric-label'>Total de leituras realizadas</div></div>", unsafe_allow_html=True)
            
            # Mostrar tabela de registros
            st.dataframe(user_scans, use_container_width=True)
            
            # Link para download dos dados
            st.markdown(get_csv_download_link(user_scans, f"meus_registros.csv"), unsafe_allow_html=True)

# Página do administrador
def admin_page():
    st.title("Painel Administrativo")
    
    # Menu lateral
    with st.sidebar:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.image("https://via.placeholder.com/100x100.png?text=GT", width=100)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #D4AF37;'>Menu Admin</h3>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color: #D4AF37;'>", unsafe_allow_html=True)
        
        if st.button("Dashboard", key="dashboard_menu"):
            st.session_state.admin_page = "dashboard"
        
        if st.button("Usuários", key="users_menu"):
            st.session_state.admin_page = "users"
        
        if st.button("Todos os Registros", key="all_records_menu"):
            st.session_state.admin_page = "all_records"
        
        st.markdown("<hr style='border-color: #D4AF37;'>", unsafe_allow_html=True)
        if st.button("Logout", key="admin_logout_menu"):
            logout()
            st.experimental_rerun()
    
    # Inicializar a página se não existir
    if "admin_page" not in st.session_state:
        st.session_state.admin_page = "dashboard"
    
    # Obter todos os scans
    all_scans = get_scans()
    
    # Conteúdo principal
    if st.session_state.admin_page == "dashboard":
        st.subheader("Dashboard")
        
        if all_scans.empty:
            st.info("Nenhum registro de leitura encontrado")
        else:
            # Mostrar estatísticas
            total_scans = len(all_scans)
            unique_users = all_scans["username"].nunique()
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<div class='metric-container'><div class='metric-value'>{total_scans}</div><div class='metric-label'>Total de leituras</div></div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='metric-container'><div class='metric-value'>{unique_users}</div><div class='metric-label'>Usuários ativos</div></div>", unsafe_allow_html=True)
            
            # Mostrar gráfico de leituras por usuário
            st.subheader("Leituras por usuário")
            user_counts = all_scans["username"].value_counts().reset_index()
            user_counts.columns = ["Usuário", "Quantidade de leituras"]
            
            st.bar_chart(user_counts.set_index("Usuário"))
            
            # Mostrar os últimos registros
            st.subheader("Últimos registros")
            st.dataframe(all_scans.tail(10), use_container_width=True)
    
    elif st.session_state.admin_page == "users":
        st.subheader("Gerenciamento de Usuários")
        
        # Mostrar usuários ativos
        users = load_users()
        
        user_list = []
        for username, data in users.items():
            user_list.append({
                "Usuário": username,
                "Administrador": "Sim" if data["is_admin"] else "Não",
                "Leituras": len(all_scans[all_scans["username"] == username]) if not all_scans.empty else 0
            })
        
        user_df = pd.DataFrame(user_list)
        st.dataframe(user_df, use_container_width=True)
    
    elif st.session_state.admin_page == "all_records":
        st.subheader("Todos os Registros")
        
        if all_scans.empty:
            st.info("Nenhum registro de leitura encontrado")
        else:
            # Lista de usuários para filtro
            users = all_scans["username"].unique()
            selected_user = st.selectbox("Filtrar por usuário", ["Todos"] + list(users))
            
            if selected_user != "Todos":
                filtered_scans = all_scans[all_scans["username"] == selected_user]
                st.dataframe(filtered_scans, use_container_width=True)
                
                # Link para download dos dados filtrados
                st.markdown(get_csv_download_link(filtered_scans, f"dados_{selected_user}.csv"), unsafe_allow_html=True)
            else:
                # Mostrar todos os registros
                st.dataframe(all_scans, use_container_width=True)
                
                # Link para download de todos os dados
                st.markdown(get_csv_download_link(all_scans, "todos_dados.csv"), unsafe_allow_html=True)

# Roteamento principal
def main():
    if not st.session_state.authenticated:
        login_page()
    else:
        if st.session_state.is_admin:
            admin_page()
        else:
            user_page()

if __name__ == "__main__":
    main()
