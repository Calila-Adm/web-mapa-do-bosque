"""
Estilos CSS e HTML para o menu do usuário e popup
"""

def get_user_button_css():
    """
    Retorna CSS para o botão do menu do usuário
    """
    return """
    <style>
    .user-button-container {
        position: fixed !important;
        top: 15px !important;
        left: 20px !important;
        z-index: 999999 !important;
    }

    button[key="user_button"] {
        width: 50px !important;
        height: 50px !important;
        border-radius: 50% !important;
        background-color: #FCB521 !important;
        border: 3px solid #ffffff !important;
        cursor: pointer !important;
        font-size: 24px !important;
        color: #000000 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
        transition: all 0.3s ease !important;
        position: fixed !important;
        top: 15px !important;
        left: 20px !important;
        z-index: 999999 !important;
    }

    button[key="user_button"]:hover {
        background-color: #E5A61F !important;
        transform: scale(1.1) !important;
    }
    </style>
    """


def get_logout_button_css():
    """
    Retorna CSS para posicionar o botão de logout
    """
    return """
    <style>
    button[key="logout_popup"] {
        position: fixed !important;
        top: 120px !important;
        left: 35px !important;
        z-index: 999999 !important;
        width: 130px !important;
    }
    </style>
    """