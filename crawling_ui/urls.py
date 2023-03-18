"""crawling URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('runspider', views.runspider, name='runspider'),
    path('mark_as_read', views.mark_as_read, name='mark_as_read'),
    path('delete_job', views.delete_job, name='delete_job'),
    path('signup', views.signup, name='signup'),
    path('signin', views.signin, name='signin'),
    path('logout', views.logout_view, name='logout'),
    path('home', views.home, name='home'),
    path('new_job', views.new_job, name='new_job'),
    path('new_contact', views.new_contact, name='new_contact'),
    path('pricing', views.pricing, name='pricing'),
    path('contact', views.contact, name='contact'),
    path('about', views.about, name='about'),
    path('subscription', views.subscription, name='subscription'),
    # path('dumy', views.dumy, name='dumy'),
    path('thanks/', views.thanks, name='thanks'),
    path('query', views.query, name='query'),
    path('quick', views.quick, name='quick'),
    path('dashboard', views.dashboard, name='dashboard'),
    # path('checkout/', views.checkout, name='checkout')
]
