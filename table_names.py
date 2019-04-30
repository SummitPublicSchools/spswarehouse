from .warehouse import Warehouse

def initialize_schema_object(klass):
    schema_name = klass.schema_name

    table_names = Warehouse.insp.get_table_names(schema_name)
    view_names = Warehouse.insp.get_view_names(schema_name)
    table_and_view_names = table_names + view_names

    for n in table_and_view_names:
        setattr(klass, n, property(lambda self, tn=n, schema_name=schema_name:
                                   Warehouse.reflect(tn, schema=schema_name)))                           
    return

class InformationSchema:
    schema_name = 'information_schema'

class InfoTeam:
    schema_name = 'info_team'

class PowerSchool:
    schema_name = 'powerschool'

class Public:
    schema_name = 'public'

class SchoolMint:
    schema_name = 'schoolmint'

class WildWest:
    schema_name = 'wild_west'

# initialize_schema_object(InformationSchema)
# information_schema = InformationSchema()

# initialize_schema_object(InfoTeam)
# info_team = InfoTeam()

# initialize_schema_object(PowerSchool)
# powerschool = PowerSchool()

# initialize_schema_object(SchoolMint)
# schoolmint = SchoolMint()

initialize_schema_object(Public)
public = Public()

initialize_schema_object(WildWest)
wild_west = WildWest()
