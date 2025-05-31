def get_rank_info(xp):
    """
    Calculate rank information based on experience points
    Returns: (current_rank, current_min, next_rank, next_min)
    """
    ranks = [
        ('Bronze', 0),
        ('Silver', 1000),
        ('Gold', 5000),
        ('Emerald', 10000),
        ('Diamond', 20000)
    ]
    
    current_rank = ranks[0][0]
    current_min = ranks[0][1]
    next_rank = None
    next_min = None
    
    for i, (rank, min_xp) in enumerate(ranks):
        if xp >= min_xp:
            current_rank = rank
            current_min = min_xp
            if i < len(ranks) - 1:
                next_rank = ranks[i + 1][0]
                next_min = ranks[i + 1][1]
        else:
            break
            
    return current_rank, current_min, next_rank, next_min 