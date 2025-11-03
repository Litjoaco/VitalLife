from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
from usuario.models import Usuario
from django.db.models import Q
from .models import Especialidad, Cita, HorarioBloqueado
from .forms import EspecialidadForm, AdminUsuarioEditForm

def es_staff(user):
    """
    Función de prueba para decoradores que verifica si un usuario es staff.
    """
    return user.is_staff

@login_required
@user_passes_test(es_staff, login_url='usuario:login')
def dashboard_redirect(request):
    """
    Redirige al usuario a su panel correspondiente basado en su rol.
    """
    if request.user.is_staff:
        return redirect(reverse('paneladmin:admin_dashboard'))
    else:
        return redirect(reverse('usuario:panel_inicio'))

@login_required
@user_passes_test(es_staff, login_url='usuario:login')
def admin_dashboard_view(request):
    total_usuarios = Usuario.objects.count()
    total_especialidades = Especialidad.objects.count()
    context = {
        'total_usuarios': Usuario.objects.count(),
        'total_especialidades': Especialidad.objects.count(),
        'ultimos_usuarios': Usuario.objects.order_by('-date_joined')[:5]
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(es_staff, login_url='usuario:login')
def lista_especialidades_view(request):
    especialidades = Especialidad.objects.all().order_by('nombre')
    return render(request, 'lista_especialidades.html', {'especialidades': especialidades})

@login_required
@user_passes_test(es_staff, login_url='usuario:login')
def crear_especialidad_view(request):
    if request.method == 'POST':
        form = EspecialidadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Especialidad creada con éxito.')
            return redirect('paneladmin:lista_especialidades')
    else:
        form = EspecialidadForm()
    return render(request, 'form_especialidad.html', {'form': form, 'titulo': 'Crear Nueva Especialidad'})

@login_required
@user_passes_test(es_staff, login_url='usuario:login')
def editar_especialidad_view(request, pk):
    especialidad = get_object_or_404(Especialidad, pk=pk)
    if request.method == 'POST':
        form = EspecialidadForm(request.POST, request.FILES, instance=especialidad)
        if form.is_valid():
            form.save()
            messages.success(request, 'Especialidad actualizada con éxito.')
            return redirect('paneladmin:lista_especialidades')
    else:
        form = EspecialidadForm(instance=especialidad)
    return render(request, 'form_especialidad.html', {'form': form, 'titulo': f'Editar {especialidad.nombre}'})

@login_required
@user_passes_test(es_staff, login_url='usuario:login')
def eliminar_especialidad_view(request, pk):
    especialidad = get_object_or_404(Especialidad, pk=pk)
    if request.method == 'POST':
        nombre_especialidad = especialidad.nombre
        especialidad.delete()
        messages.success(request, f'La especialidad "{nombre_especialidad}" ha sido eliminada.')
        return redirect('paneladmin:lista_especialidades')
    return render(request, 'confirmar_eliminar_especialidad.html', {'especialidad': especialidad})

@login_required
@user_passes_test(es_staff, login_url='usuario:login')
def lista_usuarios_view(request):
    # Excluimos al superusuario de la lista
    queryset = Usuario.objects.filter(is_superuser=False).order_by('nombre')

    # Búsqueda
    query = request.GET.get('q')
    if query:
        queryset = queryset.filter(
            Q(nombre__icontains=query) | Q(apellido__icontains=query) | Q(email__icontains=query)
        )

    # Filtro por rol
    role_filter = request.GET.get('role')
    if role_filter and role_filter in [choice[0] for choice in Usuario.Role.choices]:
        queryset = queryset.filter(role=role_filter)

    context = {
        'usuarios': queryset,
        'roles': Usuario.Role.choices,
        'current_role': role_filter,
    }
    return render(request, 'lista_usuarios.html', context)

@login_required
@user_passes_test(es_staff, login_url='usuario:login')
def editar_usuario_view(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk, is_superuser=False)
    if request.method == 'POST':
        form = AdminUsuarioEditForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Usuario "{usuario.get_full_name()}" actualizado con éxito.')
            return redirect('paneladmin:lista_usuarios')
    else:
        form = AdminUsuarioEditForm(instance=usuario)
    
    context = {
        'form': form,
        'usuario_editado': usuario,
        'titulo': f'Editar Usuario: {usuario.get_full_name()}'
    }
    return render(request, 'form_usuario.html', context)

@login_required
@user_passes_test(es_staff, login_url='usuario:login')
def eliminar_usuario_view(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk, is_superuser=False)
    if request.method == 'POST':
        nombre_usuario = usuario.get_full_name()
        usuario.delete()
        messages.success(request, f'El usuario "{nombre_usuario}" ha sido eliminado.')
        return redirect('paneladmin:lista_usuarios')
    return render(request, 'confirmar_eliminar_usuario.html', {'usuario_a_eliminar': usuario})

@user_passes_test(lambda u: u.is_staff)
def lista_citas_view(request):
    queryset = Cita.objects.all().select_related('paciente', 'medico', 'especialidad').order_by('-fecha_hora')

    # Búsqueda por nombre de paciente o médico
    query = request.GET.get('q')
    if query:
        queryset = queryset.filter(
            Q(paciente__nombre__icontains=query) | Q(paciente__apellido__icontains=query) |
            Q(medico__nombre__icontains=query) | Q(medico__apellido__icontains=query)
        )

    # Filtro por estado
    estado_filter = request.GET.get('estado')
    if estado_filter and estado_filter in [choice[0] for choice in Cita.EstadoCita.choices]:
        queryset = queryset.filter(estado=estado_filter)

    context = {
        'citas': queryset,
        'estados': Cita.EstadoCita.choices,
        'current_estado': estado_filter,
    }
    return render(request, 'lista_citas.html', context)

@user_passes_test(lambda u: u.is_staff)
def admin_cancelar_cita_view(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    if request.method == 'POST':
        cita.estado = Cita.EstadoCita.CANCELADA
        cita.save()
        messages.success(request, 'La cita ha sido cancelada con éxito.')
        return redirect('paneladmin:lista_citas')
    
    return render(request, 'admin_confirmar_cancelar_cita.html', {'cita': cita})

@user_passes_test(lambda u: u.is_staff)
def admin_gestionar_horarios_view(request, doctor_id=None):
    if doctor_id is None:
        # Si no hay ID de doctor, mostramos la lista para seleccionar uno
        medicos = Usuario.objects.filter(role='MEDICO').order_by('apellido', 'nombre')
        context = {
            'medicos': medicos
        }
        return render(request, 'admin_seleccionar_medico.html', context)

    # Si hay un ID, mostramos el calendario para ese doctor
    doctor = get_object_or_404(Usuario, id=doctor_id, role='MEDICO')
    
    fecha_base_str = request.GET.get('fecha', datetime.today().strftime('%Y-%m-%d'))
    try:
        fecha_base = datetime.strptime(fecha_base_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        fecha_base = datetime.today().date()

    start_of_week = fecha_base - timedelta(days=fecha_base.weekday())
    dias_semana = [start_of_week + timedelta(days=i) for i in range(5)]
    previous_week = start_of_week - timedelta(days=7)
    next_week = start_of_week + timedelta(days=7)
    
    horas_laborales = [datetime.strptime(f"{h}:00", "%H:%M").time() for h in range(10, 17)]

    start_of_week_dt = timezone.make_aware(datetime.combine(dias_semana[0], datetime.min.time()))
    end_of_week_dt = timezone.make_aware(datetime.combine(dias_semana[-1], datetime.max.time()))

    citas_qs = Cita.objects.filter(
        medico=doctor,
        fecha_hora__range=(start_of_week_dt, end_of_week_dt),
        estado=Cita.EstadoCita.RESERVADA  # Solo considerar citas reservadas
    ).select_related('paciente')
    citas_lookup = {cita.fecha_hora: cita for cita in citas_qs}
    
    bloqueos_utc = HorarioBloqueado.objects.filter(
        medico=doctor,
        fecha_hora__range=(start_of_week_dt, end_of_week_dt)
    ).values_list('fecha_hora', flat=True)

    horario_semanal = []
    for dia in dias_semana:
        slots_dia = []
        for hora in horas_laborales:
            fecha_hora_slot = timezone.make_aware(datetime.combine(dia, hora))
            slot_info = {
                'fecha_hora': fecha_hora_slot, 'estado': 'disponible', 'paciente': None
            }
            if fecha_hora_slot in citas_lookup:
                slot_info['estado'] = 'reservado'
                slot_info['paciente'] = citas_lookup[fecha_hora_slot].paciente
            elif fecha_hora_slot in bloqueos_utc:
                slot_info['estado'] = 'bloqueado'
            slots_dia.append(slot_info)
        horario_semanal.append({'dia': dia, 'slots': slots_dia})

    context = {
        'doctor': doctor,
        'horario_semanal': horario_semanal,
        'horas_laborales': horas_laborales,
        'start_of_week': start_of_week,
        'previous_week': previous_week,
        'next_week': next_week,
    }
    return render(request, 'admin_gestionar_horarios.html', context)

@user_passes_test(lambda u: u.is_staff)
def admin_bloquear_horario_view(request):
    if request.method == 'POST':
        fecha_hora_str = request.POST.get('fecha_hora')
        doctor_id = request.POST.get('doctor_id')
        fecha_hora = datetime.fromisoformat(fecha_hora_str)
        doctor = get_object_or_404(Usuario, id=doctor_id)
        HorarioBloqueado.objects.get_or_create(medico=doctor, fecha_hora=fecha_hora)
        return JsonResponse({'status': 'ok', 'accion': 'bloqueado'})
    return JsonResponse({'status': 'error'}, status=400)

@user_passes_test(lambda u: u.is_staff)
def admin_desbloquear_horario_view(request):
    if request.method == 'POST':
        fecha_hora_str = request.POST.get('fecha_hora')
        doctor_id = request.POST.get('doctor_id')
        fecha_hora = datetime.fromisoformat(fecha_hora_str)
        doctor = get_object_or_404(Usuario, id=doctor_id)
        HorarioBloqueado.objects.filter(medico=doctor, fecha_hora=fecha_hora).delete()
        return JsonResponse({'status': 'ok', 'accion': 'desbloqueado'})
    return JsonResponse({'status': 'error'}, status=400)
