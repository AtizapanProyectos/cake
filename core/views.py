from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import login
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta, time
import json
from django.db import transaction  # <--- Agrega esto en tus imports de hasta arriba
import os
import uuid
from django.contrib.auth.decorators import user_passes_test


# --- LIBRERÍAS DE GOOGLE PARA MEET ---
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from django.conf import settings

from .models import *
from .cuestionario_data import CUESTIONARIO_CLINICO

# =========================================================================
# 🧠 FUNCIÓN MAESTRA: CREAR ENLACE DE GOOGLE MEET
# =========================================================================
# =========================================================================
# 🧠 FUNCIÓN MAESTRA: CREAR ENLACE DE GOOGLE MEET (ACTUALIZADA)
# =========================================================================

# =========================================================================
# 🏠 NUEVA VISTA: PÁGINA DE INICIO (LANDING PAGE)
# =========================================================================
def inicio(request):
    return render(request, 'inicio.html')

def generar_link_meet(fecha_obj, hora_obj, paciente_nombre, psicologo_nombre, paciente_email, psicologo_email):
    SCOPES = ['https://www.googleapis.com/auth/calendar.events']

    token_path = os.path.join(settings.BASE_DIR, 'token.json')

    if not os.path.exists(token_path):
        print("ERROR: No existe token.json.")
        return None

    try:
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        service = build('calendar', 'v3', credentials=creds)

        inicio_datetime = datetime.combine(fecha_obj, hora_obj)
        fin_datetime = inicio_datetime + timedelta(minutes=50)

        start_format = inicio_datetime.isoformat() + '-06:00'
        end_format = fin_datetime.isoformat() + '-06:00'

        event = {
            'summary': f'Sesión HOPE: {paciente_nombre} y Psic. {psicologo_nombre}',
            'description': 'Sesión psicológica online generada desde la plataforma HOPE.',
            'start': {
                'dateTime': start_format,
                'timeZone': 'America/Mexico_City',
            },
            'end': {
                'dateTime': end_format,
                'timeZone': 'America/Mexico_City',
            },
            # 👇 AQUÍ ESTÁ LA MAGIA: LOS AGREGAMOS COMO INVITADOS OFICIALES
            'attendees': [
                {'email': paciente_email},
                {'email': psicologo_email},
            ],
            'conferenceData': {
                'createRequest': {
                    'requestId': f"hope_meet_{uuid.uuid4().hex[:10]}",
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            }
        }

        event_result = service.events().insert(
            calendarId='primary',
            body=event,
            conferenceDataVersion=1,
            sendUpdates='all'  # Opcional: Esto les manda un correo de Google avisando de la cita
        ).execute()

        return event_result.get('hangoutLink')

    except Exception as e:
        print(f"Error generando Meet: {e}")
        return None
# =========================================================================


def modulo_informativo(request):
    context = {
        'cuestionario_json': json.dumps(CUESTIONARIO_CLINICO)
    }
    return render(request, 'informativo.html', context)



@transaction.atomic  # <--- Agrega esto justo arriba de tu función
def registrar_usuario(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        password = request.POST.get('password')
        telefono = request.POST.get('telefono')  # ¡Bien, aquí lo atrapas!
        flujo_elegido = request.POST.get('flujo_elegido', 'individual')
        respuestas_raw = request.POST.get('respuestas_json', '{}')

        try:
            respuestas_dict = json.loads(respuestas_raw)
        except json.JSONDecodeError:
            respuestas_dict = {}

        if User.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'Este correo ya está registrado.'})

        user = User.objects.create_user(
            username=email, email=email, password=password)
        user.first_name = nombre
        user.is_active = False
        user.save()

        # 👇 AQUÍ ESTABA EL DETALLE 👇
        # Faltaba agregar telefono=telefono para que se guarde
        UsuarioPerfil.objects.create(usuario=user, nombre=nombre, telefono=telefono)

        CuestionarioRegistro.objects.create(
            paciente=user,
            flujo_elegido=flujo_elegido,
            respuestas=respuestas_dict,
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        link_activacion = request.build_absolute_uri(
            reverse('activar_cuenta', kwargs={'uidb64': uid, 'token': token})
        )

        asunto = 'Verifica tu cuenta en HOPE - El primer paso a tu bienestar'
        contexto = {'nombre': nombre, 'link_activacion': link_activacion}
        mensaje_html = render_to_string('verificacion_email.html', contexto)
        mensaje_plano = strip_tags(mensaje_html)

        send_mail(
            subject=asunto,
            message=mensaje_plano,
            from_email=None,
            recipient_list=[email],
            html_message=mensaje_html,
            fail_silently=False
        )
        return JsonResponse({'status': 'success', 'message': '¡Registro exitoso! Revisa tu correo para activar tu cuenta.'})

def activar_cuenta(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'verificacion_resultado.html', {'exito': True})
    else:
        return render(request, 'verificacion_resultado.html', {'exito': False})


def login_usuario(request):
    if request.method == 'POST':
        email = request.POST.get('login_email')
        password = request.POST.get('login_password')

        try:
            user = User.objects.get(username=email)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'error_type': 'invalid', 'message': 'El correo o la contraseña son incorrectos.'})

        if not user.check_password(password):
            return JsonResponse({'status': 'error', 'error_type': 'invalid', 'message': 'El correo o la contraseña son incorrectos.'})

        if not user.is_active:
            return JsonResponse({'status': 'error', 'error_type': 'unverified', 'message': 'Aún no verificas tu cuenta. Por favor, revisa tu bandeja de entrada.'})

        login(request, user)

        # =========================================================================
        # 🧠 REDIRECCIÓN INTELIGENTE (¿Es Admin, Doctor o Paciente?)
        # =========================================================================
        if user.is_superuser:
            return JsonResponse({'status': 'success', 'redirect_url': '/panel-admin/'})
        elif hasattr(user, 'perfil_psicologo'):
            return JsonResponse({'status': 'success', 'redirect_url': '/panel-doctor/'})
        else:
            return JsonResponse({'status': 'success', 'redirect_url': '/panel/'})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'})


