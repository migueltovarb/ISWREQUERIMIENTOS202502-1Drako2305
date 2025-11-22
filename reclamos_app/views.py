from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from django.conf import settings
from .models import Reclamo, Comentario, Notificacion, ArchivoReclamo
from .forms import ReclamoForm, ComentarioForm, ArchivoReclamoForm
import uuid
import magic
import os

# Create your views here.

@login_required
def inicio(request):
    if request.user.is_staff:
        # Vista de administrador con estadísticas
        reclamos_totales = Reclamo.objects.filter(cliente=request.user).count()
        reclamos_resueltos = Reclamo.objects.filter(cliente=request.user, estado='RESUELTO').count()
        reclamos_en_progreso = Reclamo.objects.filter(cliente=request.user, estado='EN_PROGRESO').count()
        reclamos_pendientes = Reclamo.objects.filter(cliente=request.user, estado='PENDIENTE').count()
        
        # Reclamos recientes
        reclamos_recientes = Reclamo.objects.filter(cliente=request.user).order_by('-fecha_creacion')[:5]
        
        # Notificaciones no leídas
        notificaciones = Notificacion.objects.filter(
            usuario=request.user,
            leida=False
        ).order_by('-fecha')[:5]

        context = {
            'reclamos_totales': reclamos_totales,
            'reclamos_resueltos': reclamos_resueltos,
            'reclamos_en_progreso': reclamos_en_progreso,
            'reclamos_pendientes': reclamos_pendientes,
            'reclamos_recientes': reclamos_recientes,
            'notificaciones': notificaciones,
        }
        return render(request, 'reclamos/inicio_admin.html', context)
    else:
        # Vista de usuario normal
        reclamos_recientes = Reclamo.objects.filter(cliente=request.user).order_by('-fecha_creacion')[:5]
        return render(request, 'reclamos/inicio_usuario.html', {'reclamos_recientes': reclamos_recientes})

@login_required
def lista_reclamos(request):
    reclamos = Reclamo.objects.filter(cliente=request.user)
    return render(request, 'reclamos/lista_reclamos.html', {'reclamos': reclamos})

@login_required
def crear_reclamo(request):
    if request.method == 'POST':
        form = ReclamoForm(request.POST)
        if form.is_valid():
            reclamo = form.save(commit=False)
            reclamo.cliente = request.user
            reclamo.save()
            
            # Procesar archivos adjuntos
            archivos = request.FILES.getlist('archivos[]')
            for archivo in archivos:
                # Verificar tamaño
                if archivo.size > settings.MAX_UPLOAD_SIZE:
                    messages.error(
                        request,
                        f'El archivo {archivo.name} es demasiado grande. Máximo 5MB.'
                    )
                    continue

                # Verificar tipo de archivo
                mime = magic.from_buffer(archivo.read(1024), mime=True)
                archivo.seek(0)  # Resetear el puntero del archivo
                
                if mime not in settings.ALLOWED_FILE_TYPES:
                    messages.error(
                        request,
                        f'El archivo {archivo.name} no es un tipo permitido. Solo PDF, JPG y PNG.'
                    )
                    continue

                # Guardar archivo
                archivo_reclamo = ArchivoReclamo(
                    reclamo=reclamo,
                    archivo=archivo,
                    nombre_original=archivo.name,
                    tipo_archivo=mime
                )
                archivo_reclamo.save()
            
            # Crear notificación
            Notificacion.objects.create(
                usuario=request.user,
                tipo='ACTUALIZACION',
                mensaje=f'Tu reclamo {reclamo.numero_referencia} ha sido creado exitosamente.',
                reclamo=reclamo
            )
            
            messages.success(request, 'Reclamo creado exitosamente.')
            return redirect('reclamos:detalle_reclamo', pk=reclamo.pk)
    else:
        form = ReclamoForm()
    return render(request, 'reclamos/crear_reclamo.html', {'form': form})

@login_required
def detalle_reclamo(request, pk):
    reclamo = get_object_or_404(Reclamo, pk=pk, cliente=request.user)
    comentarios = reclamo.comentarios.all()
    
    if request.method == 'POST':
        form_comentario = ComentarioForm(request.POST)
        if form_comentario.is_valid():
            comentario = form_comentario.save(commit=False)
            comentario.reclamo = reclamo
            comentario.autor = request.user
            comentario.save()
            
            # Crear notificación
            Notificacion.objects.create(
                usuario=request.user,
                tipo='RESPUESTA',
                mensaje=f'Has recibido una respuesta en tu reclamo {reclamo.numero_referencia}.',
                reclamo=reclamo
            )
            
            messages.success(request, 'Comentario agregado exitosamente.')
            return redirect('reclamos:detalle_reclamo', pk=pk)
    else:
        form_comentario = ComentarioForm()
    
    return render(request, 'reclamos/detalle_reclamo.html', {
        'reclamo': reclamo,
        'comentarios': comentarios,
        'form_comentario': form_comentario
    })

@login_required
def marcar_notificacion_leida(request, pk):
    notificacion = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    notificacion.leida = True
    notificacion.save()
    return redirect('reclamos:inicio')

@login_required
def editar_reclamo(request, pk):
    reclamo = get_object_or_404(Reclamo, pk=pk, cliente=request.user)
    
    if request.method == 'POST':
        form = ReclamoForm(request.POST, instance=reclamo)
        if form.is_valid():
            reclamo = form.save()
            
            # Crear notificación
            Notificacion.objects.create(
                usuario=request.user,
                tipo='ACTUALIZACION',
                mensaje=f'Tu reclamo {reclamo.numero_referencia} ha sido actualizado.',
                reclamo=reclamo
            )
            
            messages.success(request, 'Reclamo actualizado exitosamente.')
            return redirect('reclamos:detalle_reclamo', pk=reclamo.pk)
    else:
        form = ReclamoForm(instance=reclamo)
    
    return render(request, 'reclamos/editar_reclamo.html', {
        'form': form,
        'reclamo': reclamo
    })

@login_required
def eliminar_reclamo(request, pk):
    reclamo = get_object_or_404(Reclamo, pk=pk, cliente=request.user)
    
    if request.method == 'POST':
        numero_referencia = reclamo.numero_referencia
        reclamo.delete()
        messages.success(request, f'El reclamo {numero_referencia} ha sido eliminado.')
        return redirect('reclamos:lista_reclamos')
    
    return render(request, 'reclamos/eliminar_reclamo.html', {'reclamo': reclamo})
