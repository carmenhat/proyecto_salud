# Health & Fitness Analytics App

Aplicación de análisis de salud y fitness que integra datos de Google Fit para proporcionar insights personalizados y seguimiento de objetivos.

## Características

- Integración con Google Fit API
- Dashboard interactivo con Streamlit
- Análisis de datos con Pandas y Plotly
- Sistema de recomendaciones personalizadas
- Seguimiento de objetivos y progreso
- Visualización de métricas de salud

## Estructura del Proyecto

```
health-fitness-app/
├── app/
│ ├── api/ # Conexión segura con Google Fit (autenticación y obtención de datos)
│ │ ├── google_fit_auth.py # Gestión de autenticación OAuth2
│ │ └── google_fit_data.py # Obtención y procesamiento de datos de Google Fit
│ ├── services/ # Análisis y generación de recomendaciones personalizadas
│ │ ├── data_analysis.py # Procesamiento y análisis de datos de salud
│ │ └── recommendations.py # Generación de recomendaciones basadas en datos
│ └── ui/ # Interfaz de usuario desarrollada con Streamlit
│ └── pages/ # Páginas de la aplicación
│ ├── callback.py # Gestión de callbacks de autenticación
│ └── main.py # Página principal y dashboard
├── .env.example # Plantilla para variables de entorno
├── .gitignore # Configuración de archivos ignorados por Git
├── Dockerfile # Configuración para contenerización con Docker
├── README.md # Documentación principal del proyecto
├── guia_google_fit.md # Guía específica para la integración con Google Fit
└── requirements.txt # Dependencias necesarias para el proyecto
```
```

## Configuración Inicial

1. Crear un entorno virtual:
```bash
python -m venv venv
```

2. Activar el entorno virtual:
```powershell
.\venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
- Crear un archivo `.env`

## Ejecución de la Aplicación

Para ejecutar la aplicación, primero asegúrate de que el entorno virtual esté activo y luego ejecuta el siguiente comando:

```bash
streamlit run app/ui/main.py --server.port 8504
```

Esto iniciará la aplicación y te permitirá interactuar con la interfaz de usuario.