def panel_generico(request):
    if not request.user.is_authenticated:
        return redirect('modulo_informativo')

    hoy = timezone.now().date()
    hora_actual = timezone.now().time()
    perfil_usuario = request.user.perfil
    psicologo_asignado = perfil_usuario.psicologo_asignado

    cita_proxima = Cita.objects.filter(
        Q(fecha__gt=hoy) | Q(fecha=hoy, hora__gte=hora_actual),
        paciente=request.user,
        estado='Confirmada'
    ).order_by('fecha', 'hora').first()

    festivos = set(DiaFestivo.objects.filter(
        fecha__gte=hoy).values_list('fecha', flat=True))
    horas_base = [time(h, 0) for h in range(9, 19)]
    total_psicologos_activos = PerfilPsicologo.objects.filter(
        esta_activo=True).count()

    dias_json = {}
    dias_html = {}
    dias_agregados = 0
    dia_actual = hoy
    dias_iterados = 0

    while dias_agregados < 365 and dias_iterados < 400:
        dias_iterados += 1
        if dia_actual.weekday() <= 6 and dia_actual not in festivos:
            horas_del_dia_str = []
            horas_del_dia_obj = []

            for h in horas_base:
                if dia_actual == hoy and h <= hora_actual:
                    continue

                if psicologo_asignado:
                    doctor_ocupado = Cita.objects.filter(
                        psicologo=psicologo_asignado, fecha=dia_actual, hora=h, estado='Confirmada').exists()
                    if not doctor_ocupado:
                        horas_del_dia_str.append(h.strftime('%I:%M %p'))
                        horas_del_dia_obj.append(h)
                else:
                    citas_en_esta_hora = Cita.objects.filter(
                        fecha=dia_actual, hora=h, estado='Confirmada').count()
                    if citas_en_esta_hora < total_psicologos_activos:
                        horas_del_dia_str.append(h.strftime('%I:%M %p'))
                        horas_del_dia_obj.append(h)

            if horas_del_dia_str:
                dias_json[dia_actual.strftime('%Y-%m-%d')] = horas_del_dia_str
                dias_html[dia_actual] = horas_del_dia_obj
                dias_agregados += 1

        dia_actual += timedelta(days=1)

    return render(request, 'panel_generico.html', {
        'dias_disponibles_json': dias_json,
        'dias_disponibles': dias_html,
        'cita_proxima': cita_proxima
    })


