from django import forms
from django.utils.translation import gettext_lazy as _
from paneladmin.models import Diagnostico, Receta, Especialidad, FichaMedica
from datetime import date
from django.core.exceptions import ValidationError
from .models import Usuario
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

class RegistroUsuarioForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('nombre', 'apellido', 'email', 'rut', 'fecha_nacimiento', 'telefono', 'foto_perfil', 'antecedentes_medicos')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Añadir la clase 'form-control' a todos los campos para que Bootstrap los estilice
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control', 'id': 'id_password1'
        })
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['fecha_nacimiento'].widget = forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'}
        )
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})
        
        # Marcar campos opcionales
        self.fields['telefono'].required = False
        self.fields['foto_perfil'].required = False
        self.fields['antecedentes_medicos'].required = False

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        if not rut:
            return rut

        rut = rut.upper().replace(".", "").replace("-", "")
        if len(rut) < 2:
            raise forms.ValidationError("RUT inválido.")

        cuerpo = rut[:-1]
        dv = rut[-1]

        if not cuerpo.isdigit():
            raise forms.ValidationError("El cuerpo del RUT debe contener solo números.")

        try:
            suma = 0
            multiplo = 2
            for r in reversed(cuerpo):
                suma += int(r) * multiplo
                multiplo = multiplo + 1 if multiplo < 7 else 2
            
            resto = suma % 11
            dv_calculado = str(11 - resto)
            if dv_calculado == '11': dv_calculado = '0'
            if dv_calculado == '10': dv_calculado = 'K'

            if dv != dv_calculado:
                raise forms.ValidationError("El RUT ingresado no es válido (dígito verificador incorrecto).")
        except Exception:
            raise forms.ValidationError("Error al validar el RUT. Por favor, verifica el formato.")

        return self.cleaned_data['rut']

    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento:
            today = date.today()
            # Se considera mayor de edad si ya cumplió los 18 años.
            age = today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
            if age < 18:
                raise forms.ValidationError("Debes ser mayor de 18 años para registrarte.")
        return fecha_nacimiento

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono and not telefono.isdigit():
            raise forms.ValidationError("El número de teléfono solo debe contener dígitos.")
        if telefono and not (7 <= len(telefono) <= 15):
            raise forms.ValidationError("El número de teléfono debe tener entre 7 y 15 dígitos.")
        return telefono

    def clean_foto_perfil(self):
        foto = self.cleaned_data.get('foto_perfil')
        if foto:
            if foto.size > 2 * 1024 * 1024: # Límite de 2MB
                raise ValidationError("La foto de perfil no puede superar los 2MB.")
            if not foto.content_type in ['image/jpeg', 'image/png', 'image/gif']:
                raise ValidationError("Formato de imagen no válido. Sube un archivo JPG, PNG o GIF.")
        return foto

    def clean_antecedentes_medicos(self):
        archivo = self.cleaned_data.get('antecedentes_medicos')
        if archivo:
            if archivo.size > 5 * 1024 * 1024: # Límite de 5MB
                raise ValidationError("El archivo de antecedentes no puede superar los 5MB.")
        return archivo

class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label=_("Correo electrónico"),
        widget=forms.EmailInput(attrs={'autofocus': True, 'class': 'form-control', 'placeholder': 'ejemplo@correo.com'})
    )
    password = forms.CharField(
        label=_("Contraseña"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control', 'placeholder': 'Tu contraseña'}),
    )

class DiagnosticoForm(forms.ModelForm):
    class Meta:
        model = Diagnostico
        fields = ['titulo', 'descripcion']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'titulo': _('Título del Diagnóstico'),
            'descripcion': _('Descripción'),
        }

class RecetaForm(forms.ModelForm):
    class Meta:
        model = Receta
        fields = ['titulo', 'archivo', 'indicaciones']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
            'indicaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'titulo': _('Título de la Receta'),
            'archivo': _('Archivo (PDF, JPG, etc.)'),
            'indicaciones': _('Indicaciones (opcional)'),
        }

class PerfilUsuarioForm(forms.ModelForm):
    """
    Formulario para que los usuarios editen su propia información de perfil.
    """
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'telefono', 'fecha_nacimiento', 'foto_perfil', 'antecedentes_medicos']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'foto_perfil': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'antecedentes_medicos': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class FichaMedicaForm(forms.ModelForm):
    """
    Formulario para que los médicos editen la ficha médica de un paciente.
    """
    class Meta:
        model = FichaMedica
        fields = ['altura_cm', 'peso_kg', 'tipo_sangre', 'alergias', 'enfermedades_cronicas']
        widgets = {
            'altura_cm': forms.NumberInput(attrs={'class': 'form-control'}),
            'peso_kg': forms.NumberInput(attrs={'class': 'form-control'}),
            'tipo_sangre': forms.Select(attrs={'class': 'form-select'}),
            'alergias': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'enfermedades_cronicas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        help_texts = {
            'alergias': 'Listar alergias a medicamentos, alimentos, etc.',
            'enfermedades_cronicas': 'Listar condiciones médicas preexistentes como hipertensión, diabetes, etc.',
        }