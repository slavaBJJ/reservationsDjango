import csv
from io import StringIO

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render

from catalogue.models import Location, Show


CSV_FIELDS = [
    'slug',
    'title',
    'description',
    'duration',
    'created_in',
    'location_slug',
    'bookable',
]


class ShowCsvImportForm(forms.Form):
    csv_file = forms.FileField(label='Fichier CSV')

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        if not csv_file.name.lower().endswith('.csv'):
            raise forms.ValidationError('Le fichier doit avoir une extension .csv.')
        if csv_file.size > 2 * 1024 * 1024:
            raise forms.ValidationError('Le fichier CSV ne peut pas dépasser 2 Mo.')
        return csv_file


@staff_member_required
def export_shows(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="spectacles.csv"'

    # The UTF-8 BOM lets Excel recognize accented characters correctly.
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(CSV_FIELDS)

    shows = Show.objects.select_related('location').order_by('title', 'pk')
    for show in shows:
        writer.writerow([
            show.slug,
            show.title,
            show.description or '',
            show.duration or '',
            show.created_in,
            show.location.slug if show.location else '',
            '1' if show.bookable else '0',
        ])

    return response


def _positive_integer(value, field_name, line_number, required=True):
    value = value.strip()
    if not value and not required:
        return None
    try:
        number = int(value)
    except ValueError:
        raise ValueError(f'Ligne {line_number} : {field_name} doit être un nombre entier.')
    if number <= 0:
        raise ValueError(f'Ligne {line_number} : {field_name} doit être positif.')
    return number


def _bookable_value(value, line_number):
    normalized = value.strip().lower()
    values = {
        '1': True,
        'true': True,
        'oui': True,
        '0': False,
        'false': False,
        'non': False,
    }
    if normalized not in values:
        raise ValueError(
            f'Ligne {line_number} : bookable doit valoir 1/0, true/false ou oui/non.'
        )
    return values[normalized]


def _validate_rows(csv_file):
    try:
        content = csv_file.read().decode('utf-8-sig')
    except UnicodeDecodeError:
        raise ValueError('Le fichier doit être encodé en UTF-8.')

    try:
        reader = csv.DictReader(StringIO(content))
        if reader.fieldnames != CSV_FIELDS:
            raise ValueError(
                'Les colonnes doivent être exactement : ' + ', '.join(CSV_FIELDS) + '.'
            )

        rows = []
        seen_slugs = set()
        for line_number, row in enumerate(reader, start=2):
            slug = row['slug'].strip()
            title = row['title'].strip()
            location_slug = row['location_slug'].strip()

            if not slug:
                raise ValueError(f'Ligne {line_number} : slug est obligatoire.')
            if slug in seen_slugs:
                raise ValueError(f'Ligne {line_number} : le slug {slug} est présent plusieurs fois.')
            if not title:
                raise ValueError(f'Ligne {line_number} : title est obligatoire.')

            location = None
            if location_slug:
                try:
                    location = Location.objects.get(slug=location_slug)
                except Location.DoesNotExist:
                    raise ValueError(
                        f'Ligne {line_number} : le lieu {location_slug} n’existe pas.'
                    )

            rows.append({
                'slug': slug,
                'defaults': {
                    'title': title,
                    'description': row['description'].strip() or None,
                    'duration': _positive_integer(
                        row['duration'],
                        'duration',
                        line_number,
                        required=False,
                    ),
                    'created_in': _positive_integer(
                        row['created_in'],
                        'created_in',
                        line_number,
                    ),
                    'location': location,
                    'bookable': _bookable_value(row['bookable'], line_number),
                },
            })
            seen_slugs.add(slug)
    except csv.Error as error:
        raise ValueError(f'Le fichier CSV est illisible : {error}.')

    if not rows:
        raise ValueError('Le fichier CSV ne contient aucun spectacle.')
    return rows


@staff_member_required
def import_shows(request):
    form = ShowCsvImportForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        try:
            rows = _validate_rows(form.cleaned_data['csv_file'])
        except ValueError as error:
            form.add_error('csv_file', str(error))
        else:
            created = 0
            updated = 0
            with transaction.atomic():
                for row in rows:
                    _, was_created = Show.objects.update_or_create(
                        slug=row['slug'],
                        defaults=row['defaults'],
                    )
                    if was_created:
                        created += 1
                    else:
                        updated += 1

            messages.success(
                request,
                f'Import terminé : {created} spectacle(s) créé(s), '
                f'{updated} spectacle(s) mis à jour.',
            )
            return redirect('catalogue:shows-csv-import')

    return render(request, 'csv_catalogue/import.html', {
        'form': form,
        'title': 'Importer des spectacles en CSV',
        'csv_fields': CSV_FIELDS,
    })
