from django.db import models


class WaitlistEntry(models.Model):
    email = models.EmailField(unique=True, verbose_name='Email')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Cadastrado em')

    class Meta:
        verbose_name = 'Registro Waitlist'
        verbose_name_plural = 'Registros Waitlist'
        ordering = ['-created_at']

    def __str__(self):
        return self.email
