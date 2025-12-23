from ftplib import FTP
from decouple import config

# Cargar credenciales
HOST = config('FTP_HOST')
USER = config('FTP_USER')
PASS = config('FTP_PASS')

print(f"Conectando a {HOST}...")

try:
    ftp = FTP(HOST)
    ftp.login(user=USER, passwd=PASS)
    print("✅ Login exitoso.")
    
    # 1. Ver dónde estamos parados al inicio
    print(f"📂 Carpeta inicial (Raíz FTP): {ftp.pwd()}")
    
    # 2. Listar qué carpetas hay aquí
    print("📜 Contenido de la carpeta actual:")
    files = ftp.nlst()
    print(files)
    
    # 3. Intentar entrar a la ruta específica
    ruta_deseada = "/Datos_FAO/Gabinete_21738/PRUEBA"
    print(f"\nIntentando entrar a: {ruta_deseada} ...")
    
    try:
        ftp.cwd(ruta_deseada)
        print("✅ ¡ÉXITO! Esa es la ruta correcta.")
        print("Archivos encontrados:")
        print(ftp.nlst())
    except Exception as e:
        print(f"❌ Falló esa ruta. El servidor dice: {e}")
        
        # Intento alternativo (Quizás el FTP ya inicia dentro de Datos_FAO)
        ruta_alt = "/Gabinete_21738/PRUEBA"
        print(f"\nIntentando ruta alternativa: {ruta_alt} ...")
        try:
            ftp.cwd(ruta_alt)
            print("✅ ¡ÉXITO! La ruta correcta es la alternativa.")
            print("Archivos encontrados:")
            print(ftp.nlst())
        except Exception as e:
            print(f"❌ También falló. Tienes que revisar la configuración del servidor FTP.")

    ftp.quit()

except Exception as e:
    print(f"Error fatal: {e}")