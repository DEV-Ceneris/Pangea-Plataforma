from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('api/v1/datos/', views.api_datos, name='api_datos'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('proyectos/', views.lista_proyectos, name='lista_proyectos'),
    path('proyectos/crear/', views.crear_proyecto, name='crear_proyecto'),
    path('proyectos/<int:pk>/', views.detalle_proyecto, name='detalle_proyecto'),
    path('estaciones/', views.lista_estaciones, name='lista_estaciones'),
    path('estaciones/crear/', views.crear_estacion, name='crear_estacion'),
]