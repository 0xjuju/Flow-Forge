from django.db import models


class Chain(models.Model):
    name = models.CharField(max_length=255, default="")
