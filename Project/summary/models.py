from django.db import models
from django.contrib.auth.models import User

class Summary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='pdfs/')

    def __str__(self):
        return f"Summary of {self.filename} by {self.user.username}"
