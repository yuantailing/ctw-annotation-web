from __future__ import unicode_literals

from django.db import models
from django.contrib.auth import models as auth_models

from character import settings
from collection import filename_mapper
import os

# Create your models here.

User = auth_models.User


class Package(models.Model):
    direction = models.IntegerField(db_index=True, default=None)
    users = models.ManyToManyField(
        User,
        through='UserPackage')
    class Meta:
        ordering = ('direction', 'pk', )
    def __str__(self):
        return 'Package-%d-%04d' % (self.direction, self.id)
    def num_images(self):
        return self.image_set.count()
    def num_users(self):
        return self.users.count()


class UserPackage(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    package = models.ForeignKey(Package, on_delete=models.PROTECT)
    upload = models.FileField(blank=True, upload_to='collection/uploads/userpackage')
    feedback = models.FileField(blank=True, upload_to='collection/feedbacks/userpackage')
    validation = models.TextField(blank=True, default='')
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ("user", "package", )
    def __str__(self):
        return 'UserPackage(%s, %s)' % (self.user.__str__(), self.package.__str__())


class Image(models.Model):
    package = models.ForeignKey(Package, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    direction = models.IntegerField(db_index=True, default=None)
    number = models.CharField(max_length=64, db_index=True)
    class Meta:
        unique_together = ("direction", "number", )
        ordering = ('direction', 'number', )
    def __str__(self):
        return 'Image-%d%s' % (self.direction, self.number)
    def get_file_path(self):
        old_name = filename_mapper.mapper.new2old[self.number]
        file_folder = os.path.join(settings.IMAGE_DATA_ROOT, "%d" % self.direction)
        return os.path.join(file_folder, "%s.%d.jpg" % (old_name, self.direction))
    def get_distribute_name(self):
        return "%d%s" % (self.direction, self.number)
