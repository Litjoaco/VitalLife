from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# --- Lógica para crear usuarios (necesaria para el modelo personalizado) ---
class UsuarioManager(BaseUserManager):
    """
    Manager para el modelo de Usuario personalizado.
    Sabe cómo crear usuarios y superusuarios.
    """
    def create_user(self, email, nombre, apellido, password=None, **extra_fields):
        if not email:
            raise ValueError(_('El campo Email es obligatorio'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, nombre=nombre, apellido=apellido, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nombre, apellido, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('El superusuario debe tener is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('El superusuario debe tener is_superuser=True.'))

        return self.create_user(email, nombre, apellido, password, **extra_fields)

# --- Modelo de Usuario Simplificado ---
class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de Usuario personalizado con los campos justos y necesarios.
    """
    # --- El orden que pediste ---
    # id: Django lo añade automáticamente.
    # password: Es manejado por AbstractBaseUser.
    nombre = models.CharField(_('nombre'), max_length=150)
    apellido = models.CharField(_('apellido'), max_length=150)
    email = models.EmailField(
        _('correo electrónico'), 
        unique=True,
        help_text=_('El correo electrónico se usará para iniciar sesión.')
    )
    rut = models.CharField(_('RUT'), max_length=12, unique=True, null=True, blank=True)
    fecha_nacimiento = models.DateField(_("fecha de nacimiento"), blank=True, null=True)
    telefono = models.CharField(_('número de teléfono'), max_length=15, blank=True)
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Administrador')
        MEDICO = 'MEDICO', _('Médico')
        USUARIO = 'USUARIO', _('Usuario')
    
    role = models.CharField(_('rol'), max_length=10, choices=Role.choices, default=Role.USUARIO)
    especialidad = models.ForeignKey(
        'paneladmin.Especialidad',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('especialidad'),
        help_text=_('Asignar solo si el rol es Médico.')
    )
    foto_perfil = models.ImageField(_('foto de perfil'), upload_to='fotos_perfil/', null=True, blank=True)
    antecedentes_medicos = models.FileField(
        _('antecedentes médicos'), 
        upload_to='antecedentes/', 
        blank=True, 
        null=True
    )

    # --- Campos internos de Django (necesarios para que funcione el admin y el login) ---
    is_staff = models.BooleanField(
        _('es administrador'),
        default=False,
        help_text=_('Designa si el usuario puede iniciar sesión en el panel de administración.')
    )
    # Los siguientes campos son requeridos por Django, los mantenemos para la compatibilidad.
    is_active = models.BooleanField(
        _('está activo'),
        default=True,
        help_text=_('Designa si este usuario debe ser tratado como activo. Desmárcalo en lugar de eliminar la cuenta.')
    )
    # Este campo se llamará 'fecha_registro' en la base de datos y solo guardará la fecha.
    date_joined = models.DateField(
        _('fecha de registro'),
        default=timezone.now,
        db_column='fecha_registro'
    )

    # --- Campos para seguridad de Login ---
    login_attempts = models.IntegerField(default=0, help_text="Contador de intentos de login fallidos.")
    last_failed_login = models.DateTimeField(null=True, blank=True, help_text="Fecha y hora del último intento fallido.")

    # --- Configuraciones del Modelo ---
    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellido']

    class Meta:
        verbose_name = _('usuario')
        verbose_name_plural = _('usuarios')

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.nombre} {self.apellido}"

    def get_short_name(self):
        return self.nombre
