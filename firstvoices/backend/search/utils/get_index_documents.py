def text_as_list(comma_delimited_text):
    if comma_delimited_text is None:
        return comma_delimited_text

    items = comma_delimited_text.split(",")
    return [item.strip() for item in items]


def fields_as_list(queryset, field):
    values = queryset.values_list(field)
    return [str(x[0]) for x in values]
