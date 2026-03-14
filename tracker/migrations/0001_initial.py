from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Food',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('unit', models.CharField(default='100g', help_text='e.g. 100g, serving, piece', max_length=30)),
                ('calories', models.FloatField()),
                ('protein', models.FloatField(default=0)),
                ('fat', models.FloatField(default=0)),
                ('carbohydrates', models.FloatField(default=0)),
                ('fiber', models.FloatField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='foods', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['name'], 'unique_together': {('user', 'name')}},
        ),
        migrations.CreateModel(
            name='MealRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meal_type', models.CharField(choices=[('breakfast', 'Breakfast'), ('lunch', 'Lunch'), ('dinner', 'Dinner'), ('snack', 'Snack')], default='breakfast', max_length=20)),
                ('quantity', models.FloatField(help_text='Multiplier based on the food unit, e.g. 1 serving or 1 x 100g')),
                ('record_date', models.DateField()),
                ('notes', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('food', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='records', to='tracker.food')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='meal_records', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-record_date', 'meal_type', '-created_at']},
        ),
    ]
