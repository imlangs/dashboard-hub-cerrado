import streamlit as st

st.set_page_config(
    page_title="Login - Hub Cerrado",
    page_icon="🔒",
    layout="centered"
)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "admin123" and st.session_state["username"] == "admin":
            st.session_state.authenticated = True
            del st.session_state["password"]  # Don't store the password
            st.rerun()
        else:
            st.session_state.authenticated = False
            st.error("😕 Usuário ou senha incorretos")

    st.title("🔒 Login Hub Cerrado")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("Logo-Hub-Cerrado_350x100-1.png.webp", width=350)
    
    st.write("Por favor, faça login para acessar o dashboard.")
    
    with st.form("login_form"):
        st.text_input("Usuário", key="username")
        st.text_input("Senha", type="password", key="password")
        st.form_submit_button("Login", on_click=password_entered)

def main():
    if st.session_state.authenticated:
        st.success("✅ Login realizado com sucesso!")
        st.write("Por favor, acesse o Dashboard no menu lateral.")
    else:
        check_password()

if __name__ == "__main__":
    main() 