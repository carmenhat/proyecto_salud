import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import sys
import logging
from pytz import timezone
from dotenv import load_dotenv

tz = timezone('Europe/Madrid')
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Añadir el directorio raíz al path para importar módulos
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from app.api.google_fit_auth import GoogleFitAuth
from app.api.google_fit_data import GoogleFitData
from app.services.data_analysis import DataAnalyzer
from app.services.recommendations import HealthRecommender

# Configuración de la página
st.set_page_config(
    page_title="Health & Fitness Analytics",
    page_icon="🏃",
    layout="wide"
)

# Inicialización de servicios
@st.cache_resource
def get_services():

    try:
        auth = GoogleFitAuth()
        logger.info("Servicio de autenticación creado")
        
        fit_service = auth.get_fit_service()
        if not fit_service:
            logger.warning("No se pudo crear el servicio de Google Fit")
            return None, None, None, auth
        
        fit_data = GoogleFitData(fit_service)
        analyzer = DataAnalyzer()
        logger.info(f"DataAnalyzer creado con atributos: {dir(analyzer)}")
        logger.info(f"¿Tiene valid_sleep_types? {hasattr(analyzer, 'valid_sleep_types')}")
        recommender = HealthRecommender()
        logger.info("Todos los servicios inicializados correctamente")
        return fit_data, analyzer, recommender, auth
    except Exception as e:
        logger.error(f"Error al inicializar servicios: {str(e)}")
        st.error(f"Error al inicializar la aplicación: {str(e)}")
        return None, None, None, None


# Función para obtener datos
@st.cache_data(ttl=3600)
def get_data(_fit_data, days=7):
    end_time = datetime.now(tz)
    start_time = end_time - timedelta(days=days)
    
    steps_df = _fit_data.get_steps_data(start_time, end_time)
    hr_df = _fit_data.get_heart_rate_data(start_time, end_time)
    sleep_df = _fit_data.get_sleep_data(start_time, end_time)
    activity_df = _fit_data.get_activity_data(start_time, end_time)
    
    return steps_df, hr_df, sleep_df, activity_df

def show_sleep_dashboard(sleep_df, sleep_analysis):
    """Muestra un resumen visual completo del sueño."""
    if not sleep_analysis or sleep_analysis.get('total_hours', 0) == 0:
        st.warning("⚠️ No hay suficientes datos de sueño para mostrar.")
        return

    avg_hours = sleep_analysis.get('avg_hours', 0)
    sleep_quality_percent = sleep_analysis.get('sleep_quality_percent', 0)
    sleep_quality_label = sleep_analysis.get('sleep_quality_label', 'unknown')

    # Tres columnas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🛌 Horas promedio", f"{avg_hours:.1f} h")

    with col2:
        quality_map = {
            'excellent': '🟢 Excelente',
            'good': '🟢 Bueno',
            'fair': '🟠 Aceptable',
            'poor': '🔴 Pobre',
            'very poor': '🔴 Muy pobre',
            'unknown': '⚪️ Desconocido'
        }
        quality_text = quality_map.get(sleep_quality_label, '⚪️ Desconocido')
        st.metric("😴 Calidad", quality_text)

    with col3:
        import plotly.graph_objects as go
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=sleep_quality_percent,
            title={'text': "Sueño Reparador (%)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "blue"},
                'steps': [
                    {'range': [0, 40], 'color': "red"},
                    {'range': [40, 60], 'color': "orange"},
                    {'range': [60, 100], 'color': "green"},
                ],
            }
        ))
        st.plotly_chart(fig, use_container_width=True)


# Función para mostrar gráfico de pasos
def plot_steps(steps_df):
    if steps_df.empty:
        st.warning("No hay datos de pasos disponibles")
        return
        
    daily_steps = steps_df.groupby(steps_df['timestamp'].dt.date)['steps'].sum().reset_index()
    fig = px.line(daily_steps, x='timestamp', y='steps',
                  title='Pasos Diarios',
                  labels={'timestamp': 'Fecha', 'steps': 'Pasos'})
    st.plotly_chart(fig, use_container_width=True)

# Función para mostrar gráfico de ritmo cardíaco
def plot_heart_rate(hr_df):
    if hr_df.empty:
        st.warning("No hay datos de ritmo cardíaco disponibles")
        return
        
    fig = px.line(hr_df, x='timestamp', y='heart_rate',
                  title='Ritmo Cardíaco',
                  labels={'timestamp': 'Hora', 'heart_rate': 'Ritmo Cardíaco (bpm)'})
    st.plotly_chart(fig, use_container_width=True)

