import time

from django.core.management.base import BaseCommand

from scheduler_app.services.scheduler import TaskScheduler


class Command(BaseCommand):
    help = 'Run pending tasks scheduler. Use --loop for continuous polling.'

    def add_arguments(self, parser):
        parser.add_argument('--loop', action='store_true', help='Run continuously')
        parser.add_argument('--interval', type=int, default=10, help='Polling interval in seconds')

    def handle(self, *args, **options):
        scheduler = TaskScheduler()

        if not options['loop']:
            count = scheduler.run_pending()
            self.stdout.write(self.style.SUCCESS(f'Processed {count} task(s).'))
            return

        interval = options['interval']
        self.stdout.write(self.style.WARNING(f'Scheduler started with interval={interval}s'))
        try:
            while True:
                count = scheduler.run_pending()
                self.stdout.write(self.style.SUCCESS(f'Processed {count} task(s).'))
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Scheduler stopped.'))
