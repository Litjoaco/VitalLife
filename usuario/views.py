from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, Http404
from django.utils import timezone
from .forms import RegistroUsuarioForm, LoginForm, DiagnosticoForm, RecetaForm, PerfilUsuarioForm, FichaMedicaForm
from paneladmin.models import Especialidad, Cita, HorarioBloqueado, FichaMedica
from .models import Usuario
from datetime import date, datetime, timedelta

def inicio(request):
    # Si el usuario ya está autenticado, redirigirlo a su panel de inicio.
    if request.user.is_authenticated:
        return redirect('usuario:panel_inicio')
    return render(request, 'inicio.html')

def registro_view(request):
    # También es buena práctica redirigir si intentan registrarse ya logueados.
    if request.user.is_authenticated:
        return redirect('usuario:panel_inicio')
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # Usando messages de Django para mostrar una alerta de éxito.
            # Necesitarás SweetAlert2 para que se vea bien.
            messages.success(request, '¡Tu cuenta ha sido creada con éxito! Ahora puedes iniciar sesión.')
            return redirect('inicio') # Redirige a la página de inicio
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'registro.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('usuario:panel_inicio')

    if request.method == 'POST':
        form = LoginForm(request=request, data=request.POST)
        email = form.data.get('username')
        
        try:
            user_obj = Usuario.objects.get(email=email)
            # Verificar si la cuenta está bloqueada
            if user_obj.login_attempts >= 5 and user_obj.last_failed_login and (timezone.now() - user_obj.last_failed_login).total_seconds() < 900: # 15 minutos
                minutes_left = 15 - int((timezone.now() - user_obj.last_failed_login).total_seconds() / 60)
                messages.error(request, f'Demasiados intentos fallidos. Tu cuenta está bloqueada por {minutes_left} minutos.')
                return render(request, 'login.html', {'form': form})
        except Usuario.DoesNotExist:
            user_obj = None

        if form.is_valid():
            user = form.get_user()
            if user is not None:
                # Reiniciar contador de intentos al iniciar sesión con éxito
                user.login_attempts = 0
                user.save()
                login(request, user)
                return redirect('usuario:panel_inicio')
        else:
            # Si el formulario no es válido, es un intento fallido.
            if user_obj:
                user_obj.login_attempts += 1
                user_obj.last_failed_login = timezone.now()
                user_obj.save()

        messages.error(request, 'Correo electrónico o contraseña incorrectos. Por favor, inténtalo de nuevo.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

@login_required
def seleccionar_especialidad_view(request):
    """Esta es la nueva vista principal para el usuario logueado."""
    especialidades = Especialidad.objects.all()
    context = {
        'especialidades': especialidades
    }
    return render(request, 'seleccionar_especialidad.html', context)

@login_required
def panel_inicio_view(request):
    """
    Redirige al usuario a su panel de control correspondiente según su rol.
    """
    # Redirigir al usuario a su panel correspondiente según su rol
    if request.user.role == 'MEDICO':
        return redirect('usuario:medico_inicio')
    # Para todos los demás roles (USUARIO, ADMIN), mostrar el panel de usuario principal.
    
    now = timezone.now()
    
    # Buscar la próxima cita del usuario
    proxima_cita = Cita.objects.filter(
        paciente=request.user,
        fecha_hora__gte=now,
        estado='RESERVADA'
    ).select_related('medico', 'especialidad').order_by('fecha_hora').first()

    # Contar las citas pasadas para mostrar un dato interesante
    citas_pasadas_count = Cita.objects.filter(
        paciente=request.user,
        fecha_hora__lt=now
    ).count()

    context = {
        'proxima_cita': proxima_cita,
        'citas_pasadas_count': citas_pasadas_count,
    }
    return render(request, 'panel_inicio.html', context)

@login_required
def perfil_view(request):
    # Obtener todas las citas del paciente, ordenadas de más reciente a más antigua.
    # Usamos prefetch_related para cargar diagnósticos y recetas de forma eficiente.
    citas_paciente = Cita.objects.filter(paciente=request.user).order_by('-fecha_hora').prefetch_related(
        'diagnostico', 'recetas', 'medico', 'especialidad'
    )

    # Obtener la ficha médica del usuario para mostrarla en el perfil.
    ficha_medica = FichaMedica.objects.filter(paciente=request.user).first()

    context = {
        'citas': citas_paciente,
        'ficha_medica': ficha_medica,
    }
    return render(request, 'perfil.html', context)

@login_required
def editar_perfil_view(request):
    if request.method == 'POST':
        # Pasamos request.FILES para manejar la subida de la foto de perfil y antecedentes
        form = PerfilUsuarioForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Tu perfil ha sido actualizado con éxito!')
            return redirect('usuario:perfil')
    else:
        form = PerfilUsuarioForm(instance=request.user)

    context = {
        'form': form
    }
    return render(request, 'editar_perfil.html', context)

@login_required
def detalle_cita_view(request, cita_id):
    # Usamos prefetch_related para cargar diagnósticos y recetas de forma eficiente.
    # MEJORA DE SEGURIDAD: Añadimos 'paciente=request.user' al filtro.
    # Esto asegura que un usuario solo pueda ver sus propias citas.
    # Si intenta acceder a una URL de una cita ajena, recibirá un error 404.
    cita = get_object_or_404(
        Cita.objects.select_related('medico', 'especialidad', 'diagnostico').prefetch_related('recetas'),
        id=cita_id,
        paciente=request.user
    )

    context = {
        'cita': cita,
        'now': timezone.now()
    }
    return render(request, 'detalle_cita.html', context)

@login_required
def cancelar_cita_view(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, paciente=request.user)

    # Regla de negocio: Solo se pueden cancelar citas futuras y que estén reservadas.
    if cita.fecha_hora <= timezone.now() or cita.estado != Cita.EstadoCita.RESERVADA:
        messages.error(request, 'Esta cita ya no puede ser cancelada.')
        return redirect('usuario:detalle_cita', cita_id=cita.id)

    if request.method == 'POST':
        cita.estado = Cita.EstadoCita.CANCELADA
        cita.save()
        messages.success(request, 'Tu cita ha sido cancelada con éxito.')
        return redirect('usuario:perfil')

    context = {
        'cita': cita
    }
    return render(request, 'confirmar_cancelar_cita.html', context)

@login_required
def seleccionar_horario_view(request, especialidad_id):
    especialidad = get_object_or_404(Especialidad, id=especialidad_id)
    medicos = Usuario.objects.filter(role='MEDICO', especialidad=especialidad)

    # Obtener filtros del request
    medico_id_str = request.GET.get('medico')
    fecha_str = request.GET.get('fecha', date.today().strftime('%Y-%m-%d'))
    
    try:
        fecha_seleccionada = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        fecha_seleccionada = date.today()

    # Filtrar médicos si se seleccionó uno
    medicos_a_consultar = medicos
    if medico_id_str and medico_id_str != 'todos':
        medicos_a_consultar = medicos.filter(id=medico_id_str)

    # Horas de trabajo estándar
    horas_laborales = [datetime.strptime(f"{h}:00", "%H:%M").time() for h in range(10, 17)] # 10:00 a 16:00

    # --- CORRECCIÓN CLAVE: Consultar por rango de fecha/hora ---
    # Creamos el inicio y fin del día seleccionado, conscientes de la zona horaria.
    start_of_day = timezone.make_aware(datetime.combine(fecha_seleccionada, datetime.min.time()))
    end_of_day = timezone.make_aware(datetime.combine(fecha_seleccionada, datetime.max.time()))

    # Obtener citas y bloqueos
    citas_reservadas = Cita.objects.filter(
        medico__in=medicos_a_consultar,
        fecha_hora__range=(start_of_day, end_of_day),
        estado=Cita.EstadoCita.RESERVADA  # Solo contar citas reservadas
    )

    bloqueos = HorarioBloqueado.objects.filter(
        medico__in=medicos_a_consultar,
        fecha_hora__range=(start_of_day, end_of_day)
    )

    horas_no_disponibles_utc = {*citas_reservadas.values_list("fecha_hora", flat=True), *bloqueos.values_list("fecha_hora", flat=True)}

    # Generar horarios
    horarios_disponibles = []
    # --- VERIFICACIÓN: No generar horarios para fines de semana (Sábado=5, Domingo=6) ---
    if fecha_seleccionada.weekday() < 5:
        # Iterar sobre cada médico para encontrar la primera hora disponible para cada uno
        for medico in medicos_a_consultar:
            for hora in horas_laborales:
                # Hacemos que la fecha/hora sea consciente de la zona horaria actual
                fecha_hora_slot = timezone.make_aware(
                    datetime.combine(fecha_seleccionada, hora)
                )
                if fecha_hora_slot not in horas_no_disponibles_utc:
                    horarios_disponibles.append({
                        'medico': medico,
                        'fecha_hora': fecha_hora_slot
                    })

    # Ordenar por hora y luego por médico
    horarios_disponibles.sort(key=lambda x: (x['fecha_hora'], x['medico'].get_full_name()))

    context = {
        'especialidad': especialidad,
        'medicos': medicos,
        'horarios': horarios_disponibles,
        'fecha_seleccionada': fecha_seleccionada,
        'medico_seleccionado_id': medico_id_str,
    }
    return render(request, 'seleccionar_horario.html', context)


# --- VISTAS PARA MÉDICOS ---

def role_required(*roles):
    """
    Decorador que verifica si un usuario tiene uno de los roles especificados.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login') # O a donde quieras redirigir si no está logueado
            if request.user.role not in roles:
                raise PermissionDenied # Muestra un error 403 Prohibido
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

@login_required
@role_required('MEDICO')
def medico_inicio_view(request):
    today = timezone.now().date()
    citas_hoy_count = Cita.objects.filter(
        medico=request.user, 
        fecha_hora__date=today
    ).count()
    
    context = {
        'citas_hoy_count': citas_hoy_count,
    }
    return render(request, 'medico_inicio.html', context)

@login_required
@role_required('MEDICO')
def medico_dashboard_view(request):
    now = timezone.now()
    today = now.date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # Citas para hoy (lista completa, ordenada por hora)
    citas_hoy = Cita.objects.filter(
        medico=request.user, 
        fecha_hora__date=today
    ).select_related('paciente').order_by('fecha_hora')
    citas_hoy_count = citas_hoy.count()

    # Próxima cita del día (o futura)
    proxima_cita = Cita.objects.filter(
        medico=request.user,
        fecha_hora__gte=now
    ).select_related('paciente').order_by('fecha_hora').first()

    # Estadísticas
    total_pacientes = Cita.objects.filter(medico=request.user).values('paciente').distinct().count()
    
    # Citas de la semana (lista completa)
    citas_semana = Cita.objects.filter(
        medico=request.user, fecha_hora__date__range=[start_of_week, end_of_week]
    ).select_related('paciente').order_by('fecha_hora')
    citas_semana_count = citas_semana.count()

    context = {
        'citas_hoy_count': citas_hoy_count,
        'proxima_cita': proxima_cita,
        'total_pacientes': total_pacientes,
        'citas_semana_count': citas_semana_count,
        'citas_hoy': citas_hoy,
        'citas_semana': citas_semana,
    }
    
    return render(request, 'medico_dashboard.html', context)

@login_required
@role_required('MEDICO')
def gestionar_horarios_view(request):
    fecha_base_str = request.GET.get('fecha', date.today().strftime('%Y-%m-%d'))
    try:
        fecha_base = datetime.strptime(fecha_base_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        fecha_base = date.today()

    # Lunes de la semana actual
    start_of_week = fecha_base - timedelta(days=fecha_base.weekday())
    
    # Generar los 5 días de la semana
    dias_semana = [start_of_week + timedelta(days=i) for i in range(5)]
    previous_week = start_of_week - timedelta(days=7)
    next_week = start_of_week + timedelta(days=7)
    
    # Horas de trabajo estándar (10:00 a 16:00)
    horas_laborales = [datetime.strptime(f"{h}:00", "%H:%M").time() for h in range(10, 17)]

    # --- CORRECCIÓN CLAVE: Consultar por rango de fecha/hora ---
    start_of_week_dt = timezone.make_aware(datetime.combine(dias_semana[0], datetime.min.time()))
    end_of_week_dt = timezone.make_aware(datetime.combine(dias_semana[-1], datetime.max.time()))

    # Usamos select_related para traer los datos del paciente en la misma consulta y mejorar el rendimiento
    citas_qs = Cita.objects.filter(
        medico=request.user,
        fecha_hora__range=(start_of_week_dt, end_of_week_dt),
        estado=Cita.EstadoCita.RESERVADA  # Solo mostrar citas reservadas en el calendario
    ).select_related('paciente')

    # Creamos un diccionario para buscar citas fácilmente por fecha y hora
    citas_lookup = {cita.fecha_hora: cita for cita in citas_qs}
    
    bloqueos_utc = HorarioBloqueado.objects.filter(
        medico=request.user,
        fecha_hora__range=(start_of_week_dt, end_of_week_dt)
    ).values_list('fecha_hora', flat=True)

    # Crear una estructura de datos para la plantilla
    horario_semanal = []
    for dia in dias_semana:
        slots_dia = []
        for hora in horas_laborales:
            # Hacemos que la fecha/hora sea consciente de la zona horaria actual
            fecha_hora_slot = timezone.make_aware(
                datetime.combine(dia, hora)
            )
            slot_info = {
                'fecha_hora': fecha_hora_slot,
                'hora': hora,
                'estado': 'disponible',
                'paciente': None,
                'cita_id': None,
                'motivo': None,
            }
            if fecha_hora_slot in citas_lookup:
                cita = citas_lookup[fecha_hora_slot]
                slot_info['estado'] = 'reservado'
                slot_info['paciente'] = cita.paciente
                slot_info['cita_id'] = cita.id
                slot_info['motivo'] = cita.motivo
            elif fecha_hora_slot in bloqueos_utc:
                slot_info['estado'] = 'bloqueado'
            
            slots_dia.append(slot_info)
        horario_semanal.append({'dia': dia, 'slots': slots_dia})

    context = {
        'horario_semanal': horario_semanal,
        'horas_laborales': horas_laborales,
        'start_of_week': start_of_week,
        'previous_week': previous_week,
        'next_week': next_week,
    }
    return render(request, 'gestionar_horarios.html', context)

@login_required
@role_required('MEDICO')
def bloquear_horario_view(request):
    if request.method == 'POST':
        fecha_hora_str = request.POST.get('fecha_hora')
        fecha_hora = datetime.fromisoformat(fecha_hora_str)
        HorarioBloqueado.objects.get_or_create(medico=request.user, fecha_hora=fecha_hora)
        return JsonResponse({'status': 'ok', 'accion': 'bloqueado'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
@role_required('MEDICO')
def desbloquear_horario_view(request):
    if request.method == 'POST':
        fecha_hora_str = request.POST.get('fecha_hora')
        fecha_hora = datetime.fromisoformat(fecha_hora_str)
        HorarioBloqueado.objects.filter(medico=request.user, fecha_hora=fecha_hora).delete()
        return JsonResponse({'status': 'ok', 'accion': 'desbloqueado'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def agendar_cita_view(request):
    if request.method == 'POST':
        medico_id = request.POST.get('medico_id')
        especialidad_id = request.POST.get('especialidad_id')
        fecha_hora_str = request.POST.get('fecha_hora')
        motivo = request.POST.get('motivo', '')

        try:
            medico = Usuario.objects.get(id=medico_id, role='MEDICO')
            especialidad = Especialidad.objects.get(id=especialidad_id)
            
            # Convertimos el string ISO a un objeto datetime.
            # Esto es crucial para que Django lo maneje correctamente con la zona horaria.
            fecha_hora = timezone.datetime.fromisoformat(fecha_hora_str)

            # Doble verificación para evitar agendar en un horario ya ocupado (race condition)
            # La forma más segura de verificar es comparar el objeto datetime consciente de la zona horaria directamente.
            if Cita.objects.filter(medico=medico, fecha_hora=fecha_hora).exists() or \
               HorarioBloqueado.objects.filter(medico=medico, fecha_hora=fecha_hora).exists():
                return JsonResponse({'status': 'error', 'message': 'Lo sentimos, este horario ya no está disponible.'}, status=400)
            
            nueva_cita = Cita.objects.create(
                paciente=request.user,
                medico=medico,
                especialidad=especialidad,
                fecha_hora=fecha_hora,
                motivo=motivo
            )

            # Opcional: Enviar correo de confirmación aquí.

            return JsonResponse({
                'status': 'ok', 
                'message': '¡Tu cita ha sido agendada con éxito! Serás redirigido a tu panel.',
                'cita_id': nueva_cita.id
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Ocurrió un error al agendar la cita: {e}'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@login_required
@role_required('MEDICO')
def lista_pacientes_view(request):
    # Obtener IDs de pacientes únicos que tienen citas con el médico actual
    paciente_ids = Cita.objects.filter(medico=request.user).values_list('paciente_id', flat=True).distinct()
    pacientes = Usuario.objects.filter(id__in=paciente_ids).order_by('apellido', 'nombre')
    
    context = {
        'pacientes': pacientes
    }
    return render(request, 'lista_pacientes.html', context)

@login_required
@role_required('MEDICO')
def detalle_paciente_view(request, paciente_id):
    # Se elimina la restricción de rol. Un paciente puede ser cualquier usuario.
    paciente = get_object_or_404(Usuario, id=paciente_id)

    # Verificación de seguridad: El médico solo puede ver pacientes con los que tiene o ha tenido una cita.
    if not Cita.objects.filter(medico=request.user, paciente=paciente).exists():
        raise PermissionDenied("No tienes permiso para ver los detalles de este paciente.")

    # Manejar la subida de formularios
    if request.method == 'POST':
        # Primero, revisamos si se está enviando el formulario de la ficha médica.
        # Este formulario no depende de una cita específica.
        if 'submit_ficha' in request.POST:
            # Usamos get_or_create para manejar el caso de que la ficha aún no exista.
            ficha, created = FichaMedica.objects.get_or_create(paciente=paciente)
            ficha_form = FichaMedicaForm(request.POST, instance=ficha)
            if ficha_form.is_valid():
                ficha_form.save()
                messages.success(request, 'Ficha médica actualizada con éxito.')
                return redirect('usuario:detalle_paciente', paciente_id=paciente.id)
        
        # Si no es la ficha, entonces debe ser un formulario relacionado a una cita.
        else:
            cita_id = request.POST.get('cita_id')
            # Ahora sí, buscamos la cita porque es necesaria para diagnóstico o receta.
            cita = get_object_or_404(Cita, id=cita_id, medico=request.user, paciente=paciente)

            if 'submit_diagnostico' in request.POST:
                diagnostico_form = DiagnosticoForm(request.POST, prefix=f'diag-{cita.id}')
                if diagnostico_form.is_valid():
                    diagnostico = diagnostico_form.save(commit=False)
                    diagnostico.cita = cita
                    diagnostico.save()
                    messages.success(request, 'Diagnóstico guardado con éxito.')
                    return redirect('usuario:detalle_paciente', paciente_id=paciente.id)

            if 'submit_receta' in request.POST:
                receta_form = RecetaForm(request.POST, request.FILES, prefix=f'receta-{cita.id}')
                if receta_form.is_valid():
                    receta = receta_form.save(commit=False)
                    receta.cita = cita
                    receta.save()
                    messages.success(request, 'Receta subida con éxito.')
                    return redirect('usuario:detalle_paciente', paciente_id=paciente.id)

    # Obtener historial de citas con este médico, ordenadas de más reciente a más antigua
    citas = Cita.objects.filter(medico=request.user, paciente=paciente).order_by('-fecha_hora').prefetch_related(
        'diagnostico', 'recetas'
    )

    # Para cada cita, si no tiene diagnóstico, le adjuntamos un formulario nuevo.
    # Hacemos lo mismo para las recetas. Esto evita conflictos de ID en el HTML.
    for cita in citas:
        if not hasattr(cita, 'diagnostico'):
            cita.diagnostico_form = DiagnosticoForm(prefix=f'diag-{cita.id}')
        cita.receta_form = RecetaForm(prefix=f'receta-{cita.id}')

    # Obtener la ficha médica o crear una instancia de formulario vacía si no existe.
    ficha_medica = FichaMedica.objects.filter(paciente=paciente).first()
    ficha_form = FichaMedicaForm(instance=ficha_medica)

    context = {
        'paciente': paciente,
        'citas': citas,
        'ficha_form': ficha_form,
    }
    return render(request, 'detalle_paciente.html', context)