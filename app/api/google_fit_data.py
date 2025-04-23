from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from googleapiclient.discovery import Resource
import logging

class GoogleFitData:
    def __init__(self, fit_service: Resource):
        self.service = fit_service

    def get_steps_data(self, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Obtiene datos de pasos para un rango de tiempo."""
        data_source = "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
        
        response = self.service.users().dataSources().datasets().get(
            userId='me',
            dataSourceId=data_source,
            datasetId=f"{int(start_time.timestamp() * 1000000000)}-{int(end_time.timestamp() * 1000000000)}"
        ).execute()

        steps_data = []
        for point in response.get('point', []):
            steps_data.append({
                'timestamp': datetime.fromtimestamp(int(point['startTimeNanos']) / 1000000000),
                'steps': int(point['value'][0]['intVal'])
            })

        return pd.DataFrame(steps_data)

    def get_heart_rate_data(self, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Obtiene datos de ritmo cardíaco para un rango de tiempo."""
        data_source = "derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm"
        
        response = self.service.users().dataSources().datasets().get(
            userId='me',
            dataSourceId=data_source,
            datasetId=f"{int(start_time.timestamp() * 1000000000)}-{int(end_time.timestamp() * 1000000000)}"
        ).execute()

        hr_data = []
        for point in response.get('point', []):
            hr_data.append({
                'timestamp': datetime.fromtimestamp(int(point['startTimeNanos']) / 1000000000),
                'heart_rate': float(point['value'][0]['fpVal'])
            })

        return pd.DataFrame(hr_data)

    def get_sleep_data(self, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Obtiene datos de sueño para un rango de tiempo."""
        data_source = "derived:com.google.sleep.segment:com.google.android.gms:merged"
        
        try:
            logging.info(f"Solicitando datos de sueño desde {start_time} hasta {end_time}")
            dataset_id = f"{int(start_time.timestamp() * 1000000000)}-{int(end_time.timestamp() * 1000000000)}"
            logging.info(f"Dataset ID: {dataset_id}")
            
            response = self.service.users().dataSources().datasets().get(
                userId='me',
                dataSourceId=data_source,
                datasetId=dataset_id
            ).execute()
            
            logging.info("Respuesta recibida de Google Fit API")
            logging.info(f"Puntos de datos encontrados: {len(response.get('point', []))}")
            
            sleep_data = []
            for point in response.get('point', []):
                try:
                    start = datetime.fromtimestamp(int(point['startTimeNanos']) / 1000000000)
                    end = datetime.fromtimestamp(int(point['endTimeNanos']) / 1000000000)
                    sleep_type = point['value'][0]['intVal']
                    duration = (end - start).total_seconds() / 3600
                    
                    logging.debug(f"Sleep segment: {start} to {end}, type: {sleep_type}, duration: {duration:.2f} hours")
                    
                    sleep_data.append({
                        'start_time': start,
                        'end_time': end,
                        'sleep_type': sleep_type,
                        'duration': duration
                    })
                except Exception as e:
                    logging.error(f"Error procesando punto de datos: {str(e)}")
                    logging.error(f"Punto de datos: {point}")
                    continue

            df = pd.DataFrame(sleep_data)
            if not df.empty:
                logging.info(f"Total sleep segments: {len(df)}")
                logging.info(f"Sleep types found: {df['sleep_type'].unique()}")
                logging.info(f"Total sleep duration: {df['duration'].sum():.2f} hours")
                logging.info(f"Rango de fechas: {df['start_time'].min()} a {df['start_time'].max()}")
            else:
                logging.warning("No se encontraron datos de sueño en el período especificado")
            return df
            
        except Exception as e:
            logging.error(f"Error obteniendo datos de sueño: {str(e)}")
            logging.error("Devolviendo DataFrame vacío")
            return pd.DataFrame()

    def get_activity_data(self, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Obtiene datos de actividad física para un rango de tiempo."""
        data_source = "derived:com.google.activity.segment:com.google.android.gms:merge_activity_segments"
        
        response = self.service.users().dataSources().datasets().get(
            userId='me',
            dataSourceId=data_source,
            datasetId=f"{int(start_time.timestamp() * 1000000000)}-{int(end_time.timestamp() * 1000000000)}"
        ).execute()

        activity_data = []
        for point in response.get('point', []):
            activity_data.append({
                'start_time': datetime.fromtimestamp(int(point['startTimeNanos']) / 1000000000),
                'end_time': datetime.fromtimestamp(int(point['endTimeNanos']) / 1000000000),
                'activity_type': point['value'][0]['intVal']
            })

        return pd.DataFrame(activity_data) 