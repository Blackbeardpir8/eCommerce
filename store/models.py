from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

# Create your models here.

# Category Model
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='category_images/',null=True,blank=True)
    slug = models.SlugField(max_length=255,unique=True, blank=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)