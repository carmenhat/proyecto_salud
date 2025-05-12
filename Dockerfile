# Usar una imagen base de Python
FROM python:3.9-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de requisitos
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Crear directorio para tokens
RUN mkdir -p tokens

# Exponer el puerto que usa Streamlit
EXPOSE 8504

# Comando para ejecutar la aplicación
CMD ["streamlit", "run", "app/ui/main.py", "--server.port=8504", "--server.address=0.0.0.0"]