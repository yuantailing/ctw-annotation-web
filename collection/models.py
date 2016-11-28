from __future__ import unicode_literals

from django.db import models
from django.contrib.auth import models as auth_models
import accounts.models

# Create your models here.

User = auth_models.User


class Package(models.Model):
    direction = models.IntegerField(db_index=True, default=None)
    users = models.ManyToManyField(
        User,
        through='UserPackage')
    def __str__(self):
        return 'Package-%d-%05d' % (self.direction, self.id)
    def num_images(self):
        return self.image_set.count()
    def num_users(self):
        return self.users.count()


class UserPackage(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    package = models.ForeignKey(Package, on_delete=models.PROTECT)
    upload = models.FileField(null=True, blank=True, upload_to='uploads/user_package')
    feedback = models.FileField(null=True, blank=True, upload_to='feedbacks/user_package')
    validation = models.TextField(blank=True, default='')
    class Meta:
        unique_together = ("user", "package")
    def __str__(self):
        return 'UserPackage(%s, %s)' % (self.user.__str__(), self.package.__str__())


class Image(models.Model):
    package = models.ForeignKey(Package, null=True, blank=True, on_delete=models.SET_NULL)
    direction = models.IntegerField(db_index=True, default=None)
    number = models.CharField(max_length=64, db_index=True)
    class Meta:
        unique_together = ("direction", "number")
    def __str__(self):
        return 'Image %d%s' % (self.direction, self.number)
