from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from .models import WaitlistEntry


def home(request):
    if request.method == 'GET':
        context = {
            'spots_taken': 97,
            'spots_total': 100,
        }
        return render(request, 'landing/home.html', context)

    elif request.method == 'POST':
        email = request.POST.get('email')

        if WaitlistEntry.objects.filter(email=email).exists():
            messages.error(request, 'email_exists')
        else:
            WaitlistEntry.objects.create(email=email)
            messages.success(request, 'cadastrado')

        return HttpResponseRedirect(reverse('home') + '#waitlist')


