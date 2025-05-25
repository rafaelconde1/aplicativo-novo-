import streamlit as st
import pandas as pd
import json
import os
import datetime
import base64
from io import BytesIO
import pytz # Importar pytz

# Configurações da página
st.set_page_config(
    page_title="Genial Tecnologia",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Caminhos dos arquivos
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
SCANS_FILE = os.path.join(DATA_DIR, "scans.csv")
LOGO_PATH = "images/logo.png"

# Cores
DOURADO = "#D4AF37"
BRANCO = "#FFFFFF"
CINZA_CLARO = "#F5F5F5"

# Definir o fuso horário de Brasília
BR_TIMEZONE = pytz.timezone("America/Sao_Paulo")

# Garantir que os diretórios e arquivos existam
os.makedirs(DATA_DIR, exist_ok=True)

# Inicializar arquivo de usuários se não existir
if not os.path.exists(USERS_FILE):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump({
                "admin": {"password": "genial2025", "is_admin": True},
                "joao123": {"password": "senha123", "is_admin": False},
                "maria456": {"password": "senha456", "is_admin": False},
                "teste789": {"password": "senha789", "is_admin": False}
            }, f, indent=4)
    except Exception as e:
        print(f"Erro ao inicializar {USERS_FILE}: {e}")

# Inicializar arquivo de registros se não existir
if not os.path.exists(SCANS_FILE):
    try:
        with open(SCANS_FILE, "w") as f:
            f.write("username,barcode,timestamp\n")
    except Exception as e:
        print(f"Erro ao inicializar {SCANS_FILE}: {e}")

# Funções de utilidade
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error("Erro ao carregar usuários: {}".format(e))
        return {"admin": {"password": "genial2025", "is_admin": True}} # Retorna admin padrão em caso de erro

def save_users(users):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=4) # Adiciona indentação para legibilidade
        return True
    except Exception as e:
        st.error("Erro ao salvar usuários: {}".format(e))
        return False

def load_scans():
    try:
        # Adicionar parse_dates para tentar converter timestamp ao carregar
        return pd.read_csv(SCANS_FILE, parse_dates=["timestamp"])
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=["username", "barcode", "timestamp"])
    except Exception as e:
        st.error("Erro ao carregar scans.csv: {}".format(e))
        # Tentar ler sem parse_dates como fallback
        try:
             return pd.read_csv(SCANS_FILE)
        except Exception:
             return pd.DataFrame(columns=["username", "barcode", "timestamp"])

def save_scan(username, barcode):
    # Verificar se o código de barras é válido (não vazio e não é um objeto interno)
    if not barcode or not isinstance(barcode, str) or "DeltaGenerator" in barcode:
        st.warning("Código de barras inválido ou vazio recebido: {}".format(barcode))
        return False
    
    # Corrigido: Obter horário atual no fuso de Brasília
    timestamp_br = datetime.datetime.now(BR_TIMEZONE)
    timestamp_str = timestamp_br.strftime("%Y-%m-%d %H:%M:%S")
    
    # Log para depuração
    if "debug_log" not in st.session_state:
        st.session_state["debug_log"] = []
    # Usar .format() para segurança
    st.session_state["debug_log"].append("Salvando registro: {}, {}, {}".format(username, barcode, timestamp_str))
    
    # Verificar se o arquivo existe e tem cabeçalho
    file_exists = os.path.isfile(SCANS_FILE) and os.path.getsize(SCANS_FILE) > 0
    
    try:
        with open(SCANS_FILE, "a") as f:
            if not file_exists:
                f.write("username,barcode,timestamp\n")
            # Usar .format() para segurança
            f.write("{},{},{}\n".format(username, barcode, timestamp_str))
        st.session_state["debug_log"].append("Registro salvo com sucesso!")
        return True
    except Exception as e:
        st.error("Erro ao salvar no arquivo scans.csv: {}".format(e))
        st.session_state["debug_log"].append("Falha ao salvar registro: {}".format(e))
        return False

def clear_scans(username=None):
    try:
        df = load_scans()
        if username:
            # Garantir que a coluna username exista antes de filtrar
            if "username" in df.columns:
                df = df[df.username != username]
            else:
                 st.warning("Coluna 'username' não encontrada no arquivo de scans para limpar.")
                 return False # Ou retornar True se não houver nada a limpar?
        else:
            df = pd.DataFrame(columns=["username", "barcode", "timestamp"])
        df.to_csv(SCANS_FILE, index=False)
        return True
    except Exception as e:
        st.error("Erro ao limpar registros: {}".format(e))
        return False

