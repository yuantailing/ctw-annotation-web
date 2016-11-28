from django.contrib import admin

# Register your models here.
from .models import User, Package, UserPackage, Image


class PackageAdmin(admin.ModelAdmin):
    class UserPackageInline(admin.TabularInline):
        model = UserPackage
        extra = 1
    class ImageInline(admin.TabularInline):
        model = Image
        extra = 1
    inlines = (ImageInline, UserPackageInline)
    list_display = ('id', '__str__', 'direction', 'num_images', 'num_users')
    list_filter = ('direction', )


class ImageAdmin(admin.ModelAdmin):
    fieldsets = ((None, {
            'fields': ('package', 'direction', 'number', )
        }),
    )
    list_display = ('id', '__str__', 'package', 'direction', 'number', )
    list_filter = ('direction', 'package', )


admin.site.register(Package, PackageAdmin)
admin.site.register(UserPackage)
admin.site.register(Image, ImageAdmin)
