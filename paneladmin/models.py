from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class Especialidad(models.Model):
    nombre = models.CharField(_('nombre'), max_length=100, unique=True)
    descripcion = models.TextField(_('descripción'), blank=True)
    imagen = models.ImageField(_('imagen de fondo'), upload_to='especialidades/', help_text="Sube una imagen representativa para la especialidad.")

    class Meta:
        verbose_name = _('especialidad')
        verbose_name_plural = _('especialidades')

    def __str__(self):
        return self.nombre

class Disponibilidad(models.Model):
    """
    Modelo para que los médicos definan sus bloques de disponibilidad.
    """
    medico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'MEDICO'},
        related_name='disponibilidades'
    )
    fecha = models.DateField(_("Fecha"))
    hora_inicio = models.TimeField(_("Hora de inicio"))
    hora_fin = models.TimeField(_("Hora de fin"))

    class Meta:
        verbose_name = _("Disponibilidad")
        verbose_name_plural = _("Disponibilidades")
        unique_together = ('medico', 'fecha') # Un médico solo puede tener un bloque de disponibilidad por día.

    def __str__(self):
        return f"Dr. {self.medico.get_full_name()} - {self.fecha} ({self.hora_inicio} - {self.hora_fin})"

class Cita(models.Model):
    """
    Modelo para almacenar las citas agendadas por los usuarios.
    """
    class EstadoCita(models.TextChoices):
        RESERVADA = 'RESERVADA', _('Reservada')
        COMPLETADA = 'COMPLETADA', _('Completada')
        CANCELADA = 'CANCELADA', _('Cancelada')

    paciente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='citas_como_paciente')
    medico = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='citas_como_medico')
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField(_("Fecha y Hora"))
    motivo = models.TextField(_("Motivo de la consulta"), blank=True)
    estado = models.CharField(_("Estado"), max_length=15, choices=EstadoCita.choices, default=EstadoCita.RESERVADA)

    class Meta:
        verbose_name = _("Cita")
        verbose_name_plural = _("Citas")
        unique_together = ('medico', 'fecha_hora') # Evita que un médico tenga dos citas a la misma hora.

    def __str__(self):
        return f"Cita de {self.paciente} con Dr. {self.medico.get_full_name()} el {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"

class HorarioBloqueado(models.Model):
    """
    Modelo para que los médicos bloqueen horas específicas de su horario estándar.
    """
    medico = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='horarios_bloqueados')
    fecha_hora = models.DateTimeField(_("Fecha y Hora Bloqueada"))

    class Meta:
        verbose_name = _("Horario Bloqueado")
        verbose_name_plural = _("Horarios Bloqueados")
        unique_together = ('medico', 'fecha_hora')

    def __str__(self):
        return f"Bloqueo de Dr. {self.medico.get_full_name()} el {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"

class Diagnostico(models.Model):
    """
    Modelo para almacenar el diagnóstico asociado a una cita.
    """
    cita = models.OneToOneField(Cita, on_delete=models.CASCADE, related_name='diagnostico', verbose_name=_("Cita"))
    titulo = models.CharField(_("Título"), max_length=200)
    descripcion = models.TextField(_("Descripción"))
    fecha_creacion = models.DateTimeField(_("Fecha de creación"), auto_now_add=True)

    class Meta:
        verbose_name = _("Diagnóstico")
        verbose_name_plural = _("Diagnósticos")

    def __str__(self):
        return f"Diagnóstico para la cita de {self.cita.paciente.get_full_name()} el {self.cita.fecha_hora.strftime('%d/%m/%Y')}"

class Receta(models.Model):
    """
    Modelo para almacenar recetas médicas (archivos) asociadas a una cita.
    """
    cita = models.ForeignKey(Cita, on_delete=models.CASCADE, related_name='recetas', verbose_name=_("Cita"))
    titulo = models.CharField(_("Título"), max_length=200)
    archivo = models.FileField(_("Archivo de receta"), upload_to='recetas/%Y/%m/%d/')
    indicaciones = models.TextField(_("Indicaciones"), blank=True)
    fecha_creacion = models.DateTimeField(_("Fecha de creación"), auto_now_add=True)

    class Meta:
        verbose_name = _("Receta")
        verbose_name_plural = _("Recetas")

    def __str__(self):
        return f"Receta '{self.titulo}' para la cita de {self.cita.paciente.get_full_name()}"

class FichaMedica(models.Model):
    """
    Modelo para almacenar la ficha médica de un paciente, editable por los médicos.
    """
    paciente = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='ficha_medica',
        verbose_name=_("Paciente")
    )
    altura_cm = models.PositiveIntegerField(_("Altura (cm)"), null=True, blank=True, help_text="Altura en centímetros.")
    peso_kg = models.DecimalField(_("Peso (kg)"), max_digits=5, decimal_places=2, null=True, blank=True, help_text="Peso en kilogramos.")
    
    class TipoSangre(models.TextChoices):
        A_POS = 'A+', 'A+'
        A_NEG = 'A-', 'A-'
        B_POS = 'B+', 'B+'
        B_NEG = 'B-', 'B-'
        AB_POS = 'AB+', 'AB+'
        AB_NEG = 'AB-', 'AB-'
        O_POS = 'O+', 'O+'
        O_NEG = 'O-', 'O-'
        NO_SABE = 'NS', 'No sabe'

    tipo_sangre = models.CharField(_("Tipo de Sangre"), max_length=3, choices=TipoSangre.choices, blank=True)
    alergias = models.TextField(_("Alergias conocidas"), blank=True, help_text="Listar alergias a medicamentos, alimentos, etc.")
    enfermedades_cronicas = models.TextField(_("Enfermedades Crónicas"), blank=True, help_text="Listar condiciones médicas preexistentes.")
    ultima_actualizacion = models.DateTimeField(_("Última actualización"), auto_now=True)

    def __str__(self):
        return f"Ficha Médica de {self.paciente.get_full_name()}"