# admin.py
from django.contrib import admin
from .models import Summary

@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'pdf_file')
    search_fields = ('user__username',)
