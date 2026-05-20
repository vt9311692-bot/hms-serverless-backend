from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AvailabilitySlot, Booking

# Registering the Custom User model so it shows up in the admin panel
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')

admin.site.register(User, CustomUserAdmin)
admin.site.register(AvailabilitySlot)
admin.site.register(Booking)
