from django.urls import path
from . import views

app_name = 'paneladmin'

urlpatterns = [
    path('', views.dashboard_redirect, name='dashboard_redirect'),
    path('dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('especialidades/', views.lista_especialidades_view, name='lista_especialidades'), # Nueva
    path('especialidades/crear/', views.crear_especialidad_view, name='crear_especialidad'), # Nueva
    path('especialidades/editar/<int:pk>/', views.editar_especialidad_view, name='editar_especialidad'), # Nueva
    path('especialidades/eliminar/<int:pk>/', views.eliminar_especialidad_view, name='eliminar_especialidad'), # Nueva
    path('usuarios/', views.lista_usuarios_view, name='lista_usuarios'),
    path('usuarios/editar/<int:pk>/', views.editar_usuario_view, name='editar_usuario'),
    path('usuarios/eliminar/<int:pk>/', views.eliminar_usuario_view, name='eliminar_usuario'),
    # URLs para gestionar citas
    path('citas/', views.lista_citas_view, name='lista_citas'),
    path('citas/cancelar/<int:cita_id>/', views.admin_cancelar_cita_view, name='admin_cancelar_cita'),
    # URLs para gestionar horarios de médicos
    path('horarios/', views.admin_gestionar_horarios_view, name='admin_gestionar_horarios'),
    path('horarios/<int:doctor_id>/', views.admin_gestionar_horarios_view, name='admin_gestionar_horarios_medico'),
    path('horarios/bloquear/', views.admin_bloquear_horario_view, name='admin_bloquear_horario'),
    path('horarios/desbloquear/', views.admin_desbloquear_horario_view, name='admin_desbloquear_horario'),
    # --- URL para Reportes ---
    path('reportes/', views.reportes_administrativos_view, name='reportes_administrativos'),
]