import math

class LogisticsEngine:
    # Bomet County Base Logistics Configuration
    BASE_FARE = 50.0  # Base fee just for assigning a rider (KES)
    RATE_PER_KM = 30.0  # Cost per kilometer (KES)
    FREE_DELIVERY_THRESHOLD = 3000.0  # Cart value for 100% free delivery
    DISCOUNT_THRESHOLD = 1500.0  # Cart value for 50% off delivery
    
    @staticmethod
    def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculates the exact geospatial distance between two points on the Earth.
        Returns the distance in kilometers.
        """
        R = 6371.0 # Radius of the Earth in km

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat / 2)**2 + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return round(distance, 2)

    @classmethod
    def calculate_pricing_breakdown(cls, cart_total: float, distance_km: float) -> dict:
        """
        The Psychological Pricing Engine. 
        Calculates logistics costs and applies behavioral discounts to increase AOV.
        """
        raw_delivery_fee = cls.BASE_FARE + (distance_km * cls.RATE_PER_KM)
        
        # Apply Psychological Discounts
        discount_applied = 0.0
        if cart_total >= cls.FREE_DELIVERY_THRESHOLD:
            discount_applied = raw_delivery_fee
            message = "Free Delivery Unlocked! 🎉"
        elif cart_total >= cls.DISCOUNT_THRESHOLD:
            discount_applied = raw_delivery_fee * 0.5
            message = "50% Off Delivery Unlocked! 🚀"
        else:
            amount_to_discount = cls.DISCOUNT_THRESHOLD - cart_total
            message = f"Add KES {amount_to_discount} more to get 50% off delivery."

        final_delivery_fee = raw_delivery_fee - discount_applied

        return {
            "distance_km": distance_km,
            "raw_delivery_fee": round(raw_delivery_fee, 2),
            "discount_applied": round(discount_applied, 2),
            "final_delivery_fee": round(final_delivery_fee, 2),
            "total_checkout_price": round(cart_total + final_delivery_fee, 2),
            "psychology_nudge": message
        }