from django.db import models
from django.contrib.postgres.fields import ArrayField

class MovieMetadata(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.TextField(null=True, blank=True)
    poster_path = models.TextField(null=True, blank=True)
    release_year = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "movie_metadata"
        managed = False

class MasterTable(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.TextField(null=True, blank=True)
    poster_path = models.TextField(null=True, blank=True)
    revenue = models.BigIntegerField(null=True, blank=True)
    budget = models.IntegerField(null=True, blank=True)
    release_year = models.IntegerField(null=True, blank=True)
    genres_list = ArrayField(models.TextField(), null=True, blank=True)

    class Meta:
        db_table = "master_table"
        managed = False

