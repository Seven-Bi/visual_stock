from django.db import models



class Stock(models.Model):
	code_name = models.CharField(max_length=10)
	date = models.DateField()
	price = models.FloatField()

	class Meta:
		unique_together = (('code_name', 'date'),)
		ordering = ('code_name', 'date',)	