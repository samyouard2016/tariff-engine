from __future__ import unicode_literals

from django.db import models

# Create your models here.

class Production (models.Model):
    prod_name = models.CharField(max_length=500)
    prod_id = models.CharField(max_length=500)
    prod_data = models.FileField()

class LoadProfile(models.Model):
    load_name = models.CharField(max_length=500)
    load_id = models.CharField(max_length=500)
    load_data = models.FileField()

class utilities_id (models.Model):
    utility_name = models.CharField(max_length=500)
    utility_id = models.CharField(max_length=500)