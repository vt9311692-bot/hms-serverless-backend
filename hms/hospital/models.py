from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def is_doctor(self):
        return self.role == 'doctor'

    def is_patient(self):
        return self.role == 'patient'

class AvailabilitySlot(models.Model):
    doctor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='availability_slots',
        limit_choices_to={'role': 'doctor'}
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.doctor.username}: {self.start_time} - {self.end_time}"

class Booking(models.Model):
    patient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='bookings',
        limit_choices_to={'role': 'patient'}
    )
    slot = models.OneToOneField(
        AvailabilitySlot, 
        on_delete=models.CASCADE, 
        related_name='booking'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking for {self.patient.username} at {self.slot.start_time}"
