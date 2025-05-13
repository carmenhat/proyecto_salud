import os
from typing import Dict, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from pathlib import Path
import logging
from dotenv import load_dotenv
import json
import streamlit as st
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleFitAuth:
    def __init__(self):
        try:
            # Forzar el uso de la URI de redirección para Streamlit
            self.redirect_uri = "https://proyectosalud.streamlit.app"
            logger.info(f"Redirect URI forzado a: {self.redirect_uri}")
            
            self.client_id = os.getenv('GOOGLE_CLIENT_ID')
            self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
            
            if not all([self.client_id, self.client_secret]):
                logger.error("Faltan variables de entorno necesarias")
                raise ValueError("Faltan variables de entorno necesarias")
            
            self.scopes = [
                'https://www.googleapis.com/auth/fitness.activity.read',
                'https://www.googleapis.com/auth/fitness.heart_rate.read',
                'https://www.googleapis.com/auth/fitness.sleep.read',
                'https://www.googleapis.com/auth/fitness.body.read'
            ]
            
            
        except Exception as e:
            logger.error(f"Error al inicializar GoogleFitAuth: {str(e)}")
            raise

    def get_authorization_url(self) -> str:
        """Obtiene la URL de autorización para el flujo OAuth2."""
        try:
            # Verificar que estamos usando la configuración correcta
            logger.info(f"Usando redirect_uri: {self.redirect_uri}")
            
            client_config = {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            }
            logger.info(f"Configuración del cliente: {client_config}")
            
            flow = Flow.from_client_config(
                client_config,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri  # Asegurarnos de que se establece aquí también
            )
            
            authorization_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            logger.info(f"URL de autorización generada: {authorization_url}")
            return authorization_url
        except Exception as e:
            logger.error(f"Error al generar URL de autorización: {str(e)}")
            raise

    def get_credentials(self, code: str) -> Credentials:
        """Obtiene credenciales y las guarda en session_state"""
        try:
            flow = Flow.from_client_config(
                client_config={
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Serializar para session_state
            creds_dict = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            st.session_state['google_fit_creds'] = creds_dict
            logger.info("Credenciales guardadas en session_state")
            return credentials
            
        except Exception as e:
            logger.error(f"Error al obtener credenciales: {str(e)}")
            raise

    def load_credentials(self) -> Optional[Credentials]:
        """Carga credenciales desde session_state y refresca si es necesario"""
        try:
            if 'google_fit_creds' not in st.session_state:
                logger.info("No hay credenciales en session_state")
                return None

            # Cargar desde sesión
            creds_dict = st.session_state['google_fit_creds']
            # Construir manualmente las credenciales
            credentials = Credentials(
                token=creds_dict['token'],
                refresh_token=creds_dict['refresh_token'],
                token_uri=creds_dict['token_uri'],
                client_id=creds_dict['client_id'],
                client_secret=creds_dict['client_secret'],
                scopes=creds_dict['scopes'],
                expiry=datetime.fromisoformat(creds_dict['expiry'])  # Parsear datetime
            )


            # Refrescar token si está expirado
            if credentials.expired and credentials.refresh_token:
                logger.info("Refrescando token expirado...")
                credentials.refresh(Request())
            
                # Actualizar session_state con nuevo token
                self._save_credentials_to_session(credentials)
                logger.info("Token refrescado y guardado")

            return credentials

        except Exception as e:
            logger.error(f"Error cargando credenciales: {str(e)}")
            del st.session_state['google_fit_creds']  # Limpiar credenciales inválidas
            return None

    def _save_credentials_to_session(self, credentials: Credentials) -> None:
        """Guarda credenciales serializadas en session_state"""
        st.session_state['google_fit_creds'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() 
        }
    



    def get_fit_service(self) -> Optional[object]:
        """Obtiene el servicio de Google Fit."""
        try:
            credentials = self.load_credentials()
            if not credentials:
                logger.info("No hay credenciales disponibles")
                return None
                
            service = build('fitness', 'v1', credentials=credentials)
            logger.info("Servicio de Google Fit creado correctamente")
            return service
        except Exception as e:
            logger.error(f"Error al crear servicio de Google Fit: {str(e)}")
            return None 