def get_csv_download_link(df, filename="dados.csv"):
    try:
        csv = df.to_csv(index=False)
        # Usar st.download_button para melhor compatibilidade
        return st.download_button(
            label="Baixar CSV",
            data=csv,
            file_name=filename,
            mime="text/csv",
        )
    except Exception as e:
        st.error("Erro ao gerar link de download: {}".format(e))
        return None

def add_logo():
    if os.path.exists(LOGO_PATH):
        st.sidebar.image(LOGO_PATH, width=150)
    else:
        st.sidebar.warning("Logo não encontrado em {}".format(LOGO_PATH))
        st.sidebar.title("Genial Tecnologia")

# Estilo CSS personalizado
def apply_custom_style():
    # Corrigido: Usar .format() para evitar problemas com f-string
    reader_id_css = "reader_{}".format(st.session_state.get("username", "nouser"))
    # Usar .format() para a string CSS principal também
    css = """
    <style>
    .stApp {{
        background-color: {BRANCO};
    }}
    .stButton>button {{
        background-color: {DOURADO};
        color: {BRANCO};
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        cursor: pointer;
    }}
    .stButton>button:hover {{
        background-color: #B8860B;
    }}
    h1, h2, h3 {{
        color: {DOURADO};
    }}
    .sidebar .sidebar-content {{
        background-color: {CINZA_CLARO};
    }}
    #scanned-result-js {{
        font-size: 0.9em;
        color: grey;
        margin-top: 10px;
        padding: 5px;
        border: 1px solid #eee;
        min-height: 40px; /* Para garantir visibilidade */
        word-wrap: break-word; /* Para quebrar linhas longas de erro */
    }}
    #{reader_id_css} {{
         border: 1px solid #eee; /* Adiciona borda para visualização */
         min-height: 250px; /* Altura mínima para o container do scanner */
         background-color: #fafafa; /* Fundo claro para área do scanner */
    }}
    </style>
    """.format(BRANCO=BRANCO, DOURADO=DOURADO, CINZA_CLARO=CINZA_CLARO, reader_id_css=reader_id_css)
    st.markdown(css, unsafe_allow_html=True)

# Inicializar estado da sessão (se não existir)
def initialize_session_state():
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("username", None)
    st.session_state.setdefault("is_admin", False)
    st.session_state.setdefault("admin_page", "Dashboard")
    st.session_state.setdefault("debug_log", [])
    st.session_state.setdefault("scanner_active", False)
    st.session_state.setdefault("scan_result", None)

