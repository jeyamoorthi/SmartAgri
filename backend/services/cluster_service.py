"""
Geographic clustering using Haversine formula.
Groups farmers within 15km radius into clusters.
"""
import math
from db.mongodb import users_col

CLUSTER_RADIUS_KM = 15.0
EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula. Returns distance in kilometers.
    """
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


async def assign_cluster(lat: float, lng: float) -> str:
    """
    Assign a user to a geographic cluster.
    Finds existing users within 15km and assigns same cluster_id,
    or creates a new cluster if none found.
    """
    col = users_col()

    # Find all existing users with coordinates
    existing_users = await col.find(
        {"gps_coordinates": {"$exists": True}},
        {"gps_coordinates": 1, "cluster_id": 1}
    ).to_list(length=1000)

    # Find the nearest cluster
    for user in existing_users:
        coords = user.get("gps_coordinates", {})
        u_lat = coords.get("lat", 0)
        u_lng = coords.get("lng", 0)
        cluster_id = user.get("cluster_id")

        if cluster_id and u_lat and u_lng:
            dist = haversine_distance(lat, lng, u_lat, u_lng)
            if dist <= CLUSTER_RADIUS_KM:
                return cluster_id

    # No nearby cluster found — create a new one
    cluster_id = f"cluster_{lat:.2f}_{lng:.2f}"
    return cluster_id


async def get_cluster_users(cluster_id: str) -> list:
    """Get all users in a given cluster."""
    col = users_col()
    users = await col.find(
        {"cluster_id": cluster_id},
        {"email": 1, "username": 1, "gps_coordinates": 1, "present_crop": 1}
    ).to_list(length=500)
    return users


async def get_nearby_users(lat: float, lng: float, radius_km: float = CLUSTER_RADIUS_KM) -> list:
    """
    Find all users within a given radius of coordinates.
    Uses Haversine formula for distance calculation.
    """
    col = users_col()
    all_users = await col.find(
        {"gps_coordinates": {"$exists": True}},
        {"email": 1, "username": 1, "gps_coordinates": 1, "present_crop": 1, "cluster_id": 1}
    ).to_list(length=1000)

    nearby = []
    for user in all_users:
        coords = user.get("gps_coordinates", {})
        u_lat = coords.get("lat", 0)
        u_lng = coords.get("lng", 0)

        if u_lat and u_lng:
            dist = haversine_distance(lat, lng, u_lat, u_lng)
            if dist <= radius_km:
                user["distance_km"] = round(dist, 2)
                nearby.append(user)

    return nearby
