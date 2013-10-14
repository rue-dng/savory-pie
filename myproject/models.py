import logging

from django.contrib import admin
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from savory_pie.django import fields, resources, filters

logger = logging.getLogger(__name__)

class Person(models.Model):
    name = models.CharField(max_length=128)
    def __str__(self):
        return self.name

class Group(models.Model):
    name = models.CharField(max_length=128)
    members = models.ManyToManyField(Person, through='Membership')
    def __str__(self):
        return self.name

class Membership(models.Model):
    person = models.ForeignKey(Person)
    group = models.ForeignKey(Group)
    date_joined = models.DateField()
    invite_reason = models.CharField(max_length=64)

# I need some models to help me sort out AttributeFieldWithModel

class InnerThing(models.Model):
    name_i = models.CharField(max_length=128)

class MiddleThing(models.Model):
    name_m = models.CharField(max_length=128)
    inner = models.ForeignKey(InnerThing)

class OuterThing(models.Model):
    name_o = models.CharField(max_length=128)
    middle = models.ForeignKey(MiddleThing)

####### Here's how inlines work in the admin page ##########

class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1

class PersonAdmin(admin.ModelAdmin):
    inlines = (MembershipInline,)

class GroupAdmin(admin.ModelAdmin):
    inlines = (MembershipInline,)

admin.site.register(Person, PersonAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Membership)


#######


class Author(models.Model):
    """
    A Author is a book place holder.
    """
    name = models.CharField(_('Name'), max_length=100)

    def __str__(self):
        return self.name

    def to_json(self):
        return {
            'name': self.name,
            'type': 'Author'
        }

IS_THROUGH = True


class Book(models.Model):
    """
    The Book model holds markdown that will be displayed in a author.
    """
    title = models.CharField(_(u'Title'), max_length=255, blank=False)
    if IS_THROUGH:
        authors = models.ManyToManyField(Author, through='AuthorBook')
    else:
        authors = models.ManyToManyField(Author)

    def __str__(self):
        return self.title

    def to_json(self):
        return {
            'title': self.title,
            'type': 'Book'
        }


class Shelf(models.Model):
    """
    Some documentation about Shelf.
    """
    name = models.CharField(_('Name'), max_length=100)

    def __str__(self):
        return self.name

    def to_json(self):
        return {
            'name': self.name,
            'type': 'Shelf'
        }


class AuthorBook(models.Model):
    """
    The AuthorBook model is used to relate a Author to a specific Book object.

    """
    author = models.ForeignKey(Author)
    book = models.ForeignKey(Book)
    shelf = models.ForeignKey(Shelf, blank=True, null=True)

    def __str__(self):
        return "%s ; %s ; %s" % (repr(self.author), repr(self.book), repr(self.shelf))

    def to_json(self):
        return {
            'author': self.author,
            'book': self.book,
            'shelf': self.shelf,
            'type': 'AuthorBook'
        }


class AuthorAdmin(admin.ModelAdmin):
    list_display = ("id", "name",)


class BookAdmin(admin.ModelAdmin):
    list_display = ("id", "title",)


class AuthorBookAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "book", "shelf",)
    list_filter = ("author__name",)


class ShelfAdmin(admin.ModelAdmin):
    list_display = ("id", "name",)


admin.site.register(Author, AuthorAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Shelf, ShelfAdmin)
admin.site.register(AuthorBook, AuthorBookAdmin)
