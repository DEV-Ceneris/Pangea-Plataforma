from django import forms
from .models import Proyecto, Estacion

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