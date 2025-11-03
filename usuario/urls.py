from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'usuario'

urlpatterns = [
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    path('panel/', views.panel_inicio_view, name='panel_inicio'),
    path('seleccionar-especialidad/', views.seleccionar_especialidad_view, name='seleccionar_especialidad'),
    path('seleccionar-horario/<int:especialidad_id>/', views.seleccionar_horario_view, name='seleccionar_horario'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('perfil/editar/', views.editar_perfil_view, name='editar_perfil'),
    path('cita/<int:cita_id>/', views.detalle_cita_view, name='detalle_cita'),
    path('cita/cancelar/<int:cita_id>/', views.cancelar_cita_view, name='cancelar_cita'),
    path('medico/inicio/', views.medico_inicio_view, name='medico_inicio'),
    path('medico/dashboard/', views.medico_dashboard_view, name='medico_dashboard'),
    path('medico/horarios/', views.gestionar_horarios_view, name='gestionar_horarios'),
    path('medico/horarios/bloquear/', views.bloquear_horario_view, name='bloquear_horario'),
    path('medico/horarios/desbloquear/', views.desbloquear_horario_view, name='desbloquear_horario'),
    path('agendar-cita/', views.agendar_cita_view, name='agendar_cita'),

    # --- NUEVAS URLS PARA GESTIÓN DE PACIENTES ---
    path('medico/pacientes/', views.lista_pacientes_view, name='lista_pacientes'),
    path('medico/pacientes/<int:paciente_id>/', views.detalle_paciente_view, name='detalle_paciente'),
]