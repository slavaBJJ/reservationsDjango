from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserSignUpForm
from .forms import UserUpdateForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.mail import send_mail
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
from django.conf import settings


@require_GET
def signup_availability(request):
    field = request.GET.get('field', '')
    value = request.GET.get('value', '').strip()

    if field not in {'username', 'email'}:
        return JsonResponse(
            {'available': False, 'message': 'Champ de vérification invalide.'},
            status=400,
        )
    if not value:
        return JsonResponse(
            {'available': False, 'message': 'Ce champ est obligatoire.'},
        )

    if field == 'email':
        try:
            validate_email(value)
        except ValidationError:
            return JsonResponse(
                {'available': False, 'message': 'Saisissez une adresse e-mail valide.'},
            )
        exists = User.objects.filter(email__iexact=value).exists()
        label = "L’adresse e-mail"
    else:
        if len(value) > 30:
            return JsonResponse(
                {'available': False, 'message': 'Le login ne peut pas dépasser 30 caractères.'},
            )
        exists = User.objects.filter(username__iexact=value).exists()
        label = 'Le login'

    return JsonResponse({
        'available': not exists,
        'message': f'{label} est déjà utilisé.' if exists else f'{label} est disponible.',
    })

class UserSignUpView(UserPassesTestMixin, CreateView):
    form_class = UserSignUpForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        send_mail(
            subject='Bienvenue sur Scène ouverte',
            message=render_to_string(
                'registration/signup_confirmation_email.txt',
                {'user': self.object},
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.object.email],
        )
        messages.success(
            self.request,
            'Votre compte a été créé. La confirmation a été affichée dans le terminal.',
        )
        return response

    def test_func(self):
        return self.request.user.is_anonymous or self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "Vous êtes déjà inscrit!")
        return redirect('home')

class UserUpdateView(UserPassesTestMixin, UpdateView):
        model = User
        form_class = UserUpdateForm
        success_url = reverse_lazy("accounts:user-profile")
        template_name = "user/update.html"
        def test_func(self):
            pkInURL = self.kwargs['pk']
            return self.request.user.is_authenticated and self.request.user.id==pkInURL or self.request.user.is_superuser

        def handle_no_permission(self):
            messages.error(self.request, "Vous n'avez pas l'autorisation d'accéder à cette page!")
            return redirect('accounts:user-profile')


@login_required
def profile(request):
    languages = {
        "fr":"Francais",
        "en":"English",
        "nl":"Neederlands"
    }
    return render(request,'user/profile.html',{"user_language":languages[request.user.usermeta.langue],})

@login_required
def delete(request, pk):
    if request.method == 'POST':
        method = request.POST.get('_method','').upper()

        if method == 'DELETE':
            if request.user and request.user.id==pk:
                user = User.objects.get(id=request.user.id)
                user.delete()
                messages.success(request, "Utilisateur supprimé avec succès.")
                logout(request)
            else:
                messages.error(request,"Suppression d'un autre compte interdite!")
            return redirect('home')
        messages.error(request, "Suppression interdite (méthode incorrecte)!")
        return redirect('home')
