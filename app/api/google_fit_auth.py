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

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleFitAuth:
    def __init__(self):
        try:
            # Forzar el uso del puerto 8504
            self.redirect_uri = "http://localhost:8504/callback"
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
            
            # Crear directorio tokens en el directorio del proyecto
            project_root = Path(__file__).parent.parent.parent
            self.token_path = project_root / 'tokens' / 'google_fit_token.pickle'
            self.token_path.parent.mkdir(exist_ok=True)
            
            logger.info(f"GoogleFitAuth inicializado correctamente. Token path: {self.token_path}")
            
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
        """Obtiene las credenciales usando el código de autorización."""
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            flow.fetch_token(code=code)
            credentials = flow.credentials
            self._save_credentials(credentials)
            logger.info("Credenciales obtenidas y guardadas correctamente")
            return credentials
        except Exception as e:
            logger.error(f"Error al obtener credenciales: {str(e)}")
            raise

    def _save_credentials(self, credentials: Credentials) -> None:
        """Guarda las credenciales en un archivo pickle."""
        try:
            with open(self.token_path, 'wb') as token:
                pickle.dump(credentials, token)
            logger.info("Credenciales guardadas correctamente")
        except Exception as e:
            logger.error(f"Error al guardar credenciales: {str(e)}")
            raise

    def load_credentials(self) -> Optional[Credentials]:
        """Carga las credenciales desde el archivo pickle."""
        try:
            if not self.token_path.exists():
                logger.info("No se encontraron credenciales guardadas")
                return None
            
            with open(self.token_path, 'rb') as token:
                credentials = pickle.load(token)
                
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                self._save_credentials(credentials)
                logger.info("Credenciales actualizadas correctamente")
                
            return credentials
        except Exception as e:
            logger.error(f"Error al cargar credenciales: {str(e)}")
            return None

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