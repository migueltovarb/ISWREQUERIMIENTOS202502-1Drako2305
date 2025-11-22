from django import forms
from django.conf import settings
from .models import Reclamo, Comentario, ArchivoReclamo
import magic

class ArchivoReclamoForm(forms.ModelForm):
    class Meta:
        model = ArchivoReclamo
        fields = ['archivo']
        widgets = {
            'archivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            })
        }

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            # Verificar tamaño
            if archivo.size > settings.MAX_UPLOAD_SIZE:
                raise forms.ValidationError(
                    'El archivo es demasiado grande. El tamaño máximo permitido es 5MB.'
                )

            # Verificar tipo de archivo
            mime = magic.from_buffer(archivo.read(1024), mime=True)
            archivo.seek(0)  # Resetear el puntero del archivo
            
            if mime not in settings.ALLOWED_FILE_TYPES:
                raise forms.ValidationError(
                    'Tipo de archivo no permitido. Solo se permiten archivos PDF, JPG y PNG.'
                )

        return archivo

class ReclamoForm(forms.ModelForm):
    class Meta:
        model = Reclamo
        fields = ['titulo', 'descripcion', 'categoria', 'prioridad']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese un título descriptivo'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describa detalladamente su reclamo'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'prioridad': forms.Select(attrs={
                'class': 'form-select'
            })
        }

class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['contenido']
        widgets = {
            'contenido': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Escriba su comentario aquí'
            })
        } 