# Função para o componente HTML5 QR Code (com mais logs e verificações para mobile)
def html5_qrcode_component():
    # Corrigido: Usar .format() para evitar problemas com f-string
    reader_id = "reader_{}".format(st.session_state.get("username", "nouser"))
    
    # Usar .format() para as partes HTML
    html_part1 = """
    <div id="{reader_id}" style="width: 100%; max-width: 500px; margin: auto;"></div>
    <div id="scanned-result-js" style="word-wrap: break-word;">Aguardando inicialização do scanner...</div> 
    <script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
    <script>
    """.format(reader_id=reader_id)
    
    # Código JavaScript com logs detalhados e tratamento de erro para câmera
    # Otimização: Remover setTimeout desnecessários e iniciar scanner mais cedo
    javascript_code = """
        var html5QrcodeScanner;
        const readerElement = document.getElementById("READER_ID_PLACEHOLDER");
        const resultElement = document.getElementById("scanned-result-js");

        function verboseLog(message) {
            console.log(message);
        }

        function displayError(message, error) {
            console.error(message, error);
            if (resultElement) {
                let errorMsg = message;
                if (error) {
                    errorMsg += ": " + error.toString();
                }
                if (error && (error.name === "NotAllowedError" || error.name === "PermissionDeniedError")) {
                    errorMsg += " Por favor, verifique as permissões da câmera para este site nas configurações do seu navegador.";
                } else if (error && error.name === "NotFoundError") {
                     errorMsg += " Nenhuma câmera compatível foi encontrada.";
                }
                resultElement.innerText = errorMsg;
            }
        }

        function sendToStreamlit(decodedText) {
            if (!decodedText || decodedText.trim() === ") {
                verboseLog("Código inválido ou vazio ignorado.");
                return;
            }
            verboseLog("Enviando para Streamlit: " + decodedText);
            try {
                Streamlit.setComponentValue({
                    barcode: decodedText,
                    timestamp: new Date().toISOString()
                });
            } catch (e) {
                displayError("Erro ao enviar dados para Streamlit", e);
            }
        }

        function onScanSuccess(decodedText, decodedResult) {
            verboseLog(`Código lido: ${decodedText}`); 
            resultElement.innerText = "Código lido: " + decodedText;
            sendToStreamlit(decodedText);
        }

        function onScanFailure(error) {
            if (error && error.name !== "NotFoundException") { 
                 verboseLog(`Scan failure: ${error}`);
            }
        }

        function startScanner() {
            verboseLog("Iniciando startScanner()...");
            if (!readerElement) {
                displayError("Erro crítico: Elemento reader não encontrado!");
                return;
            }
            resultElement.innerText = "Solicitando permissão da câmera...";

            // Tentar obter permissão e iniciar mais rapidamente
            Html5Qrcode.getCameras().then(cameras => {
                verboseLog("Permissão da câmera obtida. Câmeras encontradas: " + cameras.length);
                if (cameras && cameras.length) {
                    resultElement.innerText = "Câmera(s) encontrada(s). Iniciando scanner...";
                    
                    if (html5QrcodeScanner && html5QrcodeScanner.isScanning) {
                        verboseLog("Scanner já ativo, limpando instância anterior...");
                        try {
                            html5QrcodeScanner.stop().catch(err => verboseLog("Aviso ao parar scanner anterior: " + err));
                        } catch (e) {
                            verboseLog("Exceção ao parar scanner anterior: " + e);
                        }
                    }

                    html5QrcodeScanner = new Html5QrcodeScanner(
                        "READER_ID_PLACEHOLDER", 
                        { 
                            fps: 10, 
                            qrbox: { width: 250, height: 250 },
                            rememberLastUsedCamera: true, 
                            supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA],
                            showTorchButtonIfSupported: true,
                            facingMode: "environment" 
                        },
                        false);
                    
                    verboseLog("Renderizando scanner...");
                    html5QrcodeScanner.render(onScanSuccess, onScanFailure);
                    resultElement.innerText = "Scanner pronto. Aponte para o código.";

                } else {
                    displayError("Nenhuma câmera encontrada após obter permissão.");
                }
            }).catch(err => {
                displayError("Erro ao acessar a câmera", err);
            });
        }
        
        window.stopScanner = function() {
            verboseLog("Tentando parar o scanner via stopScanner()...");
            if (html5QrcodeScanner) { 
                 try {
                     html5QrcodeScanner.stop()
                        .then(() => {
                            verboseLog("Scanner parado com sucesso via stop().");
                            resultElement.innerText = "Scanner parado.";
                        })
                        .catch((err) => {
                            verboseLog("stop() falhou, tentando clear(): " + err);
                            html5QrcodeScanner.clear().catch(e => {}); 
                            resultElement.innerText = "Scanner parado (após falha no stop).";
                        });
                 } catch (e) {
                     verboseLog("Exceção ao chamar stop(), tentando clear(): " + e);
                     try {
                        html5QrcodeScanner.clear().catch(e => {}); 
                        resultElement.innerText = "Scanner parado (após exceção no stop).";
                     } catch (e2) {
                         displayError("Falha crítica ao parar/limpar scanner", e2);
                     }
                 }
            } else {
                verboseLog("Nenhuma instância do scanner para parar.");
                resultElement.innerText = "Scanner não iniciado.";
            }
        };

        // Otimização: Tentar iniciar o scanner mais cedo, sem setTimeout
        if (document.readyState === "complete" || document.readyState === "interactive") {
            startScanner(); 
        } else {
            document.addEventListener("DOMContentLoaded", startScanner);
        }

    """.replace("READER_ID_PLACEHOLDER", reader_id)

    html_part2 = """
    </script>
    """
    
    # Concatenar as partes
    final_html_code = html_part1 + javascript_code + html_part2
    
    # Componente HTML
    component_value = st.components.v1.html(
        final_html_code,
        height=500, 
        scrolling=False
    )
    
    return component_value

