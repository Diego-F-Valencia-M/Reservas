from django.shortcuts import render, redirect
from .models import Services, Booking
from django import forms
from datetime import datetime, timedelta, time, date  # ✅ Import correcto
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages

# ✅ Formulario para crear/validar reservas
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['service', 'custumer_name', 'custumer_phone', 'custumer_email', 'date', 'time']
        labels = {
            'service': 'Servicio solicitado *',
            'custumer_name': 'Nombre y Apellido *',
            'custumer_phone': 'Número Celular *',
            'custumer_email': 'Correo Electrónico',
            'date': 'Fecha de la reserva *',
            'time': 'Hora de la reserva *',
        }
        widgets = {
            'service': forms.Select(attrs={'class': 'form-control'}),
            'custumer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'custumer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'custumer_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.Select(attrs={'class': 'form-control'}),  # Ahora select dinámico
        }

    def clean(self):
        cleaned_data = super().clean()
        selected_date = cleaned_data.get("date")
        selected_time = cleaned_data.get("time")
        selected_service = cleaned_data.get("service")

        # Si falta algún dato, no seguimos validando
        if not selected_date or not selected_time or not selected_service:
            return cleaned_data

        # ✅ Validar fechas pasadas
        today = date.today()  # ✅ Usamos date.today()
        if selected_date and selected_date < today:
            self.add_error("date", "⚠️ No puedes reservar en una fecha pasada")
        
        # ✅ Horarios de apertura y cierre
        opening_time = time(8, 0)   # 08:00 Apertura
        last_start_time = time(18, 0)  # 18:00 Último turno de servicio
        closing_time = time(19, 0)     # 19:00 cierre del local

        # ✅ Si la hora está fuera del rango permitido
        if selected_time < opening_time or selected_time > last_start_time:
            self.add_error(
                "time",
                f"⚠️ Solo se pueden reservar turnos entre {opening_time.strftime('%H:%M')} y {closing_time.strftime('%H:%M')} horas"
            )

        # ✅ Calcular intervalo solicitado
        requested_start = datetime.combine(selected_date, selected_time)  # ✅ Sin datetime.datetime
        requested_end = requested_start + timedelta(minutes=selected_service.duration_minutes)  # ✅ timedelta directo

        # ✅ Buscar reservas existentes para ese día
        existing_bookings = Booking.objects.filter(date=selected_date, service = selected_service)

        for booking in existing_bookings:
            existing_start = datetime.combine(booking.date, booking.time)
            existing_end = datetime.combine(booking.date, booking.end_time)

            # ✅ Si hay solapamiento (se cruzan horarios)
            if (requested_start < existing_end) and (requested_end > existing_start):
                self.add_error(
                    "time",
                    f"⚠️ Ya existe una reserva en este horario ({booking.time} - {booking.end_time}). Selecciona otra hora."
                )
                break

        return cleaned_data

@login_required
def cancel_booking(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        booking.delete()
        messages.success(request, f"✅ La reserva de {booking.custumer_name} para {booking.service.name} fue cancelada.")
    except booking.DoesNotExist:
        messages.error(request, "⚠️ La reserva no existe o ya fue cancelada.")

    return redirect('booking_list')

@login_required
def booking_list(request):
    today = date.today()              # ✅ Fecha de hoy
    now = datetime.now().time()       # ✅ Hora actual

    # ✅ Reservas del día que aún no han pasado
    todays_bookings = Booking.objects.filter(
        date=today,
        time__gte=now
    ).order_by('time')

    # ✅ Reservas futuras
    future_bookings = Booking.objects.filter(
        date__gt=today
    ).order_by('date', 'time')

    return render(request, 'booking/booking_list.html', {
        'todays_bookings': todays_bookings,
        'future_bookings': future_bookings
    })


def booking_view(request):
    services = Services.objects.all()
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            try:
                # ✅ Guardamos temporalmente sin commit
                booking = form.save(commit=False)

                # ✅ Calculamos el datetime inicial (fecha + hora)
                start_datetime = datetime.combine(
                    booking.date,
                    booking.time
                )

                # ✅ Sumamos la duración del servicio en minutos
                booking_end = start_datetime + timedelta(
                    minutes=booking.service.duration_minutes
                )

                # ✅ Guardamos solo la hora final
                booking.end_time = booking_end.time()
                booking.save()

                # ✅ Guardamos definitivamente la reserva
                booking.save()

                return render(request, 'booking/confirmation.html', {'booking': booking})

            except IntegrityError:
                form.add_error(
                    'time',
                    "⚠️ Esta hora ya fue reservada por otra persona. Intenta con otro horario."
                )
    
        # ✅ Si hay errores, recargamos el formulario
        return render(request, 'booking/booking_form.html', {'form': form, 'services': services})
    else:
        form = BookingForm()

    return render(request, 'booking/booking_form.html', {'form': form, 'services': services})


def get_available_times(request):
    date_str = request.GET.get('date')
    service_id = request.GET.get('service')

    if not date_str or not service_id:
        return JsonResponse({'error': "Faltan parámetros"}, status=400)
    
    selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    try:
        service = Services.objects.get(id=service_id)
    except Services.DoesNotExist:
        return JsonResponse({'error': "Servicio no encontrado"}, status=404)

    apertura = 8
    cierre = 18
    possible_slots = [time(h, 0) for h in range(apertura, cierre + 1)]

    #si es hoy eliminar las horas ya pasadas
    now = datetime.now()
    if selected_date == now.date():
        possible_slots = [slot for slot in possible_slots if slot > now.time()]

    # reservas existentes para esta fecha
    reservas = Booking.objects.filter(date=selected_date, service = service)

    free_slots = []
    for slot in possible_slots:
        slot_inicio = datetime.combine(selected_date, slot)
        slot_fin = slot_inicio + timedelta(minutes=service.duration_minutes)

        ocupado = False
        for r in reservas:
            res_inicio = datetime.combine(r.date, r.time)
            res_fin = datetime.combine(r.date, r.end_time)

            if (slot_inicio < res_fin) and (slot_fin > res_inicio):
                ocupado = True
                break

        if not ocupado:
            free_slots.append(slot.strftime("%H:%M"))

    
    return JsonResponse({'available_times': free_slots})