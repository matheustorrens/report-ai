from django.shortcuts import render


def home(request):
    return render(request, 'landing/home.html')


def privacy_policy(request):
    """Privacy Policy page."""
    return render(request, 'landing/privacy_policy.html')


def terms_of_service(request):
    """Terms of Service page."""
    return render(request, 'landing/terms_of_service.html')


def dpa(request):
    """Página pública do Acuerdo de Encargo de Tratamiento (DPA)."""
    return render(request, 'landing/dpa.html')