# Função de login
def login_page():
    st.title("Genial Tecnologia")
    st.subheader("Sistema de Leitura de Códigos de Barras")
    
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            users = load_users()
            if username in users and users[username]["password"] == password:
                keys_to_keep = [] 
                for key in list(st.session_state.keys()):
                    if key not in keys_to_keep:
                        del st.session_state[key]
                initialize_session_state() 
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["is_admin"] = users[username].get("is_admin", False)
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos!")

# Função para o painel do usuário
def user_page():
    st.sidebar.title("Menu")
    
    menu_option = st.sidebar.radio(
        "Navegação",
        ["Escanear Código", "Meus Registros", "Logout"],
        key="user_menu",
        label_visibility="collapsed"
    )
    
    if menu_option == "Logout":
        if st.session_state.get("scanner_active", False):
             # Corrigido: Usar aspas simples externas e duplas internas
             st.components.v1.html('<script> try { if(typeof stopScanner === "function") stopScanner(); } catch(e) { console.error("Error stopping scanner on logout:", e); } </script>', height=0)
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        initialize_session_state()
        st.rerun()
    
    # Usar .format() para segurança
    st.title("Bem-vindo, {}".format(st.session_state.get("username", "Usuário")))
    
    if menu_option == "Escanear Código":
        st.header("Escaneie um código de barras")
        
        col1, col2 = st.columns(2)
        
        if col1.button("Iniciar/Reiniciar Scanner"):
            st.session_state["scanner_active"] = True
            st.session_state["scan_result"] = None
            st.rerun() 
        
        if col2.button("Parar Scanner"):
            if st.session_state.get("scanner_active", False):
                # Corrigido: Usar aspas simples externas e duplas internas
                st.components.v1.html("<script> try { if(typeof stopScanner === 'function') stopScanner(); } catch(e) { console.error('Error stopping scanner manually:', e); } </script>", height=0)
                st.session_state["scanner_active"] = False
            st.session_state["scan_result"] = None
            st.rerun()
        
        if st.session_state.get("scanner_active", False):
            st.info("Aponte a câmera para o código de barras. Pode ser necessário conceder permissão ao navegador.")
            component_value = html5_qrcode_component()
            
            if component_value and component_value != st.session_state.get("scan_result"):
                st.session_state["scan_result"] = component_value 
                try:
                    barcode = component_value.get("barcode")
                    if barcode:
                        # Usar .format() para segurança
                        st.session_state["debug_log"].append("Código recebido do JS: {}".format(barcode))
                        if save_scan(st.session_state["username"], barcode):
                            # Usar .format() para segurança
                            st.success("Código de barras registrado: {}".format(barcode))
                        else:
                            st.error("Falha ao registrar o código de barras. Verifique os logs.")
                    else:
                         st.warning("Valor recebido do scanner não continha código de barras.")

                except Exception as e:
                    # Usar .format() para segurança
                    st.error("Erro ao processar o código recebido: {}".format(str(e)))
                    st.session_state["debug_log"].append("Erro Python ao processar: {}".format(str(e)))
        else:
            st.warning("Scanner parado. Clique em 'Iniciar/Reiniciar Scanner' para começar.")

        with st.expander("Registro manual (para testes)"):
            manual_code = st.text_input("Digite um código de barras manualmente", key="manual_code_input")
            if st.button("Registrar código manual", key="manual_code_button"):
                if manual_code:
                    if save_scan(st.session_state["username"], manual_code):
                        # Usar .format() para segurança
                        st.success("Código de barras registrado manualmente: {}".format(manual_code))
                    else:
                        st.error("Erro ao registrar o código de barras manual.")
                else:
                    st.warning("Digite um código para registrar manualmente.")
        
        with st.expander("Dicas para Escanear"):
            st.markdown("""
            1. **Iluminação:** Garanta boa luz sobre o código.
            2. **Foco:** Mantenha a imagem nítida.
            3. **Distância:** Aproxime ou afaste o código até a câmera focar.
            4. **Ângulo:** Evite reflexos e sombras.
            5. **Permissão:** Permita o acesso à câmera no navegador.
            """)
    
    elif menu_option == "Meus Registros":
        st.header("Meus registros de leitura")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 Atualizar Registros"):
                st.rerun()
        
        with col2:
            if st.button("🗑️ Limpar Meus Registros"):
                if clear_scans(st.session_state.get("username")):
                    st.success("Seus registros foram limpos com sucesso!")
                    st.rerun()
                else:
                    st.error("Falha ao limpar seus registros.")
        
        df = load_scans()
        if "username" in df.columns and st.session_state.get("username"):
            user_scans = df[df.username == st.session_state.get("username")]
        else:
            user_scans = pd.DataFrame(columns=df.columns)

        if not user_scans.empty:
            # Tentar converter para datetime e aplicar fuso horário para exibição
            try:
                if not pd.api.types.is_datetime64_any_dtype(user_scans["timestamp"]):
                    user_scans["timestamp"] = pd.to_datetime(user_scans["timestamp"], errors="coerce")
                
                # Assume que o timestamp salvo está em BRT (já que corrigimos o save_scan)
                # Apenas formatar para exibição
                user_scans_display = user_scans.copy()
                user_scans_display["timestamp"] = user_scans_display["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                st.warning(f"Erro ao formatar timestamp para exibição: {e}")
                user_scans_display = user_scans # Exibir como está se houver erro

            st.dataframe(user_scans_display.rename(columns={"username":"Usuário", "barcode":"Código", "timestamp":"Data/Hora"}))
            get_csv_download_link(user_scans, "meus_registros.csv")
            # Usar .format() para segurança
            st.info("Total de leituras realizadas: {}".format(len(user_scans)))
        else:
            st.warning("Você ainda não realizou nenhuma leitura de código de barras.")

# Função para o painel do administrador
def admin_page():
    st.sidebar.title("Menu Admin")
    
    menu_option = st.sidebar.radio(
        "Navegação Admin",
        ["Dashboard", "Usuários", "Todos os Registros", "Logout"],
        key="admin_menu",
        label_visibility="collapsed"
    )
    
    if menu_option == "Logout":
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        initialize_session_state()
        st.rerun()
    
    st.session_state["admin_page"] = menu_option 
    
    if menu_option == "Dashboard":
        st.title("Painel Administrativo")
        
        if st.button("🔄 Atualizar Dados"):
            st.rerun()
        
        with st.expander("Informações de Depuração"):
            # Usar .format() para segurança
            st.code("Arquivo de registros: {}".format(SCANS_FILE))
            st.code("Arquivo de usuários: {}".format(USERS_FILE))
            st.code("Logs de depuração: {}".format(st.session_state.get("debug_log", [])))
        
        df = load_scans()
        
        if not df.empty and "username" in df.columns and "timestamp" in df.columns:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Registros", len(df))
            
            with col2:
                st.metric("Usuários Ativos", df["username"].nunique())
            
            with col3:
                try:
                    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
                         df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
                    
                    # Calcular registros de hoje considerando o fuso de Brasília
                    hoje_br = datetime.datetime.now(BR_TIMEZONE).date()
                    registros_hoje = len(df[df["timestamp"].dt.tz_localize(BR_TIMEZONE.zone).dt.date == hoje_br])
                except Exception as e:
                    # Usar .format() para segurança
                    st.warning("Erro ao calcular registros de hoje: {}".format(e))
                    registros_hoje = "N/A"
                st.metric("Registros Hoje", registros_hoje)
            
            st.subheader("Registros por Usuário")
            try:
                user_counts = df["username"].value_counts().reset_index()
                user_counts.columns = ["Usuário", "Registros"]
                st.bar_chart(user_counts.set_index("Usuário"))
            except Exception as e:
                 # Usar .format() para segurança
                 st.error("Erro ao gerar gráfico de registros por usuário: {}".format(e))
        else:
            st.warning("Não há registros ou colunas esperadas no sistema para exibir estatísticas.")
    
    elif menu_option == "Usuários":
        st.title("Gerenciamento de Usuários")
        
        users = load_users()
        usernames_list = sorted(list(users.keys()))
        usernames_list_no_admin = sorted([u for u in users.keys() if u != "admin"])

        with st.expander("Adicionar Novo Usuário"):
            with st.form("add_user_form"):
                new_username = st.text_input("Nome de Usuário")
                new_password = st.text_input("Senha", type="password")
                is_admin = st.checkbox("É Administrador?")
                submit_add = st.form_submit_button("Adicionar Usuário")
                
                if submit_add:
                    if not new_username or not new_password:
                        st.error("Nome de usuário e senha são obrigatórios.")
                    elif new_username in users:
                        # Usar .format() para segurança
                        st.error("Usuário 	{}	 já existe!".format(new_username))
                    else:
                        users[new_username] = {"password": new_password, "is_admin": is_admin}
                        if save_users(users):
                            # Usar .format() para segurança
                            st.success("Usuário {} adicionado com sucesso!".format(new_username))
                            st.rerun()
                        else:
                            st.error("Falha ao salvar novo usuário.")
        
        with st.expander("Alterar Nome de Usuário"):
            with st.form("change_username_form"):
                old_username = st.selectbox("Selecione o Usuário Atual", usernames_list, key="change_uname_select")
                new_username_change = st.text_input("Novo Nome de Usuário", key="change_uname_new")
                submit_change_uname = st.form_submit_button("Alterar Nome")
                
                if submit_change_uname:
                    if not old_username or not new_username_change:
                         st.error("Selecione o usuário atual e digite o novo nome.")
                    elif old_username not in users:
                         st.error("Usuário selecionado não existe mais.")
                    elif new_username_change in users:
                        # Usar .format() para segurança
                        st.error("O novo nome de usuário 	{}	 já existe!".format(new_username_change))
                    else:
                        users[new_username_change] = users.pop(old_username)
                        if save_users(users):
                            df_scans = load_scans()
                            if not df_scans.empty and "username" in df_scans.columns:
                                df_scans.loc[df_scans["username"] == old_username, "username"] = new_username_change
                                df_scans.to_csv(SCANS_FILE, index=False)
                            # Usar .format() para segurança
                            st.success("Nome de usuário alterado de {} para {}!".format(old_username, new_username_change))
                            st.rerun()
                        else:
                             st.error("Falha ao salvar alteração de nome de usuário.")
                             users[old_username] = users.pop(new_username_change)
        
        with st.expander("Alterar Senha"):
            with st.form("change_password_form"):
                username_pwd = st.selectbox("Selecione o Usuário", usernames_list, key="pwd_user")
                new_password_pwd = st.text_input("Nova Senha", type="password", key="pwd_new")
                submit_pwd = st.form_submit_button("Alterar Senha")
                
                if submit_pwd:
                    if not username_pwd or not new_password_pwd:
                        st.error("Selecione o usuário e digite a nova senha.")
                    elif username_pwd not in users:
                        st.error("Usuário selecionado não existe mais.")
                    else:
                        users[username_pwd]["password"] = new_password_pwd
                        if save_users(users):
                            # Usar .format() para segurança
                            st.success("Senha do usuário {} alterada com sucesso!".format(username_pwd))
                        else:
                            # Usar .format() para segurança
                            st.error("Falha ao salvar nova senha para {}.".format(username_pwd))
        
        with st.expander("Excluir Usuário"):
            with st.form("delete_user_form"):
                username_del = st.selectbox("Selecione o Usuário (exceto admin)", usernames_list_no_admin, key="del_user")
                confirm_del = st.checkbox("Confirmar exclusão", key="del_confirm")
                submit_del = st.form_submit_button("Excluir Usuário")
                
                if submit_del:
                    if not username_del:
                         st.error("Selecione um usuário para excluir.")
                    elif not confirm_del:
                        st.error("Marque a caixa para confirmar a exclusão.")
                    elif username_del == "admin":
                        st.error("Não é possível excluir o usuário administrador principal!")
                    elif username_del not in users:
                        st.error("Usuário selecionado não existe mais.")
                    else:
                        user_data_backup = users.pop(username_del) 
                        if save_users(users):
                            if clear_scans(username_del):
                                # Usar .format() para segurança
                                st.success("Usuário {} e seus registros foram excluídos com sucesso!".format(username_del))
                            else:
                                 # Usar .format() para segurança
                                 st.warning("Usuário {} excluído, mas houve falha ao limpar seus registros.".format(username_del))
                            st.rerun()
                        else:
                            # Usar .format() para segurança
                            st.error("Falha ao salvar a exclusão do usuário {}.".format(username_del))
                            users[username_del] = user_data_backup 
    
    elif menu_option == "Todos os Registros":
        st.title("Todos os Registros")
        
        if st.button("🔄 Atualizar Registros"):
            st.rerun()
        
        df = load_scans()
        
        if not df.empty and "username" in df.columns:
            st.subheader("Filtro e Tabela Geral")
            users_with_scans = sorted(df["username"].unique().tolist())
            users_options = ["Todos"] + users_with_scans
            selected_user = st.selectbox("Filtrar por usuário:", users_options, key="filter_user_select")
            
            col1_clear, col2_clear = st.columns(2)
            with col1_clear:
                 if st.button("🗑️ Limpar Todos os Registros"):
                    if clear_scans():
                        st.success("Todos os registros foram limpos com sucesso!")
                        st.rerun()
                    else:
                        st.error("Falha ao limpar todos os registros.")
            
            if selected_user != "Todos":
                filtered_df = df[df.username == selected_user]
                with col2_clear:
                    # Usar .format() para segurança
                    if st.button("🗑️ Limpar Registros de {}".format(selected_user)):
                        if clear_scans(selected_user):
                            # Usar .format() para segurança
                            st.success("Registros de {} limpos com sucesso!".format(selected_user))
                            st.rerun()
                        else:
                             # Usar .format() para segurança
                             st.error("Falha ao limpar registros de {}.".format(selected_user))
            else:
                filtered_df = df
            
            # Tentar converter para datetime e aplicar fuso horário para exibição
            try:
                if not pd.api.types.is_datetime64_any_dtype(filtered_df["timestamp"]):
                    filtered_df["timestamp"] = pd.to_datetime(filtered_df["timestamp"], errors="coerce")
                
                # Assume que o timestamp salvo está em BRT (já que corrigimos o save_scan)
                # Apenas formatar para exibição
                filtered_df_display = filtered_df.copy()
                filtered_df_display["timestamp"] = filtered_df_display["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                st.warning(f"Erro ao formatar timestamp para exibição: {e}")
                filtered_df_display = filtered_df # Exibir como está se houver erro

            st.dataframe(filtered_df_display.rename(columns={"username":"Usuário", "barcode":"Código", "timestamp":"Data/Hora"}))
            
            # Usar .format() para segurança
            get_csv_download_link(filtered_df, "registros_{}.csv".format(selected_user.lower()))
            
            # Usar .format() para segurança
            st.info("Total de registros exibidos na tabela: {}".format(len(filtered_df)))
            
            st.markdown("---")
            st.subheader("Registros Agrupados por Usuário")
            
            if not users_with_scans:
                 st.warning("Nenhum usuário com registros encontrados para agrupar.")
            else:
                for user in users_with_scans:
                    # Usar .format() para segurança
                    with st.expander("Registros de {}".format(user)):
                        user_df = df[df.username == user]
                        # Tentar converter para datetime e aplicar fuso horário para exibição
                        try:
                            if not pd.api.types.is_datetime64_any_dtype(user_df["timestamp"]):
                                user_df["timestamp"] = pd.to_datetime(user_df["timestamp"], errors="coerce")
                            
                            # Assume que o timestamp salvo está em BRT (já que corrigimos o save_scan)
                            # Apenas formatar para exibição
                            user_df_display = user_df.copy()
                            user_df_display["timestamp"] = user_df_display["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
                        except Exception as e:
                            st.warning(f"Erro ao formatar timestamp para exibição: {e}")
                            user_df_display = user_df # Exibir como está se houver erro

                        st.dataframe(user_df_display.rename(columns={"username":"Usuário", "barcode":"Código", "timestamp":"Data/Hora"}))
                        # Usar .format() para segurança
                        get_csv_download_link(user_df, "registros_{}.csv".format(user))
                        # Usar .format() para segurança
                        st.info("Total de registros para {}: {}".format(user, len(user_df)))
        
        elif "username" not in df.columns:
             st.error("Arquivo 'scans.csv' parece estar corrompido ou não contém a coluna 'username'.")
        else: 
            st.warning("Não há registros no sistema.")

# --- Controle Principal --- 
initialize_session_state()
apply_custom_style()
add_logo()

if not st.session_state.get("logged_in", False):
    login_page()
else:
    users_check = load_users()
    if st.session_state.get("username") not in users_check:
        st.error("Sua conta foi removida ou alterada. Por favor, faça login novamente.")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        initialize_session_state()
        st.rerun()
    elif st.session_state.get("is_admin", False):
        admin_page()
    else:
        user_page()

st.markdown("---")
st.markdown("© 2025 Genial Soluções. Todos os direitos reservados.")

