# spswarehouse_airflow

This package is a clone of `spswarehouse`, adapted to be used in Airflow. Rather than using a credentials.py file, it pulls credentials from Airflow's Connections.

# Current Version

Currently, only the Warehouse-related functionality has been adapted.  Google Drive, Google Sheets, and Google Slides are not yet supported.

# Usage

The main difference in this packages is that you do not import `Warehouse` directly from the package.  Instead, you will import the function `create_warehouse`, and then call that function to create the warehouse connection when you need it.  After completing the Warehouse work, you need to manually close the Warehouse connection.

At the top of your DAG file:
```
from spswarehouse_airflow.warehouse import create_warehouse
from spswarehouse_airflow.table_utils import *
```

In a function that is fed to a PythonOperator:
```
Warehouse = create_warehouse()
<Whatever it is you need to do in the warehouse>
Warehouse.close()
```

