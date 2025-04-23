import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import sys
import logging

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
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    steps_df = _fit_data.get_steps_data(start_time, end_time)
    hr_df = _fit_data.get_heart_rate_data(start_time, end_time)
    sleep_df = _fit_data.get_sleep_data(start_time, end_time)
    activity_df = _fit_data.get_activity_data(start_time, end_time)
    
    return steps_df, hr_df, sleep_df, activity_df

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
    if sleep_df.empty:
        st.warning("No hay datos de sueño disponibles")
        return
    
    # Asegurarse de que sleep_type es numérico
    if not pd.api.types.is_numeric_dtype(sleep_df['sleep_type']):
        sleep_df['sleep_type'] = pd.to_numeric(sleep_df['sleep_type'], errors='coerce')
    
    # Filtrar solo los tipos de sueño válidos
    valid_sleep_df = sleep_df[sleep_df['sleep_type'].isin(analyzer.valid_sleep_types)]
    
    if valid_sleep_df.empty:
        st.warning("No hay datos válidos de sueño en el período seleccionado")
        return
    
    # Asegurarse de que tenemos start_time, end_time y duration
    if not all(col in valid_sleep_df.columns for col in ['start_time', 'end_time']):
        st.error("Los datos de sueño no contienen la información temporal necesaria")
        return
    
    # Crear una paleta de colores para los diferentes tipos de sueño
    color_map = {
        4: "#8da0cb",  # Sueño ligero - azul claro
        5: "#3d5a80",  # Sueño profundo - azul oscuro
        6: "#5390d9"   # Sueño REM - azul medio
    }
    
    # Convertir tipos numéricos a nombres legibles
    valid_sleep_df['sleep_type_name'] = valid_sleep_df['sleep_type'].map(analyzer.sleep_types)
    
    # Crear figura
    fig = go.Figure()
    
    # Agregar barras para cada tipo de sueño
    for sleep_type in valid_sleep_df['sleep_type'].unique():
        if sleep_type in analyzer.valid_sleep_types:
            type_df = valid_sleep_df[valid_sleep_df['sleep_type'] == sleep_type]
            type_name = analyzer.sleep_types.get(sleep_type, f"Tipo {sleep_type}")
            
            fig.add_trace(go.Bar(
                x=type_df['start_time'],
                y=type_df['duration'],
                name=type_name,
                marker_color=color_map.get(sleep_type, "#A9A9A9"),  # Color definido o gris por defecto
                hovertemplate="%{x}<br>Duración: %{y:.2f} horas<br>Tipo: " + type_name
            ))
    
    # Configurar diseño del gráfico
    fig.update_layout(
        title='Duración y Tipos de Sueño',
        xaxis_title='Fecha',
        yaxis_title='Horas de Sueño',
        barmode='stack',  # Apilar barras de diferentes tipos
        legend_title='Tipo de Sueño',
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)

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
        st.metric("Calidad del sueño", f"{sleep_analysis.get('sleep_quality', 0):.1f}%")
    
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
        # Verificar autenticación
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
            'sleep': sleep_analysis,
            'activity': activity_analysis
        }
        recommendations = recommender.generate_recommendations(analysis_results)
        show_recommendations(recommendations)
        
        # Mostrar análisis detallado del sueño
        st.header("Análisis de Sueño")
        show_sleep_analysis(sleep_analysis, analyzer)
        
    except Exception as e:
        logger.error(f"Error en la aplicación: {str(e)}")
        st.error(f"Ha ocurrido un error: {str(e)}")

if __name__ == "__main__":
    main()
