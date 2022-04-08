user_data = {}


class User:
    """

    """
    def __init__(self, user_id):
        self.user_id = user_id
        self.current_command = None
        self.city = None
        self.city_id = None
        self.hotels_num = None
        self.photos_num = None
        self.sort = 'PRICE'
        self.check_in = None
        self.check_out = None
        self.price_min = None
        self.price_max = None
        self.min_distance_from_center = None
        self.max_distance_from_center = None
        self.total_hotels = None
        self.hotels = None
        self.photos = None
        self.results = ''
