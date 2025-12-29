from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import DatosSensor
from .models import DatosSensor, Proyecto, Estacion
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProyectoForm, EstacionForm

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
    
    return render(request, 'login.html', {'form': form})

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
    """Muestra la lista de proyectos asignados al usuario"""
    usuario = request.user
    
    if usuario.is_superuser:
        # El admin ve todo
        proyectos = Proyecto.objects.all()
    else:
        # El usuario normal solo ve sus asignados
        proyectos = usuario.proyectos.all()
    
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