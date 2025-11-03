from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """
    Configuración personalizada para el modelo Usuario en el panel de administración.
    Simplificado para mostrar solo la información relevante.
    """
    # Campos a mostrar en la lista de usuarios
    list_display = ('email', 'nombre', 'apellido', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    
    # Campos para el formulario de edición
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('nombre', 'apellido', 'rut', 'telefono')}),
        ('Archivos', {'fields': ('foto_perfil', 'antecedentes_medicos')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'role')}),
        ('Fechas Importantes', {'fields': ('date_joined', 'last_login')}),
    )
    
    # Campos para el formulario de creación de un nuevo usuario
    add_fieldsets = (
        (None, {'fields': ('email', 'nombre', 'apellido', 'password', 'password2')}),
    )
    search_fields = ('email', 'nombre', 'apellido')
    ordering = ('email',)
