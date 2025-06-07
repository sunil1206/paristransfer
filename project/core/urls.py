from django.contrib import admin
from django.urls import path, include

from core import views

urlpatterns = [
path('', views.index, name='index'),
path('about/', views.about, name='about'),
path('service/', views.service, name='service'),
path('<slug:slug>/', views.blog_post, name='blog_post'),

]