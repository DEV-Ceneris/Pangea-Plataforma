from django.db import models
from django.contrib.auth.models import User

# ==========================================
# 1. PERFIL DE USUARIO (Roles y Datos Extra)
# ==========================================
class PerfilUsuario(models.Model):
    ROLES = [
        ('admin', 'Administrador Global'),
        ('supervisor', 'Supervisor de Proyecto'),
        ('operador', 'Operador de Campo'),
        ('cliente', 'Cliente (Solo lectura)'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES, default='operador')
    telefono = models.CharField(max_length=20, blank=True, help_text="Para alertas SMS/WhatsApp")

    def __str__(self):
        return f"{self.user.username} - {self.get_rol_display()}"


# ==========================================
# 2. PROYECTO (Agrupador de Estaciones)
# ==========================================
class Proyecto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateField()
    activo = models.BooleanField(default=True)
    
    # Relación: Un proyecto tiene varios usuarios asignados
    usuarios_asignados = models.ManyToManyField(User, related_name='proyectos', blank=True)

    def __str__(self):
        return self.nombre


# ==========================================
# 3. ESTACIÓN (Datalogger Físico)
# ==========================================
class Estacion(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='estaciones')
    nombre = models.CharField(max_length=100, help_text="Ej: Estación Río Norte")
    
    # CLAVE: Este código debe ser IGUAL al del nombre del archivo .dat (Ej: 21738)
    codigo_identificador = models.CharField(max_length=50, unique=True, help_text="ID único del Datalogger (ej: 21738)")
    
    # Geolocalización
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Configuración de Alertas
    limite_oxigeno_min = models.FloatField(default=4.0, help_text="Alerta si baja de este valor")
    limite_bateria_min = models.FloatField(default=11.5, help_text="Alerta si baja de este valor")

    class Meta:
        verbose_name = "Estación"
        verbose_name_plural = "Estaciones"

    def save(self, *args, **kwargs):
        # 1. Guardamos la información en la base de datos primero
        super().save(*args, **kwargs)

        # 2. Definimos la ruta de la carpeta
        # Usamos el codigo_identificador para el nombre de la carpeta (Ej: 21738)
        nombre_carpeta = str(self.codigo_identificador).strip()
        ruta_carpeta = os.path.join(settings.RUTA_DATOS_TELEMETRIA, nombre_carpeta)

        # 3. Verificamos si existe, si no, la creamos
        if not os.path.exists(ruta_carpeta):
            try:
                # os.makedirs crea la carpeta y subcarpetas si faltan
                # mode=0o755 da permisos de lectura/ejecución a otros usuarios (importante para FTP)
                os.makedirs(ruta_carpeta, mode=0o755)
                print(f"✅ Carpeta creada exitosamente: {ruta_carpeta}")
            except OSError as e:
                print(f"❌ Error al crear carpeta para estación {self.codigo_identificador}: {e}")
        else:
            print(f"ℹ️ La carpeta ya existía: {ruta_carpeta}")

    def __str__(self):
        return f"{self.nombre} ({self.codigo_identificador})"


# ==========================================
# 4. DATOS DE SENSORES (Lecturas)
# ==========================================
class DatosSensor(models.Model):
    # Relación con la Estación
    estacion = models.ForeignKey(Estacion, on_delete=models.CASCADE, related_name='mediciones')
    
    # Identificadores de Tiempo y Registro
    timestamp = models.DateTimeField(verbose_name="Fecha y Hora", db_index=True)
    record_id = models.IntegerField(verbose_name="Número de Registro")
    
    # --- Energía ---
    bateria_voltaje = models.FloatField(null=True, blank=True, verbose_name="Batería (V)")
    ptemp_c = models.FloatField(null=True, blank=True, verbose_name="Temp. Interna (°C)")
    
    # --- Oxígeno ---
    oxigeno_disuelto = models.FloatField(null=True, blank=True, verbose_name="Oxígeno (mg/L)")
    oxigeno_max = models.FloatField(null=True, blank=True, verbose_name="Oxígeno Máx")
    oxigeno_tmax = models.DateTimeField(null=True, blank=True, verbose_name="Hora Oxígeno Máx")
    porcentaje_oxigeno = models.FloatField(null=True, blank=True, verbose_name="% Oxígeno")
    presion_oxigeno = models.FloatField(null=True, blank=True, verbose_name="Presión O2")
    
    # --- Calidad de Agua ---
    temperatura_agua = models.FloatField(null=True, blank=True, verbose_name="Temp. Agua (°C)")
    
    conductividad = models.FloatField(null=True, blank=True, verbose_name="Conductividad")
    
    salinidad = models.FloatField(null=True, blank=True, verbose_name="Salinidad (%)")
    salinidad_max = models.FloatField(null=True, blank=True, verbose_name="Salinidad Máx")
    salinidad_tmax = models.DateTimeField(null=True, blank=True, verbose_name="Hora Salinidad Máx")
    
    solidos_disueltos = models.FloatField(null=True, blank=True, verbose_name="TDS")
    densidad = models.FloatField(null=True, blank=True, verbose_name="Densidad")
    
    ph = models.FloatField(null=True, blank=True, verbose_name="pH")
    ph_max = models.FloatField(null=True, blank=True, verbose_name="pH Máx")
    ph_tmax = models.DateTimeField(null=True, blank=True, verbose_name="Hora pH Máx")
    
    orp = models.FloatField(null=True, blank=True, verbose_name="ORP (mV)")

    class Meta:
        # Evita duplicados por estación
        unique_together = ('estacion', 'timestamp', 'record_id')
        ordering = ['-timestamp']
        verbose_name = "Lectura de Sensor"
        verbose_name_plural = "Lecturas de Sensores"

    def __str__(self):
        return f"{self.estacion.codigo_identificador} - {self.timestamp}"


# ==========================================
# 5. NOTIFICACIONES (Alertas del Sistema)
# ==========================================
class Notificacion(models.Model):
    TIPOS = [
        ('info', 'Información'),
        ('warning', 'Advertencia'),
        ('danger', 'Peligro Crítico')
    ]
    estacion = models.ForeignKey(Estacion, on_delete=models.CASCADE, related_name='notificaciones')
    fecha = models.DateTimeField(auto_now_add=True)
    mensaje = models.CharField(max_length=255)
    leido = models.BooleanField(default=False)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='info')

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"[{self.tipo.upper()}] {self.estacion.nombre}: {self.mensaje}"