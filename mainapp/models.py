from django.db import models

class champion_index(models.Model):
    en = models.CharField(max_length=32)
    kr = models.CharField(max_length=32)
