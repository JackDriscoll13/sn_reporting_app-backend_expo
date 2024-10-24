from crud import nielsen_crud


# The four additional mappings, returned as dictionaries
def get_station_network_mapping_dict(db):
    station_network_mapping = nielsen_crud.get_station_network_mapping(db)
    station_network_mapping_dict = station_network_mapping.set_index('station_name')['network'].to_dict()
    return station_network_mapping_dict

def get_spectrum_station_names_dict(db):
    spectrum_station_names = nielsen_crud.get_spectrum_station_name_mapping(db)
    spectrum_station_names_dict = spectrum_station_names.set_index('station_abbr')['station_name_full'].to_dict()
    return spectrum_station_names_dict

def get_daypart_order_mapping_dict(db):
    daypart_order_mapping = nielsen_crud.get_daypart_order_mapping(db)
    daypart_order_mapping_dict = daypart_order_mapping.set_index('daypart')['order_in_report_table'].to_dict()
    return daypart_order_mapping_dict

def get_fifteen_min_order_mapping_dict(db):
    fifteen_min_order_mapping = nielsen_crud.get_fifteen_min_order_mapping(db)
    fifteen_min_order_mapping_dict = fifteen_min_order_mapping.set_index('time_slot')['order_in_x_axis'].to_dict()
    return fifteen_min_order_mapping_dict

# The one user configurable mapping, contains Nielsen DMA name, Spectrum DMA name, and DMA viewership penetration
# This is stored as one table in the database, but we return as two distinct mapping dictionaries

def get_dma_name_mapping_dict(db):
    dma_name_mapping = nielsen_crud.get_dma_name_mapping(db)
    dma_name_mapping_dict = dma_name_mapping.set_index('nielsen_dma_name')['sn_dma_name'].to_dict()
    return dma_name_mapping_dict

def get_dma_penetration_mapping_dict(db):
    dma_penetration_mapping = nielsen_crud.get_dma_penetration_mapping(db)
    dma_penetration_mapping_dict = dma_penetration_mapping.set_index('sn_dma_name')['penetration_percent'].to_dict()
    return dma_penetration_mapping_dict

# Now we combine them all into one function
# def get_all_mappings(db):
#     return {
#         'station_network_mapping': get_station_network_mapping_dict(db),
#         'spectrum_station_names_mapping': get_spectrum_station_names_dict(db),
#         'daypart_order_mapping': get_daypart_order_mapping_dict(db),
#         'fifteen_min_order_mapping': get_fifteen_min_order_mapping_dict(db),
#         'dma_name_mapping': get_dma_name_mapping_dict(db),
#         'dma_penetration_mapping': get_dma_penetration_mapping_dict(db)
#     }


