from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='recipes.index'),
    path('<int:id>/', views.show, name='recipes.show'),
]