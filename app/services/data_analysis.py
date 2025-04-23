import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import logging

class DataAnalyzer:
    def __init__(self):
        self.activity_types = {
            0: "Inactivo",
            1: "En vehículo",
            2: "Bicicleta",
            3: "A pie",
            4: "Tilting",
            7: "Caminando",
            8: "Corriendo",
            72: "Durmiendo",
            109: "Ejercicio",
            113: "En transporte"
        }

    def analyze_steps(self, steps_df: pd.DataFrame) -> Dict:
        """Analiza los datos de pasos y genera estadísticas."""
        if steps_df.empty:
            return {
                'total_steps': 0,
                'daily_average': 0,
                'max_steps': 0,
                'min_steps': 0,
                'trend': 'stable'
            }

        daily_steps = steps_df.groupby(steps_df['timestamp'].dt.date)['steps'].sum()
        
        return {
            'total_steps': int(daily_steps.sum()),
            'daily_average': int(daily_steps.mean()),
            'max_steps': int(daily_steps.max()),
            'min_steps': int(daily_steps.min()),
            'trend': self._calculate_trend(daily_steps)
        }

    def analyze_heart_rate(self, hr_df: pd.DataFrame) -> Dict:
        """Analiza los datos de ritmo cardíaco y genera estadísticas."""
        if hr_df.empty:
            return {
                'average_hr': 0,
                'max_hr': 0,
                'min_hr': 0,
                'resting_hr': 0
            }

        return {
            'average_hr': float(hr_df['heart_rate'].mean()),
            'max_hr': float(hr_df['heart_rate'].max()),
            'min_hr': float(hr_df['heart_rate'].min()),
            'resting_hr': self._calculate_resting_hr(hr_df)
        }

    def analyze_sleep(self, sleep_df: pd.DataFrame) -> Dict:
        """Analiza los datos de sueño y devuelve estadísticas."""
        if sleep_df.empty:
            logging.warning("No hay datos de sueño disponibles")
            return {
                'total_hours': 0.0,
                'avg_hours': 0.0,
                'sleep_quality': 0.0
        }
    
        try:
            # Ver qué columnas están disponibles
            logging.info(f"Columnas en sleep_df: {sleep_df.columns.tolist()}")
            logging.info(f"Tipos de sueño encontrados: {sleep_df['sleep_type'].unique()}")
        
            # Asegurarse de que las columnas necesarias existan
            required_columns = ['sleep_type', 'duration']
            missing_columns = [col for col in required_columns if col not in sleep_df.columns]
            if missing_columns:
                logging.error(f"Faltan columnas requeridas: {missing_columns}")
                return {
                    'total_hours': 0.0,
                    'avg_hours': 0.0,
                    'sleep_quality': 0.0
                }
        
            # Convertir sleep_type a numérico si no lo es
            if not pd.api.types.is_numeric_dtype(sleep_df['sleep_type']):
                sleep_df['sleep_type'] = pd.to_numeric(sleep_df['sleep_type'], errors='coerce')
        
            # IMPORTANTE: Eliminemos NaNs antes de filtrar
            sleep_df = sleep_df.dropna(subset=['sleep_type', 'duration'])
        
            # Mostrar valores antes de filtrar
            logging.info(f"Tipos de sueño antes de filtrar: {sleep_df['sleep_type'].value_counts().to_dict()}")
            logging.info(f"Total duración antes de filtrar: {sleep_df['duration'].sum():.2f} horas")
        
            # Filtrar solo los tipos de sueño relevantes (4=ligero, 5=profundo, 6=REM)
            valid_sleep_df = sleep_df[sleep_df['sleep_type'].isin([4, 5, 6])]
        
            logging.info(f"Filas después de filtrar por tipos válidos: {len(valid_sleep_df)}")
            logging.info(f"Tipos después de filtrar: {valid_sleep_df['sleep_type'].value_counts().to_dict()}")
        
            if valid_sleep_df.empty:
                logging.warning("No hay sesiones de sueño válidas después de filtrar")
                return {
                    'total_hours': 0.0,
                    'avg_hours': 0.0,
                    'sleep_quality': 0.0
                }
        
            # Calcular métricas
            total_hours = float(valid_sleep_df['duration'].sum())
        
            # Determinar cómo calcular días únicos
            if 'date' in valid_sleep_df.columns:
                unique_dates = valid_sleep_df['date'].nunique()
            elif 'start_time' in valid_sleep_df.columns:
                unique_dates = valid_sleep_df['start_time'].dt.date.nunique()
            else:
                unique_dates = 1
            
            logging.info(f"Días únicos encontrados: {unique_dates}")
        
            avg_hours = total_hours / unique_dates if unique_dates > 0 else 0.0
        
            # Calcular calidad del sueño
            deep_sleep = float(valid_sleep_df[valid_sleep_df['sleep_type'] == 5]['duration'].sum())
            rem_sleep = float(valid_sleep_df[valid_sleep_df['sleep_type'] == 6]['duration'].sum())
            sleep_quality = ((deep_sleep + rem_sleep) / total_hours * 100) if total_hours > 0 else 0.0
        
            logging.info(f"Total sleep hours: {total_hours:.2f}")
            logging.info(f"Average sleep hours: {avg_hours:.2f}")
            logging.info(f"Sleep quality: {sleep_quality:.2f}%")
        
            return {
                'total_hours': total_hours,
                'avg_hours': avg_hours,
                'sleep_quality': sleep_quality
            }
        
        except Exception as e:
            logging.error(f"Error al analizar datos de sueño: {str(e)}")
            logging.error(f"DataFrame info: {sleep_df.info()}")
            logging.exception("Detalle del error:")
            return {
                'total_hours': 0.0,
                'avg_hours': 0.0,
                'sleep_quality': 0.0
        }

    def analyze_activity(self, activity_df: pd.DataFrame) -> Dict:
        """Analiza los datos de actividad y genera estadísticas."""
        if activity_df.empty:
            return {
                'active_minutes': 0,
                'main_activities': [],
                'activity_distribution': {}
            }

        activity_df['duration'] = (activity_df['end_time'] - activity_df['start_time']).dt.total_seconds() / 60
        active_minutes = activity_df[activity_df['activity_type'].isin([3, 7, 8, 109])]['duration'].sum()
        
        activity_dist = activity_df.groupby('activity_type')['duration'].sum()
        main_activities = activity_dist.nlargest(3).index.map(lambda x: self.activity_types.get(x, 'Unknown')).tolist()
        
        return {
            'active_minutes': float(active_minutes),
            'main_activities': main_activities,
            'activity_distribution': activity_dist.to_dict()
        }

    def _calculate_trend(self, daily_values: pd.Series) -> str:
        """Calcula la tendencia de los valores diarios."""
        if len(daily_values) < 2:
            return 'stable'
        
        recent = daily_values.tail(7)
        if len(recent) < 2:
            return 'stable'
            
        slope = np.polyfit(range(len(recent)), recent, 1)[0]
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        return 'stable'

    def _calculate_resting_hr(self, hr_df: pd.DataFrame) -> float:
        """Calcula el ritmo cardíaco en reposo."""
        # Asumimos que el ritmo cardíaco más bajo durante la noche es el ritmo en reposo
        night_hr = hr_df[hr_df['timestamp'].dt.hour.between(0, 6)]['heart_rate']
        return float(night_hr.min()) if not night_hr.empty else 0

    def _calculate_sleep_efficiency(self, sleep_df: pd.DataFrame) -> float:
        """Calcula la eficiencia del sueño."""
        if sleep_df.empty:
            return 0
            
        total_time = (sleep_df['end_time'].max() - sleep_df['start_time'].min()).total_seconds() / 3600
        actual_sleep = sleep_df['duration'].sum()
        return float((actual_sleep / total_time) * 100) if total_time > 0 else 0

    def _assess_sleep_quality(self, sleep_df: pd.DataFrame) -> str:
        """Evalúa la calidad del sueño basada en la duración y eficiencia."""
        if sleep_df.empty:
            return 'unknown'
            
        avg_sleep = sleep_df['duration'].mean()
        efficiency = self._calculate_sleep_efficiency(sleep_df)
        
        if avg_sleep >= 7 and efficiency >= 85:
            return 'excellent'
        elif avg_sleep >= 6 and efficiency >= 75:
            return 'good'
        elif avg_sleep >= 5 and efficiency >= 65:
            return 'fair'
        return 'poor' 
