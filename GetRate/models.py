from __future__ import unicode_literals
from django.db import models
from django.core.urlresolvers import reverse


class utilities_id (models.Model):
    utility_name = models.CharField(max_length=500)
    utility_id = models.CharField(max_length=500)

    def __unicode__(self):
        return self.utility_name

