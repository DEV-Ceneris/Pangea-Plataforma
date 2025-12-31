import random
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import DatosSensor, Empresa, PerfilUsuario, DatosSensor, Proyecto, Estacion
from .forms import ProyectoForm, EstacionForm, RegistroEmpresaForm, RegistroPaso1Form, VerificacionForm, PasswordSetupForm
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import login

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
        else:
            # Aquí está la magia: añadimos un mensaje de error personalizado
            messages.error(request, 'Usuario o contraseña incorrectos. Por favor, inténtalo de nuevo.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'inicio/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html')

@login_required 
def api_datos(request):
    # Traemos todos los datos ordenados
    datos = DatosSensor.objects.all().order_by('timestamp')
    
    # Preparamos diccionarios vacíos para cada serie
    response_data = {
        'bateria_nivel': [], # Ojo: Tu CSV no tiene % batería, solo Voltaje. Usaremos Voltaje.
        'bateria_voltaje': [],
        'ptemp': [],
        'oxigeno_mg': [],
        'oxigeno_porc': [],
        'temperatura_agua': [],
        'conductividad': [],
        'salinidad': [],
        'solidos': [],
        'ph': [],
        'orp': []
    }

    for d in datos:
        ts = d.timestamp.timestamp() * 1000 # Fecha en milisegundos
        
        # Función auxiliar para agregar dato si no es nulo
        def add(key, value):
            if value is not None:
                response_data[key].append([ts, value])

        add('bateria_voltaje', d.bateria_voltaje)
        add('ptemp', d.ptemp_c)
        add('oxigeno_mg', d.oxigeno_disuelto)
        add('oxigeno_porc', d.porcentaje_oxigeno)
        add('temperatura_agua', d.temperatura_agua)
        add('conductividad', d.conductividad)
        add('salinidad', d.salinidad)
        add('solidos', d.solidos_disueltos)
        add('ph', d.ph)
        add('orp', d.orp)
        # Nota: Como no tienes "Nivel Batería %" en el CSV, usaremos Voltaje duplicado o vacío
        # Si tienes la fórmula para calcular % basado en voltaje, la pondríamos aquí.

    return JsonResponse(response_data)

# ==========================================
# 3. GESTIÓN DE ESTACIONES
# ==========================================

@login_required
def lista_proyectos(request):
    try:
        perfil = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        # Caso de emergencia: El usuario existe pero no tiene perfil
        return render(request, 'errores/sin_perfil.html', {
            'mensaje': 'Tu usuario no tiene un perfil configurado. Contacta a soporte.'
        })

    if not perfil.empresa:
        # Caso: Tiene perfil pero no se le asignó empresa
        return render(request, 'errores/sin_empresa.html', {
             'mensaje': 'No tienes una empresa asignada.'
        })

    # Si todo está bien, filtramos
    # Corregido: Filtramos por los proyectos asignados al usuario
    proyectos = request.user.proyectos.all()
    return render(request, 'proyectos/lista.html', {'proyectos': proyectos})

# 2. CREAR PROYECTO
@login_required
def crear_proyecto(request):
    """Formulario para crear un nuevo proyecto"""
    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            proyecto = form.save()
            # Auto-asignar al creador para que no pierda acceso
            proyecto.usuarios_asignados.add(request.user)
            return redirect('lista_proyectos')
    else:
        form = ProyectoForm()
    
    return render(request, 'proyectos/crear.html', {'form': form})

# 3. DETALLE PROYECTO (Ver sus estaciones)
def detalle_proyecto(request, pk):
    """Muestra las estaciones dentro de un proyecto específico"""
    proyecto = get_object_or_404(Proyecto, pk=pk)
    
    # SEGURIDAD: Verificar si el usuario tiene permiso para ver este proyecto
    if not request.user.is_superuser and request.user not in proyecto.usuarios_asignados.all():
        # Si no tiene permiso, mostramos error 403 o redirigimos
        return HttpResponseForbidden("No tienes permiso para ver este proyecto.")
        
    estaciones = proyecto.estaciones.all()
    
    return render(request, 'proyectos/detalle.html', {
        'proyecto': proyecto,
        'estaciones': estaciones
    })

# ==========================================
# 3. GESTIÓN DE ESTACIONES
# ==========================================

@login_required
def lista_estaciones(request):
    usuario = request.user
    
    if usuario.is_superuser:
        estaciones = Estacion.objects.all()
    else:
        # Filtramos estaciones que pertenezcan a los proyectos del usuario
        estaciones = Estacion.objects.filter(proyecto__in=usuario.proyectos.all())
    
    return render(request, 'estacion/lista_estacion.html', {'estaciones': estaciones})

@login_required
def crear_estacion(request):
    if request.method == 'POST':
        # Pasamos el usuario al form para filtrar el dropdown de proyectos
        form = EstacionForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_estaciones')
    else:
        form = EstacionForm(request.user)
    
    return render(request, 'estacion/crear_estacion.html', {'form': form})

# ==========================================
#  USUARIOS
# ==========================================

def registro_usuario(request):
    # Capturar el plan de la URL (GET)
    plan_get = request.GET.get('plan', 'gratuito')

    if request.method == 'POST':
        form = RegistroEmpresaForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Crear empresa CON EL PLAN
            nombre_empresa = form.cleaned_data.get('nombre_empresa')
            plan_final = form.cleaned_data.get('plan_seleccionado') or 'gratuito'
            
            empresa = Empresa.objects.create(
                nombre=nombre_empresa,
                plan=plan_final # <--- AQUÍ GUARDAMOS EL PLAN
            )
            
            perfil, created = PerfilUsuario.objects.get_or_create(user=user)
            perfil.empresa = empresa
            perfil.rol = 'admin_empresa'
            perfil.save()
            
            login(request, user)
            return redirect('dashboard')
    else:
        # Inicializar formulario con el plan que viene de la URL
        form = RegistroEmpresaForm(initial={'plan_seleccionado': plan_get})
    
    return render(request, 'inicio/registro.html', {'form': form, 'plan_elegido': plan_get})

def planes_precios(request):
    return render(request, 'inicio/planes.html')

# ==========================================
#  Registro Multietapa
# ==========================================

# PASO 1: Recolección de datos y Envío de Email
def registro_paso1(request):
    # Capturar plan si viene de la URL (ej: ?plan=pro)
    plan_seleccionado = request.GET.get('plan', 'gratuito')
    
    if request.method == 'POST':
        form = RegistroPaso1Form(request.POST)
        if form.is_valid():
            # 1. Generar Código de 6 dígitos
            codigo = str(random.randint(100000, 999999))
            
            # 2. Guardar datos en SESIÓN TEMPORAL (No en BD todavía)
            request.session['registro_temp'] = {
                'nombre_empresa': form.cleaned_data['nombre_empresa'],
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'email': form.cleaned_data['email'],
                'plan': plan_seleccionado,
                'codigo_verificacion': codigo,
                'verificado': False # Bandera de seguridad
            }

            # 3. Enviar Correo
            asunto = f"Tu código de verificación Pangea: {codigo}"
            mensaje = f"Hola {form.cleaned_data['first_name']},\n\nTu código de seguridad es: {codigo}\n\nIngresa este código para completar tu registro."
            
            try:
                send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [form.cleaned_data['email']])
                return redirect('registro_verificacion')
            except Exception as e:
                form.add_error(None, f"Error enviando correo: {e}")

    else:
        form = RegistroPaso1Form()

    return render(request, 'registro/registro_paso1.html', {'form': form, 'plan': plan_seleccionado})

