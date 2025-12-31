from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('api/v1/datos/', views.api_datos, name='api_datos'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('proyectos/', views.lista_proyectos, name='lista_proyectos'),
    path('proyectos/crear/', views.crear_proyecto, name='crear_proyecto'),
    path('proyectos/<int:pk>/', views.detalle_proyecto, name='detalle_proyecto'),
    path('estaciones/', views.lista_estaciones, name='lista_estaciones'),
    path('estaciones/crear/', views.crear_estacion, name='crear_estacion'),
    #path('registro/', views.registro_usuario, name='registro'),
    path('planes/', views.planes_precios, name='planes_precios'),

    # Rutas para registro
    path('registro/', views.registro_paso1, name='registro'),
    path('registro/verificar/', views.registro_verificacion, name='registro_verificacion'),
    path('registro/password/', views.registro_password, name='registro_password'),
]