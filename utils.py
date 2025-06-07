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

def get_location_name(location_code, location_type='city'):
    """
    Convert location code to full name
    Args:
        location_code: code like 'hcm', 'quan5', etc.
        location_type: 'city' or 'district'
    Returns:
        Full location name
    """
    # Mapping for cities/provinces
    city_mapping = {
        'hcm': 'TP. Hồ Chí Minh',
        'hanoi': 'Hà Nội',
        'danang': 'Đà Nẵng',
        'cantho': 'Cần Thơ',
        'haiphong': 'Hải Phòng'
    }
    
    # Mapping for districts in Ho Chi Minh City
    district_mapping = {
        'quan1': 'Quận 1',
        'quan2': 'Quận 2', 
        'quan3': 'Quận 3',
        'quan4': 'Quận 4',
        'quan5': 'Quận 5',
        'quan6': 'Quận 6',
        'quan7': 'Quận 7',
        'quan8': 'Quận 8',
        'quan9': 'Quận 9',
        'quan10': 'Quận 10',
        'quan11': 'Quận 11',
        'quan12': 'Quận 12',
        'quantanbinh': 'Quận Tân Bình',
        'quantanphu': 'Quận Tân Phú',
        'quanbinhtan': 'Quận Bình Tân',
        'quanbinhthanh': 'Quận Bình Thạnh',
        'quangovap': 'Quận Gò Vấp',
        'quanphunhuan': 'Quận Phú Nhuận',
        'quanthuduc': 'Quận Thủ Đức',
        # Hanoi districts
        'quanbadinh': 'Quận Ba Đình',
        'quanhoankieu': 'Quận Hoàn Kiếm',
        'quantayho': 'Quận Tây Hồ',
        'quanlongbien': 'Quận Long Biên',
        'quancaugiay': 'Quận Cầu Giấy',
        'quandongda': 'Quận Đống Đa',
        'quanhaibatrung': 'Quận Hai Bà Trưng',
        'quanhoangmai': 'Quận Hoàng Mai',
        'quanthanxuan': 'Quận Thanh Xuân',
        'quannamtuliem': 'Quận Nam Từ Liêm',
        'quanbactuliem': 'Quận Bắc Từ Liêm'
    }
    
    if location_type == 'city':
        return city_mapping.get(location_code, location_code)
    elif location_type == 'district':
        return district_mapping.get(location_code, location_code)
    
    return location_code
