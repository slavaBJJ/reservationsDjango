from django.urls import path
from .views import UserSignUpView, UserUpdateView
from .import views
from .views import profile

app_name = 'accounts'

urlpatterns = [
    path('signup/', UserSignUpView.as_view(), name='user-signup'),
    path(
        'signup/availability/',
        views.signup_availability,
        name='signup-availability',
    ),
    path('profile/',views.profile, name='user-profile'),
    path('profile/<int:pk>',UserUpdateView.as_view(), name='user-update' ),
    path('profile/delete/<int:pk>/', views.delete, name='user-delete'),
]
