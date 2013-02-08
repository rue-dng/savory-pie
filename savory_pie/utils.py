from django.db.models.constants import LOOKUP_SEP 

def append_select_related(queryset, *related_fields):
    """
        The django queryset use the last call to select_related, but we want to
        be able to build it up call by call. So we have the badness all in
        here. I am sorry when you upgrade django and this fails.

        Hint: django/db/models/sql/query.py:add_select_related
    """
    for field in related_fields:
        queryset.query.select_related = select_related = queryset.query.select_related or {}
        for remote in field.split(LOOKUP_SEP):
            select_related = select_related.setdefault(remote, {})
