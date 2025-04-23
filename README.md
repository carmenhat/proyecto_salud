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
│   ├── api/              # Integración con Google Fit API
│   ├── core/             # Lógica principal de la aplicación
│   ├── models/           # Modelos de datos
│   ├── services/         # Servicios de análisis y recomendaciones
│   └── ui/               # Interfaz de usuario con Streamlit
├── tests/                # Pruebas unitarias y de integración
├── config/               # Configuraciones y variables de entorno
├── data/                 # Datos y scripts de inicialización
├── docs/                 # Documentación adicional
├── requirements.txt      # Dependencias del proyecto
└── Dockerfile           # Configuración de Docker
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
streamlit run app/ui/main.py
```

Esto iniciará la aplicación y te permitirá interactuar con la interfaz de usuario.
