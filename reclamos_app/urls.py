from django.urls import path
from . import views

app_name = 'reclamos'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('reclamos/', views.lista_reclamos, name='lista_reclamos'),
    path('reclamos/nuevo/', views.crear_reclamo, name='crear_reclamo'),
    path('reclamos/<int:pk>/', views.detalle_reclamo, name='detalle_reclamo'),
    path('reclamos/<int:pk>/editar/', views.editar_reclamo, name='editar_reclamo'),
    path('reclamos/<int:pk>/eliminar/', views.eliminar_reclamo, name='eliminar_reclamo'),
    path('notificaciones/<int:pk>/marcar-leida/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
] 