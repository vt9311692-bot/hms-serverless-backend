from django.contrib import admin
from django.urls import path
from hospital import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/', views.signup, name='signup'),
    path('slots/create/', views.create_slot, name='create_slot'),
    path('slots/available/', views.list_available_slots, name='available_slots'),
    path('slots/<int:slot_id>/book/', views.book_slot, name='book_slot'),
]