# PASO 2: Validar Código
def registro_verificacion(request):
    datos = request.session.get('registro_temp')
    if not datos:
        return redirect('registro') # Si no hay datos, volver al inicio

    if request.method == 'POST':
        form = VerificacionForm(request.POST)
        if form.is_valid():
            codigo_ingresado = form.cleaned_data['codigo']
            
            # Comparar código
            if codigo_ingresado == datos.get('codigo_verificacion'):
                # ¡Éxito! Marcamos como verificado
                datos['verificado'] = True
                request.session['registro_temp'] = datos
                return redirect('registro_password')
            else:
                form.add_error('codigo', "Código incorrecto. Intenta nuevamente.")
    else:
        form = VerificacionForm()

    return render(request, 'registro/registro_verificacion.html', {'form': form, 'email': datos['email']})

# PASO 3: Crear Contraseña y Guardar en BD
def registro_password(request):
    datos = request.session.get('registro_temp')
    
    # Seguridad: Si no hay datos o no verificó el código, expulsar
    if not datos or not datos.get('verificado'):
        return redirect('registro')

    if request.method == 'POST':
        form = PasswordSetupForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            
            # --- AQUÍ OCURRE LA MAGIA DE GUARDADO EN BD ---
            
            # 1. Crear Usuario
            # Usamos el email como username para simplificar login, o generamos uno
            username = datos['email'].split('@')[0]
            # Asegurar unicidad básica de username
            if User.objects.filter(username=username).exists():
                username = f"{username}_{random.randint(1,999)}"

            user = User.objects.create_user(
                username=username,
                email=datos['email'],
                password=password,
                first_name=datos['first_name'],
                last_name=datos['last_name']
            )

            # 2. Crear Empresa
            empresa, created_empresa = Empresa.objects.get_or_create(
                nombre=datos['nombre_empresa'],
                defaults={'plan': datos['plan']}
            )

            # 3. Obtener el Perfil y actualizarlo (La corrección que hicimos antes)
            perfil, created_perfil = PerfilUsuario.objects.get_or_create(user=user)
            perfil.empresa = empresa
            perfil.rol = 'admin_empresa'
            perfil.save()

            # 4. Limpiar Sesión y Loguear
            del request.session['registro_temp']
            login(request, user)
            
            return redirect('dashboard') # ¡ADENTRO!
            
    else:
        form = PasswordSetupForm()

    return render(request, 'registro/registro_password.html', {'form': form})