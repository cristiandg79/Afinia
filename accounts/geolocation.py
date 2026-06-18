import math
import unicodedata


RADIUS_CHOICES = [
    ('', 'Indiferente'),
    ('10', '10 Km'),
    ('25', '25 Km'),
    ('50', '50 Km'),
    ('100', '100 Km'),
]


CITY_COORDS = {
    # España: capitales grandes y áreas metropolitanas principales.
    ('ES', 'a coruna'): (43.3623, -8.4115),
    ('ES', 'alicante'): (38.3452, -0.4810),
    ('ES', 'alcorcon'): (40.3468, -3.8278),
    ('ES', 'alcobendas'): (40.5373, -3.6370),
    ('ES', 'algeciras'): (36.1408, -5.4562),
    ('ES', 'almeria'): (36.8340, -2.4637),
    ('ES', 'arona'): (28.0996, -16.6810),
    ('ES', 'avila'): (40.6565, -4.6818),
    ('ES', 'badalona'): (41.4500, 2.2474),
    ('ES', 'badajoz'): (38.8794, -6.9707),
    ('ES', 'barakaldo'): (43.2970, -2.9916),
    ('ES', 'barcelona'): (41.3874, 2.1686),
    ('ES', 'bilbao'): (43.2630, -2.9350),
    ('ES', 'burgos'): (42.3439, -3.6969),
    ('ES', 'cadiz'): (36.5271, -6.2886),
    ('ES', 'castellon de la plana'): (39.9864, -0.0513),
    ('ES', 'castello de la plana'): (39.9864, -0.0513),
    ('ES', 'cerdanyola del valles'): (41.4911, 2.1408),
    ('ES', 'ceuta'): (35.8894, -5.3198),
    ('ES', 'ciudad real'): (38.9848, -3.9274),
    ('ES', 'cornella de llobregat'): (41.3556, 2.0704),
    ('ES', 'cordoba'): (37.8882, -4.7794),
    ('ES', 'coslada'): (40.4238, -3.5613),
    ('ES', 'cuenca'): (40.0704, -2.1374),
    ('ES', 'dos hermanas'): (37.2866, -5.9242),
    ('ES', 'el prat de llobregat'): (41.3275, 2.0947),
    ('ES', 'elche'): (38.2699, -0.7126),
    ('ES', 'elx'): (38.2699, -0.7126),
    ('ES', 'esplugues de llobregat'): (41.3773, 2.0881),
    ('ES', 'fuenlabrada'): (40.2902, -3.8035),
    ('ES', 'getafe'): (40.3083, -3.7327),
    ('ES', 'gijon'): (43.5322, -5.6611),
    ('ES', 'girona'): (41.9794, 2.8214),
    ('ES', 'granada'): (37.1773, -3.5986),
    ('ES', 'guadalajara'): (40.6333, -3.1667),
    ('ES', 'huelva'): (37.2614, -6.9447),
    ('ES', 'huesca'): (42.1401, -0.4089),
    ('ES', 'hospitalet de llobregat'): (41.3662, 2.1165),
    ('ES', 'jaen'): (37.7796, -3.7849),
    ('ES', 'jerez de la frontera'): (36.6850, -6.1261),
    ('ES', 'las palmas de gran canaria'): (28.1235, -15.4363),
    ('ES', 'l hospitalet de llobregat'): (41.3662, 2.1165),
    ('ES', 'la laguna'): (28.4874, -16.3159),
    ('ES', 'leon'): (42.5987, -5.5671),
    ('ES', 'leganes'): (40.3319, -3.7687),
    ('ES', 'lleida'): (41.6176, 0.6200),
    ('ES', 'logrono'): (42.4627, -2.4449),
    ('ES', 'lugo'): (43.0097, -7.5568),
    ('ES', 'madrid'): (40.4168, -3.7038),
    ('ES', 'malaga'): (36.7213, -4.4214),
    ('ES', 'marbella'): (36.5101, -4.8824),
    ('ES', 'mataro'): (41.5381, 2.4445),
    ('ES', 'melilla'): (35.2923, -2.9381),
    ('ES', 'mollet del valles'): (41.5408, 2.2135),
    ('ES', 'mostoles'): (40.3223, -3.8649),
    ('ES', 'murcia'): (37.9922, -1.1307),
    ('ES', 'orense'): (42.3358, -7.8639),
    ('ES', 'ourense'): (42.3358, -7.8639),
    ('ES', 'oviedo'): (43.3619, -5.8494),
    ('ES', 'palencia'): (42.0097, -4.5288),
    ('ES', 'palma'): (39.5696, 2.6502),
    ('ES', 'palma de mallorca'): (39.5696, 2.6502),
    ('ES', 'pamplona'): (42.8125, -1.6458),
    ('ES', 'parla'): (40.2360, -3.7675),
    ('ES', 'pontevedra'): (42.4310, -8.6444),
    ('ES', 'pozuelo de alarcon'): (40.4352, -3.8131),
    ('ES', 'reus'): (41.1548, 1.1087),
    ('ES', 'rivas vaciamadrid'): (40.3261, -3.5109),
    ('ES', 'sabadell'): (41.5463, 2.1086),
    ('ES', 'salamanca'): (40.9701, -5.6635),
    ('ES', 'san cristobal de la laguna'): (28.4874, -16.3159),
    ('ES', 'san sebastian'): (43.3183, -1.9812),
    ('ES', 'santander'): (43.4623, -3.8099),
    ('ES', 'sant adria de besos'): (41.4306, 2.2185),
    ('ES', 'sant boi de llobregat'): (41.3474, 2.0431),
    ('ES', 'sant cugat del valles'): (41.4706, 2.0853),
    ('ES', 'santa coloma de gramenet'): (41.4515, 2.2081),
    ('ES', 'santa cruz de tenerife'): (28.4636, -16.2518),
    ('ES', 'segovia'): (40.9429, -4.1088),
    ('ES', 'sevilla'): (37.3891, -5.9845),
    ('ES', 'soria'): (41.7666, -2.4790),
    ('ES', 'tarragona'): (41.1189, 1.2445),
    ('ES', 'terrassa'): (41.5632, 2.0089),
    ('ES', 'teruel'): (40.3456, -1.1065),
    ('ES', 'toledo'): (39.8628, -4.0273),
    ('ES', 'torrejon de ardoz'): (40.4568, -3.4755),
    ('ES', 'valencia'): (39.4699, -0.3763),
    ('ES', 'valladolid'): (41.6523, -4.7245),
    ('ES', 'vitoria'): (42.8467, -2.6716),
    ('ES', 'vitoria gasteiz'): (42.8467, -2.6716),
    ('ES', 'vigo'): (42.2406, -8.7207),
    ('ES', 'viladecans'): (41.3141, 2.0143),
    ('ES', 'vilanova i la geltru'): (41.2239, 1.7251),
    ('ES', 'zamora'): (41.5035, -5.7446),
    ('ES', 'zaragoza'): (41.6488, -0.8891),

    # Argentina.
    ('AR', 'buenos aires'): (-34.6037, -58.3816),
    ('AR', 'cordoba'): (-31.4201, -64.1888),
    ('AR', 'la plata'): (-34.9215, -57.9545),
    ('AR', 'mar del plata'): (-38.0055, -57.5426),
    ('AR', 'mendoza'): (-32.8895, -68.8458),
    ('AR', 'rosario'): (-32.9442, -60.6505),
    ('AR', 'san miguel de tucuman'): (-26.8083, -65.2176),

    # Bolivia.
    ('BO', 'cochabamba'): (-17.3895, -66.1568),
    ('BO', 'el alto'): (-16.5000, -68.1500),
    ('BO', 'la paz'): (-16.4897, -68.1193),
    ('BO', 'santa cruz de la sierra'): (-17.7833, -63.1821),
    ('BO', 'sucre'): (-19.0196, -65.2619),

    # Chile.
    ('CL', 'antofagasta'): (-23.6509, -70.3975),
    ('CL', 'concepcion'): (-36.8201, -73.0444),
    ('CL', 'la serena'): (-29.9027, -71.2519),
    ('CL', 'santiago'): (-33.4489, -70.6693),
    ('CL', 'valparaiso'): (-33.0472, -71.6127),
    ('CL', 'vina del mar'): (-33.0153, -71.5500),

    # Colombia.
    ('CO', 'barranquilla'): (10.9685, -74.7813),
    ('CO', 'bogota'): (4.7110, -74.0721),
    ('CO', 'bucaramanga'): (7.1193, -73.1227),
    ('CO', 'cali'): (3.4516, -76.5320),
    ('CO', 'cartagena'): (10.3910, -75.4794),
    ('CO', 'medellin'): (6.2442, -75.5812),

    # Costa Rica.
    ('CR', 'alajuela'): (10.0162, -84.2116),
    ('CR', 'cartago'): (9.8644, -83.9194),
    ('CR', 'heredia'): (9.9981, -84.1165),
    ('CR', 'san jose'): (9.9281, -84.0907),

    # Cuba.
    ('CU', 'camaguey'): (21.3926, -77.9053),
    ('CU', 'la habana'): (23.1136, -82.3666),
    ('CU', 'santiago de cuba'): (20.0169, -75.8302),
    ('CU', 'santa clara'): (22.4069, -79.9649),

    # República Dominicana.
    ('DO', 'la romana'): (18.4273, -68.9728),
    ('DO', 'santiago de los caballeros'): (19.4792, -70.6931),
    ('DO', 'santo domingo'): (18.4861, -69.9312),

    # Ecuador.
    ('EC', 'cuenca'): (-2.9006, -79.0045),
    ('EC', 'guayaquil'): (-2.1894, -79.8891),
    ('EC', 'quito'): (-0.1807, -78.4678),
    ('EC', 'santo domingo'): (-0.2531, -79.1754),

    # El Salvador.
    ('SV', 'san miguel'): (13.4833, -88.1833),
    ('SV', 'san salvador'): (13.6929, -89.2182),
    ('SV', 'santa ana'): (13.9942, -89.5597),

    # Guatemala.
    ('GT', 'ciudad de guatemala'): (14.6349, -90.5069),
    ('GT', 'guatemala'): (14.6349, -90.5069),
    ('GT', 'mixco'): (14.6333, -90.6064),
    ('GT', 'quetzaltenango'): (14.8347, -91.5181),

    # Honduras.
    ('HN', 'la ceiba'): (15.7792, -86.7930),
    ('HN', 'san pedro sula'): (15.5042, -88.0250),
    ('HN', 'tegucigalpa'): (14.0723, -87.1921),

    # México.
    ('MX', 'ciudad de mexico'): (19.4326, -99.1332),
    ('MX', 'cdmx'): (19.4326, -99.1332),
    ('MX', 'guadalajara'): (20.6597, -103.3496),
    ('MX', 'merida'): (20.9674, -89.5926),
    ('MX', 'monterrey'): (25.6866, -100.3161),
    ('MX', 'puebla'): (19.0414, -98.2063),
    ('MX', 'queretaro'): (20.5888, -100.3899),
    ('MX', 'tijuana'): (32.5149, -117.0382),

    # Nicaragua.
    ('NI', 'leon'): (12.4356, -86.8794),
    ('NI', 'managua'): (12.1140, -86.2362),
    ('NI', 'masaya'): (11.9744, -86.0942),

    # Panamá.
    ('PA', 'ciudad de panama'): (8.9824, -79.5199),
    ('PA', 'colon'): (9.3592, -79.9014),
    ('PA', 'david'): (8.4273, -82.4308),
    ('PA', 'panama'): (8.9824, -79.5199),

    # Paraguay.
    ('PY', 'asuncion'): (-25.2637, -57.5759),
    ('PY', 'ciudad del este'): (-25.5167, -54.6167),
    ('PY', 'san lorenzo'): (-25.3397, -57.5088),

    # Perú.
    ('PE', 'arequipa'): (-16.4090, -71.5375),
    ('PE', 'cusco'): (-13.5319, -71.9675),
    ('PE', 'lima'): (-12.0464, -77.0428),
    ('PE', 'trujillo'): (-8.1091, -79.0215),

    # Puerto Rico.
    ('PR', 'bayamon'): (18.3986, -66.1557),
    ('PR', 'carolina'): (18.3808, -65.9574),
    ('PR', 'ponce'): (18.0111, -66.6141),
    ('PR', 'san juan'): (18.4655, -66.1057),

    # Uruguay.
    ('UY', 'canelones'): (-34.5228, -56.2778),
    ('UY', 'maldonado'): (-34.9011, -54.9516),
    ('UY', 'montevideo'): (-34.9011, -56.1645),
    ('UY', 'salto'): (-31.3833, -57.9667),

    # Venezuela.
    ('VE', 'barquisimeto'): (10.0678, -69.3467),
    ('VE', 'caracas'): (10.4806, -66.9036),
    ('VE', 'maracaibo'): (10.6545, -71.6500),
    ('VE', 'maracay'): (10.2469, -67.5958),
    ('VE', 'valencia'): (10.1579, -67.9972),

    # Estados Unidos.
    ('US', 'chicago'): (41.8781, -87.6298),
    ('US', 'houston'): (29.7604, -95.3698),
    ('US', 'los angeles'): (34.0522, -118.2437),
    ('US', 'miami'): (25.7617, -80.1918),
    ('US', 'new york'): (40.7128, -74.0060),
    ('US', 'nueva york'): (40.7128, -74.0060),
    ('US', 'orlando'): (28.5383, -81.3792),
    ('US', 'san antonio'): (29.4241, -98.4936),
}


def normalize_city(city):
    normalized = unicodedata.normalize('NFKD', city or '')
    normalized = ''.join(char for char in normalized if not unicodedata.combining(char))
    normalized = normalized.lower().replace("'", ' ').replace('.', ' ').strip()
    return ' '.join(normalized.split())


def city_coords(country, city):
    return CITY_COORDS.get((country or 'ES', normalize_city(city)))


def clean_radius(value):
    valid_values = {value for value, _ in RADIUS_CHOICES}
    return value if value in valid_values else ''


def distance_km(origin, destination):
    lat1, lon1 = origin
    lat2, lon2 = destination
    earth_radius_km = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return earth_radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def within_radius(origin_country, origin_city, target_country, target_city, radius):
    origin = city_coords(origin_country, origin_city)
    destination = city_coords(target_country, target_city)
    if not origin or not destination:
        return False
    return distance_km(origin, destination) <= int(radius)


def filter_by_user_radius(items, user_profile, radius, country_attr='country', city_attr='city'):
    if not radius:
        return items
    return [
        item for item in items
        if within_radius(
            user_profile.country,
            user_profile.city,
            getattr(item, country_attr, ''),
            getattr(item, city_attr, ''),
            radius,
        )
    ]
