from datetime import datetime

from django.db import models


# Create your models here.
class Counters(models.Model):
    id = models.AutoField
    count = models.IntegerField(default=0)
    createdAt = models.DateTimeField(auto_now = True)
    updatedAt = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'Counters'  # 数据库表名
