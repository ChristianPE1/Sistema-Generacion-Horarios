# Generated migration for LLR dataset support

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schedule_app', '0001_initial'),
    ]

    operations = [
        # Agregar department a Class
        migrations.AddField(
            model_name='class',
            name='department',
            field=models.IntegerField(null=True, blank=True),
        ),
        
        # Agregar breakTime a TimeSlot
        migrations.AddField(
            model_name='timeslot',
            name='break_time',
            field=models.IntegerField(default=10),
        ),
        
        # Crear modelo GroupConstraint
        migrations.CreateModel(
            name='GroupConstraint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('xml_id', models.IntegerField(unique=True)),
                ('constraint_type', models.CharField(max_length=50)),
                ('preference', models.CharField(max_length=10)),
                ('course_limit', models.IntegerField(null=True, blank=True)),
                ('delta', models.IntegerField(null=True, blank=True)),
            ],
            options={
                'db_table': 'group_constraints',
                'verbose_name': 'Restricción de Grupo',
                'verbose_name_plural': 'Restricciones de Grupo',
            },
        ),
        
        # Crear relación muchos-a-muchos entre GroupConstraint y Class
        migrations.CreateModel(
            name='GroupConstraintClass',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('constraint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='classes', to='schedule_app.groupconstraint')),
                ('class_obj', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_constraints', to='schedule_app.class')),
            ],
            options={
                'db_table': 'group_constraint_classes',
                'unique_together': {('constraint', 'class_obj')},
            },
        ),
        
        # Agregar weight a la relación StudentClass (para course projections)
        migrations.AddField(
            model_name='studentclass',
            name='weight',
            field=models.FloatField(default=1.0),
        ),
        
        # Agregar offering_id y weight para student demands
        migrations.AddField(
            model_name='studentclass',
            name='offering',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, to='schedule_app.course'),
        ),
    ]
