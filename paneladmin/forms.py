from django import forms
from .models import Especialidad
from usuario.models import Usuario

class EspecialidadForm(forms.ModelForm):
    class Meta:
        model = Especialidad
        fields = ['nombre', 'descripcion', 'imagen']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs.update({'class': 'form-control-especialidad'})
        self.fields['descripcion'].widget.attrs.update({'class': 'form-control-especialidad'})


class AdminUsuarioEditForm(forms.ModelForm):
    """Formulario para que un admin edite un usuario."""
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'email', 'rut', 'telefono', 'role', 'especialidad', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicar clases de Bootstrap a los campos
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})