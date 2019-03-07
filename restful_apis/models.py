from django.db import models

# represent stock 
class Stock(models.Model):
	code_name = models.CharField(max_length=10)
	date = models.DateField()
	price = models.FloatField()
	# make sure the entry is unique
	class Meta:
		unique_together = (('code_name', 'date'),)	