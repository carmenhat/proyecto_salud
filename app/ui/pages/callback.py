import streamlit as st
import logging
from app.api.google_fit_auth import GoogleFitAuth

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    st.title("Autenticación de Google Fit")
    
    try:
        # Obtener el código de autorización de la URL
        query_params = st.query_params
        code = query_params.get("code", [None])[0]
        state = query_params.get("state", [None])[0]
        
        if not code:
            st.error("No se recibió el código de autorización")
            return
            
        # Inicializar el servicio de autenticación
        auth = GoogleFitAuth()
        
        # Obtener las credenciales
        credentials = auth.get_credentials(code)
        
        if credentials:
            st.success("¡Autenticación exitosa!")
            st.info("Puedes cerrar esta ventana y volver a la aplicación principal.")
        else:
            st.error("Error al obtener las credenciales")
            
    except Exception as e:
        logger.error(f"Error en la página de callback: {str(e)}")
        st.error(f"Ha ocurrido un error: {str(e)}")

if __name__ == "__main__":
    main() 