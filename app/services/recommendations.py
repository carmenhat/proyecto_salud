from typing import Dict, List, Optional

class HealthRecommender:
    def __init__(self):
        self.recommendations: List[Dict[str, str]] = []
        self.goals = {
            'steps': 8000,
            'sleep': 7,          # horas
            'active_minutes': 30 # minutos
        }

    def generate_recommendations(self, analysis_results: Dict) -> List[Dict]:
        """Genera recomendaciones basadas en los datos de análisis del usuario."""
        self.recommendations.clear()
        
        self._analyze_steps(analysis_results.get('steps'))
        self._analyze_sleep(analysis_results.get('sleep'))
        self._analyze_activity(analysis_results.get('activity'))
        self._analyze_heart_rate(analysis_results.get('heart_rate'))
        
        if not self.recommendations:
            self.recommendations.append({
                'type': 'general',
                'priority': 'low',
                'message': '¡Todo parece en orden! Sigue manteniendo tus hábitos saludables.'
            })
        
        return self.recommendations

    def set_goals(self, goals: Dict[str, float]) -> None:
        """Permite actualizar los objetivos personalizados del usuario."""
        self.goals.update(goals)

    def _safe_get(self, data: Optional[Dict], key: str, default=0) -> float:
        """Extrae datos de forma segura evitando errores."""
        if data and key in data:
            return data[key]
        return default

    def _analyze_steps(self, steps_data: Optional[Dict]) -> None:
        daily_avg = self._safe_get(steps_data, 'daily_average')
        goal = self.goals['steps']

        if daily_avg == 0:
            self.recommendations.append({
                'type': 'steps',
                'priority': 'high',
                'message': 'No hay registros recientes de pasos. ¿Estás sincronizando tu dispositivo?'
            })
            return

        completion_rate = daily_avg / goal
        
        if completion_rate < 0.5:
            msg = (f'Tu promedio de pasos diarios ({daily_avg:.0f}) es muy bajo respecto al objetivo ({goal}). '
                   f'Intenta dar paseos cortos después de las comidas o usar las escaleras más seguido.')
            priority = 'high'
        elif completion_rate < 0.9:
            msg = (f'Estás cerca de alcanzar tu meta diaria de {goal} pasos. ¡Un pequeño esfuerzo extra y lo lograrás!')
            priority = 'medium'
        else:
            msg = '¡Excelente! Estás cumpliendo tu objetivo diario de pasos. Mantén la constancia.'
            priority = 'low'

        self.recommendations.append({
            'type': 'steps',
            'priority': priority,
            'message': msg
        })

    def _analyze_sleep(self, sleep_data: Optional[Dict]) -> None:
        avg_sleep = self._safe_get(sleep_data, 'avg_hours') 
        sleep_quality = sleep_data.get('sleep_quality_label', 'unknown') if sleep_data else 'unknown'
        goal = self.goals['sleep']

        if avg_sleep == 0:
            self.recommendations.append({
                'type': 'sleep',
                'priority': 'high',
                'message': 'No se detectaron registros de sueño. Revisa si tu dispositivo está monitoreando correctamente.'
            })
            return

        if avg_sleep < goal * 0.8:
            self.recommendations.append({
                'type': 'sleep',
                'priority': 'high',
                'message': f'Tu promedio de sueño es de {avg_sleep:.1f}h, inferior a las {goal}h recomendadas. Intenta establecer horarios regulares de sueño.'
            })
        elif goal * 0.8 <= avg_sleep < goal:
            self.recommendations.append({
                'type': 'sleep',
                'priority': 'medium',
                'message': f'Estás cerca de tu meta de sueño ({goal}h). Un pequeño ajuste en tus horarios podría ser suficiente.'
            })

        if sleep_quality == 'poor':
            self.recommendations.append({
                'type': 'sleep',
                'priority': 'medium',
                'message': 'Tu calidad de sueño es baja. Prueba limitar pantallas antes de dormir y crear un ambiente relajante.'
            })

    def _analyze_activity(self, activity_data: Optional[Dict]) -> None:
        active_minutes = self._safe_get(activity_data, 'active_minutes')
        goal = self.goals['active_minutes']

        if active_minutes == 0:
            self.recommendations.append({
                'type': 'activity',
                'priority': 'medium',
                'message': 'No se han registrado minutos activos hoy. Intenta incluir pequeñas sesiones de actividad física.'
            })
            return

        if active_minutes < goal:
            self.recommendations.append({
                'type': 'activity',
                'priority': 'medium',
                'message': f'Actualmente acumulas {active_minutes} minutos activos diarios. Intenta alcanzar al menos {goal} minutos para mejorar tu salud cardiovascular.'
            })

        main_activities = activity_data.get('main_activities', []) if activity_data else []
        if 'Inactivo' in main_activities:
            self.recommendations.append({
                'type': 'activity',
                'priority': 'high',
                'message': 'Se detectan periodos largos de inactividad. Trata de moverte al menos 5 minutos cada hora.'
            })

    def _analyze_heart_rate(self, hr_data: Optional[Dict]) -> None:
        resting_hr = self._safe_get(hr_data, 'resting_hr')
        max_hr = self._safe_get(hr_data, 'max_hr')

        if resting_hr > 80:
            self.recommendations.append({
                'type': 'heart_rate',
                'priority': 'high',
                'message': 'Tu ritmo cardíaco en reposo es alto. Podría ser señal de estrés o fatiga. Si persiste, considera consultar a un médico.'
            })

        if max_hr > 180:
            self.recommendations.append({
                'type': 'heart_rate',
                'priority': 'medium',
                'message': 'Has alcanzado un ritmo cardíaco muy elevado durante la actividad. Controla la intensidad para evitar riesgos.'
            })
