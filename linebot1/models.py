from django.db import models

# Create your models here.

from datetime import date, timedelta
yesterday = date.today() - timedelta(days=1)


#建立管理者
class superuser(models.Model):
    uid = models.CharField(max_length=50,null=False,primary_key=True)
    name = models.CharField(max_length=255,null=False,blank=True)
    def __str__(self):
        return self.uid

class User_Info(models.Model):
    uid = models.CharField(max_length=50,null=False,primary_key=True)   #user_id
    name = models.CharField(max_length=255,null=False,blank=True)       #LINE名字
    points = models.IntegerField(null=False,default=0)                  #分數
    now_state = models.CharField(max_length=255,default="default")      #現在狀態
    
    def __str__(self):
        return self.uid
    
class User_ans(models.Model):
    uid = models.CharField(max_length=50,null=False)
    qid = models.IntegerField(null=False,default=0)
    user_ans = models.CharField(max_length=50, null=False)

    def __str__(self):
        return self.uid
    
class Tests(models.Model):
    qid = models.IntegerField(null=False, primary_key=True)
    show_type = models.CharField(max_length=15,null=False)
    question = models.CharField(max_length=50,null=False)
    opA = models.CharField(max_length=100, null=True)
    opB = models.CharField(max_length=100, null=True)
    opC = models.CharField(max_length=100, null=True)
    opD = models.CharField(max_length=100, null=True)
    opE = models.CharField(max_length=100, null=True)
    ans = models.CharField(max_length=100, null=False)

    def __int__(self):
        return self.id
    
class ranking(models.Model):
    rank = models.IntegerField(null=False,default=0)
    uid = models.CharField(max_length=50,null=False)
    name = models.CharField(max_length=255,null=False,blank=True) 
    points = models.IntegerField(null=False,default=0)

    def __int__(self):
        return self.uid
    

