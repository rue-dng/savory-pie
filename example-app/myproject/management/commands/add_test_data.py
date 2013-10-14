from django.core.management.base import BaseCommand

from myproject import models


class Command(BaseCommand):

    help = 'Create some data for testing.'

    def handle(self, **options):
        z1 = models.Author(name='Smith'); z1.save()
        z2 = models.Author(name='Hemingway'); z2.save()
        c1 = models.Book(title='A Tree Grows in Brooklyn'); c1.save()
        c2 = models.Book(title='The Sun Also Rises'); c2.save()
        s1 = models.Shelf(name='NewYork'); s1.save()
        s2 = models.Shelf(name='War'); s2.save()
        models.AuthorBook(author=z1, book=c1, shelf=s1).save()
        models.AuthorBook(author=z2, book=c2, shelf=s2).save()
