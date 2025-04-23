import sys
from pathlib import Path

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

# Importar directamente desde el archivo
from app.services.data_analysis import DataAnalyzer

def main():
    try:
        analyzer = DataAnalyzer()
        print("Atributos del analizador:")
        print(f"sleep_types: {hasattr(analyzer, 'sleep_types')}")
        if hasattr(analyzer, 'sleep_types'):
            print(f"Contenido de sleep_types: {analyzer.sleep_types}")
        print(f"valid_sleep_types: {hasattr(analyzer, 'valid_sleep_types')}")
        if hasattr(analyzer, 'valid_sleep_types'):
            print(f"Contenido de valid_sleep_types: {analyzer.valid_sleep_types}")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 