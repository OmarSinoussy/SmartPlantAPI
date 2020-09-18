"""CapstoneServer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
import smart_plant_api.views as smart_api_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', smart_api_views.welcome_view),
    path('AddEntry', smart_api_views.add_entry),
    path('StatisticalData', smart_api_views.statistical_data),
    path('RemoveEntries', smart_api_views.remove_entries),
    path('ActuatorData', smart_api_views.actuator_data),
    path('AppBasicData', smart_api_views.app_basic_data),
    path('Override', smart_api_views.Override),
    path('RemoveOverride', smart_api_views.RemoveOverride),
    path('BindPlantIdToken', smart_api_views.bindPlantIdToken),
]