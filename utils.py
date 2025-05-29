def get_rank_info(xp_current):
    # Define rank thresholds and names
    rank_thresholds = {
        'Bronze': 0,
        'Silver': 1000,
        'Gold': 5000,
        'Platium': 10000,
        'Diamond': 20000
    }

    # Determine current rank
    current_rank = 'Bronze'
    for rank, threshold in rank_thresholds.items():
        if xp_current >= threshold:
            current_rank = rank

    # Get experience points needed to reach the next rank
    rank_values = list(rank_thresholds.values())
    current_rank_index = list(rank_thresholds.keys()).index(current_rank)
    
    # Calculate how much more xp the user needs for the next rank
    if current_rank_index + 1 < len(rank_values):
        next_rank = list(rank_thresholds.keys())[current_rank_index + 1]
        next_min = rank_values[current_rank_index + 1]
    else:
        next_rank = 'Diamond'
        next_min = 0

    return current_rank, xp_current, next_rank, next_min