# Función para mostrar gráfico de sueño
def plot_sleep(sleep_df, analyzer):
    """Muestra un gráfico detallado del sueño con los diferentes tipos."""
    try:
        # --- Validación inicial ---
        if sleep_df.empty:
            st.warning("⏳ No hay datos de sueño disponibles")
            return
        
        # --- Verificar columnas obligatorias ---
        required_columns = ['start_time', 'end_time', 'sleep_type']
        missing_cols = [col for col in required_columns if col not in sleep_df.columns]
        
        if missing_cols:
            st.error(f"🚨 Datos incompletos. Faltan: {', '.join(missing_cols)}")
            return

        # --- Conversión de timezone ---
        # Si los datos vienen sin zona horaria (tz-naive)
        if sleep_df['start_time'].dt.tz is None:
            sleep_df['start_time'] = sleep_df['start_time'].dt.tz_localize('UTC').dt.tz_convert(tz)
            sleep_df['end_time'] = sleep_df['end_time'].dt.tz_localize('UTC').dt.tz_convert(tz)
        else:
            sleep_df['start_time'] = sleep_df['start_time'].dt.tz_convert(tz)
            sleep_df['end_time'] = sleep_df['end_time'].dt.tz_convert(tz)

        # --- Limpieza de datos ---
        # Convertir sleep_type a numérico
        sleep_df['sleep_type'] = pd.to_numeric(sleep_df['sleep_type'], errors='coerce')
        sleep_df = sleep_df.dropna(subset=['sleep_type'])
        sleep_df['sleep_type'] = sleep_df['sleep_type'].astype(int)

        # --- Filtrar tipos válidos ---
        valid_sleep_df = sleep_df[sleep_df['sleep_type'].isin(analyzer.valid_sleep_types)]
        
        if valid_sleep_df.empty:
            st.warning("""
                🛌 No se encontraron fases de sueño válidas. 
                **Tipos esperados:**  
                - Sueño ligero (4)  
                - Sueño profundo (5)  
                - Sueño REM (6)
            """)
            return

        # --- Preparar datos para visualización ---
        valid_sleep_df['sleep_phase'] = valid_sleep_df['sleep_type'].map({
            4: "Ligero",
            5: "Profundo",
            6: "REM"
        })
        
        # --- Crear gráfico ---
        color_discrete_map = {
            "Ligero": "#8da0cb",
            "Profundo": "#3d5a80",
            "REM": "#5390d9"
        }
        
        fig = px.timeline(
            valid_sleep_df,
            x_start="start_time",
            x_end="end_time",
            y="sleep_phase",
            color="sleep_phase",
            color_discrete_map=color_discrete_map,
            title="Fases del Sueño",
            labels={"sleep_phase": "Fase", "start_time": "Hora"}
        )
        
        fig.update_yaxes(categoryorder="array", categoryarray=["Ligero", "Profundo", "REM"])
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error grave al procesar el sueño: {str(e)}")
        logger.exception("Error detallado:")

# Función para mostrar recomendaciones
def show_recommendations(recommendations):
    if not recommendations:
        st.success("¡Todo parece estar en orden! No hay recomendaciones en este momento.")
        return
        
    for rec in recommendations:
        if rec['priority'] == 'high':
            st.error(rec['message'])
        else:
            st.warning(rec['message'])