def guardar_cita_ajax(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Debes iniciar sesión.'})

        fecha_str = request.POST.get('fecha')
        hora_str = request.POST.get('hora')
        animo = request.POST.get('animo', 'No especificó')

        try:
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora_obj = datetime.strptime(hora_str, '%H:%M').time()
            perfil = request.user.perfil

            psicologo = perfil.psicologo_asignado

            if not psicologo:
                preferencia = ""
                try:
                    cuestionario = request.user.cuestionario_inicial
                    preferencia = cuestionario.respuestas.get(
                        'preferencia_terapeuta', '')
                except:
                    pass

                psicologos_ocupados_ids = Cita.objects.filter(
                    fecha=fecha_obj, hora=hora_obj, estado='Confirmada').values_list('psicologo_id', flat=True)
                psicologos_libres = PerfilPsicologo.objects.filter(esta_activo=True).exclude(
                    id__in=psicologos_ocupados_ids).annotate(carga_pacientes=Count('pacientes_asignados'))

                if not psicologos_libres.exists():
                    return JsonResponse({'status': 'error', 'message': 'Lo sentimos, este horario acaba de ser ocupado por alguien más. Por favor elige otro.'})

                if 'Mujer' in preferencia:
                    psicologo = psicologos_libres.filter(
                        genero='Mujer').order_by('carga_pacientes').first()
                elif 'Hombre' in preferencia:
                    psicologo = psicologos_libres.filter(
                        genero='Hombre').order_by('carga_pacientes').first()

                if not psicologo:
                    psicologo = psicologos_libres.order_by(
                        'carga_pacientes').first()

                perfil.psicologo_asignado = psicologo
                perfil.save()

            else:
                if Cita.objects.filter(psicologo=psicologo, fecha=fecha_obj, hora=hora_obj, estado='Confirmada').exists():
                    return JsonResponse({'status': 'error', 'message': 'Lo sentimos, tu terapeuta acaba de ocupar este horario. Elige otro por favor.'})

            # =========================================================================
            # ¡MAGIA EN ACCIÓN! GENERAMOS EL LINK DE MEET ANTES DE GUARDAR LA CITA
            # =========================================================================

            enlace_generado = generar_link_meet(
                fecha_obj=fecha_obj,
                hora_obj=hora_obj,
                paciente_nombre=request.user.first_name,
                psicologo_nombre=psicologo.usuario.first_name,
                paciente_email=request.user.email,             # <--- NUEVO
                psicologo_email=psicologo.usuario.email        # <--- NUEVO
            )

            Cita.objects.create(
                paciente=request.user,
                psicologo=psicologo,
                fecha=fecha_obj,
                hora=hora_obj,
                estado_animo=animo,
                motivo='Primera Sesión' if not perfil.psicologo_asignado else 'Sesión de Seguimiento',
                estado='Confirmada',
                enlace_meet=enlace_generado  # <--- ¡GUARDADO DIRECTO EN LA BASE DE DATOS!
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error'})


# =========================================================================
# 🩺 PANEL DEL DOCTOR (ULTRA LIMPIO)
# =========================================================================
def panel_doctor(request):
    if not request.user.is_authenticated:
        return redirect('modulo_informativo')

    if not hasattr(request.user, 'perfil_psicologo'):
        return redirect('panel_generico')

    psicologo = request.user.perfil_psicologo
    hoy = timezone.now().date()

    citas_hoy = Cita.objects.filter(
        psicologo=psicologo, fecha=hoy, estado='Confirmada').order_by('hora')

    todas_las_citas = Cita.objects.filter(psicologo=psicologo)
    eventos_calendario = []
    for cita in todas_las_citas:
        color = '#297E7E' if cita.fecha >= hoy else '#D1D5DB'
        eventos_calendario.append({
            'title': f"{cita.paciente.first_name} ({cita.hora.strftime('%H:%M')})",
            'start': f"{cita.fecha.isoformat()}T{cita.hora.strftime('%H:%M:%S')}",
            'backgroundColor': color,
            'borderColor': color,
        })

    # Lista de pacientes (Sin cargar todo el historial, para que sea rapidísimo)
    mis_pacientes_db = User.objects.filter(
        perfil__psicologo_asignado=psicologo).distinct()
    pacientes_data = []

    for paciente in mis_pacientes_db:
        total_citas = Cita.objects.filter(
            paciente=paciente, psicologo=psicologo).count()
        pacientes_data.append({
            'usuario': paciente,
            'total_citas': total_citas
        })

    return render(request, 'panel_doctor.html', {
        'psicologo': psicologo,
        'citas_hoy': citas_hoy,
        'eventos_calendario_json': json.dumps(eventos_calendario),
        'pacientes_data': pacientes_data,
        'hoy': hoy
    })

# =========================================================================
# 📂 NUEVA VISTA: EXPEDIENTE COMPLETO DEL PACIENTE
# =========================================================================


def detalle_paciente(request, paciente_id):
    if not request.user.is_authenticated or not hasattr(request.user, 'perfil_psicologo'):
        return redirect('modulo_informativo')

    psicologo = request.user.perfil_psicologo

    try:
        paciente = User.objects.get(id=paciente_id)
    except User.DoesNotExist:
        return redirect('panel_doctor')

    # Seguridad: Solo puede ver pacientes que estén asignados a él
    if getattr(paciente.perfil, 'psicologo_asignado', None) != psicologo:
        return redirect('panel_doctor')

    historiales = HistorialClinico.objects.filter(
        paciente=paciente, psicologo=psicologo).order_by('-fecha_registro')
    total_sesiones = Cita.objects.filter(
        paciente=paciente, psicologo=psicologo).count()

    return render(request, 'detalle_paciente.html', {
        'paciente': paciente,
        'historiales': historiales,
        'total_sesiones': total_sesiones
    })


# =========================================================================
# 📝 GUARDAR HISTORIAL CLÍNICO (NUEVA FUNCIÓN)
# =========================================================================
def guardar_historial_ajax(request):
    if request.method == 'POST':
        cita_id = request.POST.get('cita_id')
        notas = request.POST.get('notas_sesion')
        diagnostico = request.POST.get('diagnostico')
        tareas = request.POST.get('tareas')

        try:
            # Buscamos la cita que le pertenece a este doctor
            cita = Cita.objects.get(
                id=cita_id, psicologo=request.user.perfil_psicologo)

            # Guardamos o actualizamos el expediente de esta sesión
            historial, created = HistorialClinico.objects.get_or_create(
                cita=cita,
                defaults={
                    'paciente': cita.paciente,
                    'psicologo': request.user.perfil_psicologo,
                    'notas_sesion': notas,
                    'diagnostico_temporal': diagnostico,
                    'tareas_asignadas': tareas
                }
            )

            # Si ya existía, lo actualizamos
            if not created:
                historial.notas_sesion = notas
                historial.diagnostico_temporal = diagnostico
                historial.tareas_asignadas = tareas
                historial.save()

            # Opcional: Cambiamos la cita a "Completada" para que ya no estorbe
            cita.estado = 'Completada'
            cita.save()

            return JsonResponse({'status': 'success', 'message': 'Expediente clínico guardado con éxito.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error'})




# =========================================================================
# 👑 CENTRO DE COMANDO (PANEL DE SUPER ADMIN / CEO)
# =========================================================================
def es_admin(user):
    return user.is_superuser

@user_passes_test(es_admin, login_url='/')
def panel_admin(request):
    hoy = timezone.now().date()
    
    # 1. Estadísticas Generales (Clínicas)
    total_pacientes = UsuarioPerfil.objects.filter(es_psicologo=False).count()
    total_doctores = PerfilPsicologo.objects.filter(esta_activo=True).count()
    citas_hoy = Cita.objects.filter(fecha=hoy).count()
    citas_totales = Cita.objects.filter(estado='Completada').count()

    # 2. Rendimiento por Doctor (Carga y Eficacia)
    doctores_data = []
    doctores = PerfilPsicologo.objects.all()
    for doc in doctores:
        pacientes_activos = doc.pacientes_asignados.count()
        citas_doc_hoy = Cita.objects.filter(psicologo=doc, fecha=hoy).count()
        citas_doc_total = Cita.objects.filter(psicologo=doc, estado='Completada').count()
        
        # Analizador de Carga de Trabajo
        estado_carga = "Óptima"
        color_carga = "#10b981" # Verde
        if pacientes_activos > 15: 
            estado_carga = "Alta"
            color_carga = "#f59e0b" # Naranja
        elif pacientes_activos == 0: 
            estado_carga = "Sin pacientes"
            color_carga = "#94a3b8" # Gris

        doctores_data.append({
            'nombre': doc.usuario.first_name,
            'especialidad': doc.especialidad or 'Terapia General',
            'pacientes': pacientes_activos,
            'citas_hoy': citas_doc_hoy,
            'citas_historicas': citas_doc_total,
            'carga': estado_carga,
            'color_carga': color_carga
        })

    # 3. Listado de Pacientes y su Seguimiento
    pacientes_recientes = UsuarioPerfil.objects.filter(es_psicologo=False).order_by('-id')[:12]
    pacientes_data = []
    for pac in pacientes_recientes:
        total_sesiones = Cita.objects.filter(paciente=pac.usuario, estado='Completada').count()
        doctor_nombre = pac.psicologo_asignado.usuario.first_name if pac.psicologo_asignado else 'Sin asignar'
        
        # Inteligencia: Determinar la fase del tratamiento
        fase = "Inicial"
        color_fase = "#38bdf8"
        if total_sesiones > 5: 
            fase = "Desarrollo"
            color_fase = "#a855f7"
        if total_sesiones > 15: 
            fase = "Mantenimiento"
            color_fase = "#10b981"
        if not pac.psicologo_asignado: 
            fase = "En espera"
            color_fase = "#f43f5e"

        pacientes_data.append({
            'nombre': pac.nombre,
            'email': pac.usuario.email,
            'doctor': doctor_nombre,
            'sesiones': total_sesiones,
            'fase': fase,
            'color_fase': color_fase
        })

    context = {
        'total_pacientes': total_pacientes,
        'total_doctores': total_doctores,
        'citas_hoy': citas_hoy,
        'citas_totales': citas_totales,
        'doctores': doctores_data,
        'pacientes': pacientes_data,
        'hoy': hoy
    }
    return render(request, 'panel_admin.html', context)