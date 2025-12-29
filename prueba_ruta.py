import os
from ftplib import FTP

# CONFIGURACIÓN (Extraída de tu código CRBasic)
FTP_HOST = "13.217.194.29"
FTP_USER = "pangea_ftp"  # Usuario que creamos en Linux
FTP_PASS = "pangea_telemetria"
DEST_FOLDER = "upload"   # Carpeta de destino dentro del servidor

def test_datalogger_upload():
    print(f"--- Iniciando prueba de simulación Datalogger CR300 ---")
    
    # 1. Crear contenido falso simulando una línea de 'Tabla2'
    # Fecha, Record, BattV, PTemp_C, COxigeno...
    csv_header = "TIMESTAMP,RECORD,BattV_avg,PTemp_C_avg,COxigeno_dis_avg,pH_avg\n"
    csv_data = "2025-12-26 12:00:00,1,12.5,24.3,7.8,8.1\n"
    filename = "H_simulado_FAO_21738.dat"

    with open(filename, "w") as f:
        f.write(csv_header)
        f.write(csv_data)

    try:
        print(f"Conectando a {FTP_HOST}...")
        ftp = FTP()
        # Tiempo de espera corto para detectar fallas de red rápidamente
        ftp.connect(FTP_HOST, 21, timeout=10) 
        
        print(f"Autenticando usuario: {FTP_USER}...")
        ftp.login(user=FTP_USER, passwd=FTP_PASS)
        
        # Forzar modo pasivo (requerido para dataloggers en redes celulares)
        ftp.set_pasv(True)
        print("✅ Modo Pasivo activado.")

        # Entrar a la carpeta de subida
        ftp.cwd(DEST_FOLDER)
        print(f"✅ Cambiado a directorio: {ftp.pwd()}")

        # Subir el archivo
        print(f"Enviando archivo {filename}...")
        with open(filename, "rb") as file_to_send:
            ftp.storbinary(f"STOR {filename}", file_to_send)
        
        print(f"✅ ¡ÉXITO! El archivo {filename} se subió correctamente.")
        
        # Listar para confirmar
        print("Contenido actual en el servidor:")
        print(ftp.nlst())

        ftp.quit()

    except Exception as e:
        print(f"❌ ERROR DE CONFIGURACIÓN: {e}")
        print("\nVerifica:")
        print("1. ¿Están abiertos los puertos 21 y 40000-50000 en el Firewall de Lightsail?")
        print("2. ¿El servicio vsftpd está corriendo? (sudo systemctl status vsftpd)")
        print("3. ¿El usuario tiene permisos en la carpeta? (sudo chown -R)")
    
    finally:
        # Limpiar archivo local de prueba
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    test_datalogger_upload()