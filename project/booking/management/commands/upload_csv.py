import csv
from django.core.management.base import BaseCommand
from booking.models import TaxiData  # Use your model

class Command(BaseCommand):
    help = 'Load taxi data from a CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **kwargs):
        file_path = kwargs['csv_file']
        with open(file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                TaxiData.objects.create(
                    trip_type=row['trip_type'],
                    pickup_location=row['pickup_location'],
                    dropoff_location=row['dropoff_location'],
                    transport_type=row['transport_type'],
                    adults=row['adults'],
                    children=row['children'],
                    pickup_time=row['pickup_time'],
                    return_time=row['return_time'],
                    price=row['price']
                )
        self.stdout.write(self.style.SUCCESS('CSV data uploaded successfully!'))
