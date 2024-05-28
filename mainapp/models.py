from django.db import models

class champion_index(models.Model):
    EN = models.CharField(max_length=32)
    KR = models.CharField(max_length=32)