from django.contrib import admin

# Register your models here.
from .models import User, Package, UserPackage, Image


class PackageAdmin(admin.ModelAdmin):
    class ImageInline(admin.TabularInline):
        model = Image
        extra = 1
    class UserPackageInline(admin.TabularInline):
        model = UserPackage
        extra = 1
    inlines = (ImageInline, UserPackageInline)
    list_display = ('id', '__str__', 'direction', 'num_images', 'num_users', )
    list_filter = ('direction', )


class UserPackageAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'package', 'annotation_uploaded', 'create_time', 'update_time', )
    list_filter = ('user', 'package', )


class ImageAdmin(admin.ModelAdmin):
    fieldsets = ((None, {
            'fields': ('package', 'direction', 'number', )
        }),
    )
    list_display = ('id', '__str__', 'package', 'direction', 'number', )
    list_filter = ('direction', 'package', )


admin.site.register(Package, PackageAdmin)
admin.site.register(UserPackage, UserPackageAdmin)
admin.site.register(Image, ImageAdmin)
