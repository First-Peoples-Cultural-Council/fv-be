def import_m2m_text_models(row, prefix, model):
    """
    Helper method to iterate over different columns in the input dataset
    based on given prefix, collect all the text values.
    Then Add instances of those models, and link them back to the primary resource
    i.e. dictionary_entry for now.
    """
    input_values = []
    for key, val in row.items():
        if key.startswith(prefix):
            input_values.append(val)

    if len(input_values) == 0:
        return

    for text in input_values:
        entry = model(text=text, dictionary_entry_id=row["id"])
        entry.save()


def get_valid_boolean_for_batch_import(input_val):
    cleaned_input = str(input_val).strip().lower()

    if cleaned_input in ["true", "yes", "y", "1"]:
        return True
    elif cleaned_input in ["false", "no", "n", "0"]:
        return False
    else:
        return None
