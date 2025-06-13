from django .urls import path
from . import views
from .views import RegisterView

urlpatterns = [
    path('',views.index, name= 'index'),
    path('api/auth/register/', RegisterView.as_view(), name="register"),

]

