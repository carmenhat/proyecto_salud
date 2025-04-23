from typing import Dict, List
from datetime import datetime, timedelta

class HealthRecommender:
    def __init__(self):
        self.recommendations = []
        self.goals = {
            'steps': 8000,
            'sleep': 7,
            'active_minutes': 30
        }

    def generate_recommendations(self, analysis_results: Dict) -> List[Dict]:
        """Genera recomendaciones basadas en el análisis de datos."""
        self.recommendations = []
        
        # Analizar pasos
        self._analyze_steps(analysis_results.get('steps', {}))
        
        # Analizar sueño
        self._analyze_sleep(analysis_results.get('sleep', {}))
        
        # Analizar actividad
        self._analyze_activity(analysis_results.get('activity', {}))
        
        # Analizar ritmo cardíaco
        self._analyze_heart_rate(analysis_results.get('heart_rate', {}))
        
        return self.recommendations

    def _analyze_steps(self, steps_data: Dict) -> None:
        """Analiza los datos de pasos y genera recomendaciones."""
        if not steps_data:
            return
            
        daily_avg = steps_data.get('daily_average', 0)
        goal = self.goals['steps']
        
        if daily_avg < goal * 0.5:
            self.recommendations.append({
                'type': 'steps',
                'priority': 'high',
                'message': f'Tu promedio de pasos diarios ({daily_avg}) está muy por debajo del objetivo recomendado ({goal}). Intenta incorporar más caminatas en tu rutina diaria.'
            })
        elif daily_avg < goal:
            self.recommendations.append({
                'type': 'steps',
                'priority': 'medium',
                'message': f'Estás cerca de alcanzar tu objetivo de {goal} pasos diarios. ¡Sigue así!'
            })

    def _analyze_sleep(self, sleep_data: Dict) -> None:
        """Analiza los datos de sueño y genera recomendaciones."""
        if not sleep_data:
            return
            
        avg_sleep = sleep_data.get('average_sleep', 0)
        quality = sleep_data.get('sleep_quality', 'unknown')
        goal = self.goals['sleep']
        
        if avg_sleep < goal * 0.8:
            self.recommendations.append({
                'type': 'sleep',
                'priority': 'high',
                'message': f'Tu promedio de sueño ({avg_sleep:.1f}h) está por debajo de lo recomendado ({goal}h). Intenta establecer una rutina de sueño más consistente.'
            })
        
        if quality == 'poor':
            self.recommendations.append({
                'type': 'sleep',
                'priority': 'medium',
                'message': 'La calidad de tu sueño podría mejorar. Considera reducir el uso de dispositivos antes de dormir y mantener un ambiente oscuro y tranquilo.'
            })

    def _analyze_activity(self, activity_data: Dict) -> None:
        """Analiza los datos de actividad y genera recomendaciones."""
        if not activity_data:
            return
            
        active_minutes = activity_data.get('active_minutes', 0)
        goal = self.goals['active_minutes']
        
        if active_minutes < goal:
            self.recommendations.append({
                'type': 'activity',
                'priority': 'medium',
                'message': f'Intenta aumentar tu actividad física diaria. El objetivo es {goal} minutos de actividad moderada.'
            })
        
        main_activities = activity_data.get('main_activities', [])
        if 'Inactivo' in main_activities:
            self.recommendations.append({
                'type': 'activity',
                'priority': 'high',
                'message': 'Parece que pasas mucho tiempo inactivo. Considera hacer pausas activas cada hora.'
            })

    def _analyze_heart_rate(self, hr_data: Dict) -> None:
        """Analiza los datos de ritmo cardíaco y genera recomendaciones."""
        if not hr_data:
            return
            
        resting_hr = hr_data.get('resting_hr', 0)
        if resting_hr > 80:
            self.recommendations.append({
                'type': 'heart_rate',
                'priority': 'high',
                'message': 'Tu ritmo cardíaco en reposo parece elevado. Considera consultar con un profesional de la salud.'
            })
        
        max_hr = hr_data.get('max_hr', 0)
        if max_hr > 180:
            self.recommendations.append({
                'type': 'heart_rate',
                'priority': 'medium',
                'message': 'Has alcanzado ritmos cardíacos muy altos durante el ejercicio. Asegúrate de mantener una intensidad adecuada a tu condición física.'
            })

    def set_goals(self, goals: Dict) -> None:
        """Actualiza los objetivos del usuario."""
        self.goals.update(goals) 