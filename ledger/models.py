from django.db import models


class Supplier(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class TypeDescription(models.Model):
    code = models.CharField(max_length=10)
    description = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Type Description"
        verbose_name_plural = "Type Descriptions"

    def __str__(self):
        return f"{self.code} - {self.description}"


class ConstructionEntry(models.Model):
    LM_CHOICES = [
        ('L', 'Labor'),
        ('M', 'Materials'),
        ('U', 'Utility'),
        ('X', 'Transfer'),
    ]

    POSTED_CHOICES = [
        ('Yes', 'Yes'),
        ('Inv', 'Invoice'),
    ]

    DELIVERY_CHOICES = [
        ('Delivery', 'Delivery'),
        ('Pickup', 'Pickup'),
        ('SR In Store', 'SR In Store'),
    ]

    date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=500, blank=True, default='')
    stage = models.CharField(max_length=20, blank=True, default='')
    lc_stage = models.CharField(max_length=20, blank=True, default='', verbose_name='LC-Stage')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    estimate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='QTY')
    supplies_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tax_fees = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Tax/Fees')
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    invoiced_amt = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Invoiced Amt')
    posted = models.CharField(max_length=10, choices=POSTED_CHOICES, blank=True, default='')
    lm = models.CharField(max_length=5, choices=LM_CHOICES, blank=True, default='', verbose_name='L/M')
    supervisor = models.CharField(max_length=200, blank=True, default='')
    invoice_number = models.CharField(max_length=50, blank=True, default='', verbose_name='Invoice #')
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_CHOICES, blank=True, default='')
    materials = models.CharField(max_length=200, blank=True, default='')
    book_number = models.CharField(max_length=20, blank=True, default='', verbose_name='Book #')
    notes = models.TextField(blank=True, default='')
    type_description = models.ForeignKey(
        TypeDescription, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Type'
    )

    class Meta:
        verbose_name = "Construction Entry"
        verbose_name_plural = "Construction Entries"
        ordering = ['date', 'id']

    def __str__(self):
        return f"{self.date} - {self.description[:50]}"