# Función para mostrar análisis de sueño
def show_sleep_analysis(sleep_analysis, analyzer):
    if not sleep_analysis or sleep_analysis.get('total_hours', 0) == 0:
        st.warning("No se encontraron datos de sueño en el período seleccionado")
        return
        
    # Mostrar métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Horas totales de sueño", f"{sleep_analysis.get('total_hours', 0):.1f}")
    with col2:
        st.metric("Promedio por día", f"{sleep_analysis.get('avg_hours', 0):.1f}")
    with col3:
        st.metric("Calidad del sueño", f"{sleep_analysis.get('sleep_quality_percent', 0):.1f}%")
    
    # Mostrar gráfico de distribución del sueño
    st.subheader("Distribución del sueño")
    sleep_distribution = sleep_analysis.get('sleep_distribution', {})
    
    if sleep_distribution:
        # Crear DataFrame para el gráfico
        dist_df = pd.DataFrame({
            'Tipo': list(sleep_distribution.keys()),
            'Horas': list(sleep_distribution.values())
        })
        
        fig = px.bar(dist_df, x='Tipo', y='Horas',
                    title='Distribución de Tipos de Sueño',
                    color='Tipo',
                    labels={'Tipo': 'Tipo de Sueño', 'Horas': 'Horas'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos válidos para mostrar en el gráfico")

# Interfaz principal
def main():
    st.title("Health & Fitness Analytics")
    
    try:
        # --- Capturar parámetros de la URL ---
        query_params = st.query_params
        code = query_params.get("code", None)
        if code:
            st.success(f"Código recibido: {code[:5]}...")
        if code and not st.session_state.get("authenticated", False):
            st.success("Código de autorización recibido. Obteniendo credenciales...")
            try:
                auth = GoogleFitAuth()
                credentials = auth.get_credentials(code)
                st.success("✅ Credenciales obtenidas y guardadas correctamente.")
                
                # Marcar sesión como autenticada
                st.session_state["authenticated"] = True
                
                # Limpiar parámetros de la URL
                st.query_params.clear()
                
                # Recargar la app
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error obteniendo credenciales: {str(e)}")
                return
        
        # --- BLOQUE NORMAL de inicialización ---
        fit_data, analyzer, recommender, auth = get_services()
        
        if not auth:
            st.error("""
                No se pudo inicializar el servicio de autenticación. 
                Por favor, verifica que:
                1. Las variables de entorno GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET y GOOGLE_REDIRECT_URI estén configuradas correctamente
                2. El archivo .env esté en el directorio raíz del proyecto
                3. Los permisos de la aplicación en Google Cloud Console estén correctamente configurados
            """)
            return
        
        if not fit_data:
            try:
                auth_url = auth.get_authorization_url()
                st.info("""
                    Para acceder a tus datos de salud, necesitas autenticarte con Google Fit.
                    Esto permitirá a la aplicación acceder a tus datos de actividad física, ritmo cardíaco y sueño.
                """)
                st.markdown(f"[Haz clic aquí para autenticarte con Google Fit]({auth_url})")
                st.warning("""
                    Nota: La autenticación es necesaria para acceder a tus datos.
                    No almacenamos tus credenciales de Google, solo usamos tokens temporales para acceder a la API.
                """)
                return
            except Exception as e:
                logger.error(f"Error al obtener URL de autorización: {str(e)}")
                st.error(f"""
                    Error al obtener la URL de autorización: {str(e)}
                    
                    Por favor, verifica que:
                    1. Las credenciales de Google Fit estén correctamente configuradas
                    2. La aplicación tenga los permisos necesarios en Google Cloud Console
                    3. La URL de redirección esté correctamente configurada
                """)
                return
        
        # Sidebar para configuración
        with st.sidebar:
            st.header("Configuración")
            days = st.slider("Días a mostrar", 1, 30, 7)
            
            st.header("Objetivos")
            steps_goal = st.number_input("Objetivo de pasos diarios", 1000, 20000, 8000)
            sleep_goal = st.number_input("Objetivo de horas de sueño", 4, 12, 7)
            active_minutes_goal = st.number_input("Objetivo de minutos activos", 10, 120, 30)
            
            recommender.set_goals({
                'steps': steps_goal,
                'sleep': sleep_goal,
                'active_minutes': active_minutes_goal
            })
        
        # Obtener datos
        steps_df, hr_df, sleep_df, activity_df = get_data(fit_data, days)
        
        # Análisis de datos
        steps_analysis = analyzer.analyze_steps(steps_df)
        hr_analysis = analyzer.analyze_heart_rate(hr_df)
        sleep_analysis = analyzer.analyze_sleep(sleep_df)
        activity_analysis = analyzer.analyze_activity(activity_df)
        
        # Mostrar métricas principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Pasos Promedio", steps_analysis.get('daily_average', 0))
        with col2:
            st.metric("Ritmo Cardíaco Promedio", f"{hr_analysis.get('average_hr', 0):.1f} bpm")
        with col3:
            st.metric("Horas de Sueño Promedio", f"{sleep_analysis.get('avg_hours', 0):.1f}")
        with col4:
            st.metric("Minutos Activos", activity_analysis.get('active_minutes', 0))
        
        # Mostrar gráficos
        st.header("Gráficos")
        plot_steps(steps_df)
        plot_heart_rate(hr_df)
        plot_sleep(sleep_df, analyzer)
        
        # Mostrar recomendaciones
        st.header("Recomendaciones")
        analysis_results = {
            'steps': steps_analysis,
            'heart_rate': hr_analysis,
            'sleep': {
                'avg_hours': sleep_analysis.get('avg_hours', 0),
                'sleep_quality_percent': sleep_analysis.get('sleep_quality_percent', 0),
                'sleep_quality_label': sleep_analysis.get('sleep_quality_label', 'unknown')
            },
            'activity': activity_analysis
        }
        recommendations = recommender.generate_recommendations(analysis_results)
        show_recommendations(recommendations)
        
        # Mostrar análisis detallado del sueño
        st.header("Análisis de Sueño")
        show_sleep_analysis(sleep_analysis, analyzer)
        st.subheader("🔍 Dashboard de Sueño")
        show_sleep_dashboard(sleep_df, sleep_analysis)

        
    except Exception as e:
        logger.error(f"Error en la aplicación: {str(e)}")
        st.error(f"Ha ocurrido un error: {str(e)}")

if __name__ == "__main__":
    main()
