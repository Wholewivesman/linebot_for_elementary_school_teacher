from django.contrib import admin

# Register your models here.

from linebot1.models import *

class User_Info_Admin(admin.ModelAdmin):
    list_display = ('uid', 'name', 'points', 'now_state')
admin.site.register(User_Info,User_Info_Admin)

class superuser_Admin(admin.ModelAdmin):
    list_display = ('uid', 'name')
admin.site.register(superuser,superuser_Admin)

class Tests_Admin(admin.ModelAdmin):
    list_display = ('qid', 'show_type', 'question', 'opA', 'opB', 'opC', 'opD', 'opE', 'ans')
admin.site.register(Tests,Tests_Admin)

class User_ans_Admin(admin.ModelAdmin):
    list_display = ('uid', 'qid', 'user_ans')
admin.site.register(User_ans,User_ans_Admin)

class ranking_Admin(admin.ModelAdmin):
    list_display = ('rank', 'uid', 'name', 'points')
admin.site.register(ranking,ranking_Admin)



# class superuser(models.Model):
#     uid = models.CharField(max_length=50,null=False,primary_key=True)
#     name = models.CharField(max_length=255,null=False,blank=True)
#     def __str__(self):
#         return self.uid