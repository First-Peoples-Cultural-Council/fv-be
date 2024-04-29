def get_usages_total(usages_dict):
    # Get total count of all objects a media file is used in
    total = 0
    for usage in usages_dict.values():
        if isinstance(
            usage, list
        ):  # adding a check as some keys contain objects and not arrays
            total += len(usage)
        elif isinstance(usage, dict) and "id" in usage:
            # If there is a site the image is a banner/logo of
            total += 1
    return total
