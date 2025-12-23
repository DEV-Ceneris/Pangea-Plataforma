import io
import csv
from ftplib import FTP
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from datetime import datetime
from decouple import config
from telemetria.models import DatosSensor, Estacion

class Command(BaseCommand):
    help = 'Importar FTP Relacional: Asigna datos a Estaciones por código de archivo'

    # MAPEO DE CAMPOS (Igual que antes)
    MAPEO_CAMPOS = {
        'record_id':          ['R', 'RECORD'],
        'bateria_voltaje':    ['BattV'],
        'ptemp_c':            ['PTemp'],
        'oxigeno_disuelto':   ['COxigeno_dis(mg/L)', 'COxigeno_dis'],
        'oxigeno_max':        ['COxigeno_dis_max'],
        'oxigeno_tmax':       ['COxigeno_dis_Tmax'],
        'porcentaje_oxigeno': ['Porcent_Oxigeno'],
        'presion_oxigeno':    ['Presionp_oxigeno'],
        'temperatura_agua':   ['Temperatura'],
        'conductividad':      ['Conductividad'],
        'salinidad':          ['Salinidad(%)'],
        'salinidad_max':      ['Salinidad_max'],
        'salinidad_tmax':     ['Salinidad_Tmax'],
        'solidos_disueltos':  ['TSD'],
        'densidad':           ['Densidad'],
        'ph':                 ['pH(pH)'],
        'ph_max':             ['pH_max'],
        'ph_tmax':            ['pH_Tmax'],
        'orp':                ['ORP']
    }

    CAMPOS_FECHA = ['oxigeno_tmax', 'salinidad_tmax', 'ph_tmax']

    def handle(self, *args, **kwargs):
        HOST = config('FTP_HOST')
        USER = config('FTP_USER')
        PASS = config('FTP_PASS')
        REMOTE_DIR = config('FTP_REMOTE_DIR', default='/')

        print(f"📡 Conectando a {HOST}...")
        try:
            ftp = FTP(HOST)
            ftp.login(user=USER, passwd=PASS)
            if REMOTE_DIR != '/': ftp.cwd(REMOTE_DIR)
            
            # Filtramos solo archivos de datos (H_)
            archivos = sorted([f for f in ftp.nlst() if f.startswith('H_') and f.endswith('.dat')])
            print(f"📂 Encontrados {len(archivos)} archivos de sensores.")

            for archivo in archivos:
                self.procesar_archivo(ftp, archivo)
            
            ftp.quit()
            print("✅ --- Proceso Finalizado ---")

        except Exception as e:
            print(f"❌ Error Fatal: {e}")

    def to_float(self, valor):
        if not valor: return None
        try:
            return float(str(valor).strip())
        except:
            return None

    def to_date(self, valor):
        if not valor: return None
        try:
            limpio = str(valor).replace('"', '').strip()
            if limpio in ['nan', 'NAN', '0', '']: return None
            fecha = datetime.strptime(limpio, "%Y-%m-%d %H:%M:%S")
            return make_aware(fecha)
        except:
            return None

    def obtener_codigo_estacion(self, filename):
        """
        Extrae el código del nombre del archivo.
        Ejemplo: 'H_..._FAO_21738.dat' -> Devuelve '21738'
        """
        try:
            # Quitamos la extensión .dat
            nombre_sin_ext = filename.replace('.dat', '')
            # Separamos por guion bajo y tomamos el último elemento
            partes = nombre_sin_ext.split('_')
            codigo = partes[-1]
            return codigo
        except:
            return None

    def procesar_archivo(self, ftp, filename):
        # 1. IDENTIFICAR LA ESTACIÓN
        codigo = self.obtener_codigo_estacion(filename)
        
        try:
            estacion = Estacion.objects.get(codigo_identificador=codigo)
        except Estacion.DoesNotExist:
            print(f"⚠️ Saltando {filename}: No existe la estación con código '{codigo}' en la BD.")
            return

        print(f"\nProcessing: {filename} -> Estación: {estacion.nombre}")
        
        memoria = io.BytesIO()
        try:
            ftp.retrbinary("RETR " + filename, memoria.write)
            memoria.seek(0)
            
            contenido = memoria.getvalue().decode('latin-1')
            lineas = contenido.splitlines()
            if not lineas: return

            # 2. ANALIZAR ENCABEZADO
            reader = csv.reader([lineas[0]])
            encabezado = next(reader)
            
            # 3. MAPEO DINÁMICO
            indices = {}
            try:
                idx_fecha = next(i for i, col in enumerate(encabezado) if 'Fecha' in col or 'TIMESTAMP' in col)
                indices['main_fecha'] = idx_fecha
            except StopIteration:
                indices['main_fecha'] = 0

            for campo_django, posibles_nombres in self.MAPEO_CAMPOS.items():
                indices[campo_django] = None
                for i, col_csv in enumerate(encabezado):
                    for nombre in posibles_nombres:
                        if nombre in col_csv:
                            indices[campo_django] = i
                            break
                    if indices[campo_django] is not None: break
            
            registros = []
            
            # 4. PROCESAR DATOS
            for i, linea in enumerate(lineas):
                linea = linea.strip()
                if not linea or not linea.startswith('"20'): continue

                try:
                    partes = next(csv.reader([linea]))
                    
                    # Fecha Principal
                    fecha_obj = self.to_date(partes[indices['main_fecha']])
                    if not fecha_obj: continue

                    def get(campo):
                        idx = indices.get(campo)
                        if idx is not None and idx < len(partes):
                            val = partes[idx]
                            if campo in self.CAMPOS_FECHA: return self.to_date(val)
                            return self.to_float(val)
                        return None

                    dato = DatosSensor(
                        estacion=estacion,  # <--- VINCULACIÓN IMPORTANTE
                        timestamp=fecha_obj,
                        record_id=int(get('record_id') or 0),
                        
                        bateria_voltaje=get('bateria_voltaje'),
                        ptemp_c=get('ptemp_c'),
                        oxigeno_disuelto=get('oxigeno_disuelto'),
                        oxigeno_max=get('oxigeno_max'),
                        oxigeno_tmax=get('oxigeno_tmax'),
                        porcentaje_oxigeno=get('porcentaje_oxigeno'),
                        presion_oxigeno=get('presion_oxigeno'),
                        temperatura_agua=get('temperatura_agua'),
                        conductividad=get('conductividad'),
                        salinidad=get('salinidad'),
                        salinidad_max=get('salinidad_max'),
                        salinidad_tmax=get('salinidad_tmax'),
                        solidos_disueltos=get('solidos_disueltos'),
                        densidad=get('densidad'),
                        ph=get('ph'),
                        ph_max=get('ph_max'),
                        ph_tmax=get('ph_tmax'),
                        orp=get('orp')
                    )
                    registros.append(dato)

                except Exception:
                    continue

            # 5. GUARDAR
            if registros:
                DatosSensor.objects.bulk_create(
                    registros, 
                    update_conflicts=True,
                    unique_fields=['estacion', 'timestamp', 'record_id'],
                    update_fields=['bateria_voltaje', 'oxigeno_disuelto', 'temperatura_agua', 'ph', 'conductividad']
                )
                print(f"   [✔] {len(registros)} registros guardados para {estacion.nombre}")
            else:
                print("   [!] Sin registros válidos.")

        except Exception as e:
            print(f"   [X] Error procesando: {e}")