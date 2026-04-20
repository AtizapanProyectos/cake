from django.db import models
from django.contrib.auth.models import User

# ==========================================
# 1. PERFIL DEL PSICÓLOGO (DOCTORES)
# ==========================================
class PerfilPsicologo(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_psicologo')
    cedula_profesional = models.CharField(max_length=50, unique=True, verbose_name="Cédula Profesional")
    genero = models.CharField(max_length=20, choices=[('Hombre', 'Hombre'), ('Mujer', 'Mujer')], verbose_name="Género")
    especialidad = models.CharField(max_length=150, blank=True, null=True, verbose_name="Especialidad (Ej. Terapia Cognitiva)")
    esta_activo = models.BooleanField(default=True, verbose_name="Aceptando nuevos pacientes")
    
    # Aquí puedes agregar horarios, tarifa, foto de perfil, etc.

    def __str__(self):
        return f"Psicólogo/a: {self.usuario.first_name} ({self.genero})"


# ==========================================
# 2. PERFIL DEL PACIENTE (USUARIO GENERAL)
# ==========================================
class UsuarioPerfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil', null=True, blank=True)
    nombre = models.CharField(max_length=100)
    es_psicologo = models.BooleanField(default=False)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    # ¡LA CONEXIÓN DE POR VIDA! 
    # Aquí guardamos a qué psicólogo fue asignado tras su registro/primera cita
    psicologo_asignado = models.ForeignKey(
        PerfilPsicologo, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='pacientes_asignados',
        verbose_name="Psicólogo Asignado"
    )

    def __str__(self):
        return self.nombre


# ==========================================
# 3. CITAS (AHORA LIGADAS AL DOCTOR)
# ==========================================
class Cita(models.Model):
    paciente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='citas_como_paciente')
    # Añadimos al psicólogo a la cita
    psicologo = models.ForeignKey(PerfilPsicologo, on_delete=models.CASCADE, related_name='citas_agendadas', null=True)
    
    fecha = models.DateField(verbose_name='Fecha de la sesión')
    hora = models.TimeField(verbose_name='Hora de la sesión')
    motivo = models.CharField(max_length=150, verbose_name='Motivo de consulta', default='Primera sesión')
    estado_animo = models.CharField(max_length=50, blank=True, null=True, verbose_name='Estado de ánimo')
    estado = models.CharField(max_length=50, default='Confirmada', choices=[
        ('Pendiente', 'Pendiente'),
        ('Confirmada', 'Confirmada'),
        ('Completada', 'Completada'),
        ('Cancelada', 'Cancelada'),
    ])
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    enlace_meet = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Cita: {self.paciente.first_name} con {self.psicologo.usuario.first_name} el {self.fecha.strftime('%d/%m')} a las {self.hora.strftime('%H:%M')}"


# ==========================================
# 4. HISTORIAL CLÍNICO (EXPEDIENTE)
# ==========================================
class HistorialClinico(models.Model):
    paciente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='historiales_clinicos')
    psicologo = models.ForeignKey(PerfilPsicologo, on_delete=models.SET_NULL, null=True, related_name='notas_creadas')
    cita = models.OneToOneField(Cita, on_delete=models.SET_NULL, null=True, blank=True, related_name='nota_clinica', verbose_name="Cita Relacionada")
    
    # Datos clínicos
    notas_sesion = models.TextField(verbose_name="Notas privadas del psicólogo")
    diagnostico_temporal = models.CharField(max_length=250, blank=True, null=True)
    tareas_asignadas = models.TextField(blank=True, null=True, verbose_name="Tareas para el paciente")
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Expediente de {self.paciente.first_name} - {self.fecha_registro.strftime('%d/%m/%Y')}"


# ==========================================
# 5. CUESTIONARIO Y EXTRAS
# ==========================================
class CuestionarioRegistro(models.Model):
    paciente = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cuestionario_inicial')
    flujo_elegido = models.CharField(max_length=50, verbose_name="Tipo de Terapia (Individual, Pareja, Menor)")
    respuestas = models.JSONField(verbose_name="Respuestas del Cuestionario", default=dict)
    fecha_completado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cuestionario Previo - {self.paciente.email} ({self.flujo_elegido})"

class DiaFestivo(models.Model):
    fecha = models.DateField(unique=True, verbose_name="Día bloqueado")
    motivo = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return f"{self.fecha.strftime('%d/%m/%Y')} - {self.motivo}"