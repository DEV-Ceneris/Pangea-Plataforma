from django import forms
from .models import Proyecto, Estacion, Empresa
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

# Estilos reutilizables
TW_INPUT = "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-brand focus:border-brand block w-full p-2.5"

# ==========================================
#  Formularios de Registro Multietapa
# ==========================================

# --- PASO 1: DATOS INICIALES ---
class RegistroPaso1Form(forms.Form):
    nombre_empresa = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'Ej: Minera San Juan'}))
    first_name = forms.CharField(label="Nombres", max_length=100, widget=forms.TextInput(attrs={'class': TW_INPUT}))
    last_name = forms.CharField(label="Apellidos", max_length=100, widget=forms.TextInput(attrs={'class': TW_INPUT}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': TW_INPUT, 'placeholder': 'nombre@empresa.com'}))
    
    # Los Checks
    terminos = forms.BooleanField(required=True, error_messages={'required': 'Debes aceptar los términos y condiciones.'})
    privacidad = forms.BooleanField(required=True, error_messages={'required': 'Debes aceptar la política de privacidad.'})

    def clean_nombre_empresa(self):
        nombre = self.cleaned_data.get('nombre_empresa')
        if Empresa.objects.filter(nombre=nombre).exists():
            raise ValidationError("Esta empresa ya está registrada. Por favor elige otro nombre.")
        return nombre

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado.")
        return email

# --- PASO 2: CÓDIGO DE VERIFICACIÓN ---
class VerificacionForm(forms.Form):
    codigo = forms.CharField(max_length=6, widget=forms.TextInput(attrs={
        'class': 'bg-gray-50 border border-gray-300 text-center text-2xl tracking-widest text-gray-900 rounded-lg focus:ring-brand focus:border-brand block w-full p-2.5',
        'placeholder': '000000',
        'maxlength': '6'
    }))

# --- PASO 3: CONTRASEÑA ---
class PasswordSetupForm(forms.Form):
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': TW_INPUT, 'placeholder': '••••••••'}))
    confirm_password = forms.CharField(label="Confirmar Contraseña", widget=forms.PasswordInput(attrs={'class': TW_INPUT, 'placeholder': '••••••••'}))

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Las contraseñas no coinciden.")
        return cleaned_data

# creo que este se va a borrar.

class RegistroEmpresaForm(UserCreationForm):
    # Definimos los estilos comunes una sola vez
    TAILWIND_CLASS = "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-brand focus:border-brand block w-full p-2.5 placeholder-gray-400"

    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': TAILWIND_CLASS, 'placeholder': 'nombre@empresa.com'}))
    nombre_empresa = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': TAILWIND_CLASS, 'placeholder': 'Ej: Minera San Juan S.A.'}))
    first_name = forms.CharField(label="Nombre", max_length=100, required=True, widget=forms.TextInput(attrs={'class': TAILWIND_CLASS}))
    # Campo oculto del plan
    plan_seleccionado = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email', 'nombre_empresa', 'plan_seleccionado']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicamos el estilo al campo de usuario que viene por defecto
        self.fields['username'].widget.attrs.update({'class': self.TAILWIND_CLASS})

class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['nombre', 'descripcion', 'fecha_inicio', 'usuarios_asignados']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-1 focus:ring-brand focus:border-brand'}),
            'descripcion': forms.Textarea(attrs={'class': 'w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-1 focus:ring-brand focus:border-brand', 'rows': 3}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-1 focus:ring-brand focus:border-brand'}),
            'usuarios_asignados': forms.SelectMultiple(attrs={'class': 'w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-1 focus:ring-brand focus:border-brand'}),
        }

class EstacionForm(forms.ModelForm):
    class Meta:
        model = Estacion
        fields = ['nombre', 'codigo_identificador', 'proyecto', 'latitud', 'longitud', 'limite_oxigeno_min', 'limite_bateria_min']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-brand focus:border-brand'}),
            'codigo_identificador': forms.TextInput(attrs={'class': 'w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-brand focus:border-brand', 'placeholder': 'Ej: 21738'}),
            'proyecto': forms.Select(attrs={'class': 'w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-brand focus:border-brand'}),
            'latitud': forms.NumberInput(attrs={'class': 'w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-brand focus:border-brand', 'step': 'any'}),
            'longitud': forms.NumberInput(attrs={'class': 'w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-brand focus:border-brand', 'step': 'any'}),
            'limite_oxigeno_min': forms.NumberInput(attrs={'class': 'w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-brand focus:border-brand'}),
            'limite_bateria_min': forms.NumberInput(attrs={'class': 'w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-brand focus:border-brand'}),
        }

    def __init__(self, user, *args, **kwargs):
        super(EstacionForm, self).__init__(*args, **kwargs)
        # Filtramos el campo 'proyecto'
        if not user.is_superuser:
            self.fields['proyecto'].queryset = user.proyectos.all()


