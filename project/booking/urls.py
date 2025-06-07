from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from booking import views


urlpatterns = [
    path('predict/', views.predict_price, name='predict_price'),
    path('booking/', views.predict_price_and_book, name='booking'),
]
