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
        dist_df = pd.DataFrame({
            'Fase': list(sleep_distribution.keys()),
            'Horas': list(sleep_distribution.values())
        })

        fig = px.bar(
            dist_df,
            x='Fase',
            y='Horas',
            color='Fase',
            text='Horas',
            color_discrete_map={
                'Ligero': '#8da0cb',
                'Profundo': '#3d5a80',
                'REM': '#5390d9'
            },
            title="Distribución de Sueño por Fase"
        )

        fig.update_traces(texttemplate='%{text:.1f}h', textposition='outside')
        fig.update_layout(
            yaxis_title='Horas',
            xaxis_title='Fase del sueño',
            uniformtext_minsize=8,
            uniformtext_mode='hide',
            bargap=0.4
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ No hay datos válidos para mostrar en el gráfico de fases de sueño.")

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
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Pasos Promedio", steps_analysis.get('daily_average', 0))
        with col2:
            st.metric("Ritmo Cardíaco Promedio", f"{hr_analysis.get('average_hr', 0):.1f} bpm")
        with col3:
            st.metric("Horas de Sueño Promedio", f"{sleep_analysis.get('avg_hours', 0):.1f}")
        
        # Mostrar sección de actividad física
        st.subheader("🏃 Actividad Física")

        active_minutes = int(activity_analysis.get('active_minutes', 0))
        goal_per_day = recommender.goals.get('active_minutes', 30)
        total_goal = goal_per_day * days  # meta semanal

        # Conversión a horas y minutos
        h = active_minutes // 60
        m = active_minutes % 60
        tiempo_str = f"{h}h {m}min" if h > 0 else f"{m} min"

        # Cálculo de porcentaje
        progress = min((active_minutes / total_goal) * 100, 100)
        progress_color = "green" if progress >= 100 else "orange" if progress >= 60 else "red"

        # Mensaje motivacional
        if progress >= 100:
            msg = "🎉 ¡Has superado tu objetivo semanal de actividad! Excelente trabajo."
        elif progress >= 60:
             msg = "🟠 Vas por buen camino. ¡Un último esfuerzo y lo consigues!"
        else:
            msg = "🔴 Intenta moverte un poco más cada día para alcanzar tu meta."

        # Mostrar métrica principal
        st.metric("Total Minutos Activos", tiempo_str)

        # Mostrar barra de progreso con Plotly
        import plotly.graph_objects as go

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=active_minutes,
            number={'suffix': " min"},
            title={'text': "Progreso hacia la meta"},
            gauge={
                'axis': {'range': [0, total_goal]},
                'bar': {'color': progress_color},
                'steps': [
                    {'range': [0, total_goal * 0.6], 'color': '#f7c6c6'},
                    {'range': [total_goal * 0.6, total_goal * 0.9], 'color': '#ffe0b2'},
                    {'range': [total_goal * 0.9, total_goal], 'color': '#c8e6c9'},
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': total_goal
                }
                
            }
        ))
        st.plotly_chart(fig, use_container_width=True)

        # Mostrar mensaje motivacional
        st.info(msg)
        # ======================
        # GRÁFICO DE MINUTOS ACTIVOS DIARIOS
        # ======================
        st.subheader("📆 Minutos Activos por Día")

        if activity_df.empty:
            st.warning("No hay datos de actividad disponibles.")
        else:
            # Calcular duración por día
            activity_df['date'] = activity_df['start_time'].dt.date
            active_types = [3, 7, 8, 109]  # A pie, caminando, corriendo, ejercicio
            filtered = activity_df[activity_df['activity_type'].isin(active_types)]

            daily_minutes = filtered.groupby('date')['duration'].sum().reset_index()
            daily_minutes.rename(columns={'date': 'Fecha', 'duration': 'Minutos'}, inplace=True)

            # Etiquetar si cumple objetivo
            daily_minutes['Cumple Meta'] = daily_minutes['Minutos'].apply(
                lambda x: '✅ Meta alcanzada' if x >= goal_per_day else '❌ Por debajo'
            )

            # Crear gráfico de barras
            fig = px.bar(
                daily_minutes,
                x='Fecha',
                y='Minutos',
                color='Cumple Meta',
                color_discrete_map={
                    '✅ Meta alcanzada': '#66c2a5',  # verde
                    '❌ Por debajo': '#fc8d62'       # rojo-naranja
                },
                title="Actividad Diaria: ¿Alcanzas tu meta de minutos activos?",
                labels={'Minutos': 'Minutos Activos'}
            )

            # Línea de meta (etiquetas de texto)
            fig.add_hline(
                y=goal_per_day,
                line_dash="dot",
                line_color="black",
                annotation_text=f"Meta diaria: {goal_per_day} min",
                annotation_position="top left"
            )

            fig.update_layout(
                xaxis_title="Fecha",
                yaxis_title="Minutos activos",
                legend_title="Estado",
                bargap=0.25
            )

            st.plotly_chart(fig, use_container_width=True)


        # ======================
        # SECCIÓN DE PASOS
        # ======================
        st.subheader("👣 Pasos")

        total_steps = steps_analysis.get('total_steps', 0)
        daily_average = steps_analysis.get('daily_average', 0)
        steps_goal = recommender.goals.get('steps', 8000)

        # Calcular progreso sobre la media diaria
        progress = min((daily_average / steps_goal) * 100, 100)

        # Mensaje motivador
        if daily_average >= steps_goal:
            msg = "✅ ¡Estás cumpliendo tu meta diaria de pasos! Sigue así."
        elif daily_average >= steps_goal * 0.8:
            msg = "🟠 Estás muy cerca de la meta. Un pequeño esfuerzo diario más y lo logras."
        else:
            msg = "🔴 Intenta caminar un poco más cada día para alcanzar los beneficios mínimos recomendados."

        # Mostrar resumen de pasos
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Promedio Diario", f"{daily_average:,} pasos")
        with col2:
            st.metric("Pasos Totales", f"{total_steps:,}")

        # Gráfico de progreso tipo gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=daily_average,
            number={'suffix': " /día"},
            title={'text': "Progreso hacia la meta diaria"},
            gauge={
                'axis': {'range': [0, steps_goal]},
                'bar': {'color': "green" if progress >= 100 else "orange" if progress >= 70 else "red"},
                'steps': [
                    {'range': [0, steps_goal * 0.7], 'color': '#f7c6c6'},
                    {'range': [steps_goal * 0.7, steps_goal * 0.9], 'color': '#ffe0b2'},
                    {'range': [steps_goal * 0.9, steps_goal], 'color': '#c8e6c9'},
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': steps_goal
                }
            }
        ))
        st.plotly_chart(fig, use_container_width=True)

        # Mostrar mensaje motivador
        st.info(msg)
        # ======================
        # GRÁFICO DE PASOS DIARIOS (con fines de semana)
        # ======================

        st.subheader("📊 Evolución Diaria de Pasos")

        if steps_df.empty:
            st.warning("No hay datos de pasos disponibles.")
        else:
            # Agrupar por fecha y sumar pasos
            steps_daily = steps_df.groupby(steps_df['timestamp'].dt.date)['steps'].sum().reset_index()
            steps_daily.rename(columns={'timestamp': 'Fecha', 'steps': 'Pasos'}, inplace=True)
    
            # Añadir tipo de día (laboral o fin de semana)
            steps_daily['Día'] = pd.to_datetime(steps_daily['Fecha']).dt.dayofweek
            steps_daily['Tipo de Día'] = steps_daily['Día'].apply(lambda x: 'Fin de Semana' if x >= 5 else 'Entre Semana')

            # Crear gráfico
            fig = px.bar(
                steps_daily,
                x='Fecha',
                y='Pasos',
                color='Tipo de Día',
                color_discrete_map={
                    'Entre Semana': '#6baed6',   # azul claro
                    'Fin de Semana': '#fd8d3c'   # naranja
                },
                title="Pasos Diarios: Semana vs. Fin de Semana",
                labels={'Pasos': 'Total de pasos'}
            )

            # Línea de referencia de objetivo
            fig.add_hline(
                y=steps_goal,
                line_dash="dot",
                line_color="green",
                annotation_text=f"Meta: {steps_goal} pasos",
                annotation_position="top left"
            )

            fig.update_layout(
                xaxis_title="Fecha",
                yaxis_title="Pasos",
                legend_title="Tipo de Día",
                bargap=0.25
            )

            st.plotly_chart(fig, use_container_width=True)

        
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
