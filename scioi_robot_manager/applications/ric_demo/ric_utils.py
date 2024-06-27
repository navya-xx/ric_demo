def generate_next_id(ids):
    if not ids:
        return None

    # Extract the prefix from the first entry (assuming all entries have the same prefix)
    prefix = ''.join(filter(str.isalpha, ids[0]))

    # Extract the numeric parts and find the maximum
    max_id = max(int(''.join(filter(str.isdigit, id))) for id in ids)

    # Generate the next id by incrementing the maximum numeric part found
    next_id = prefix + str(max_id + 1)

    return next_id

