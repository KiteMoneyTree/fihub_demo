import pandas as pd
import psycopg2
import logging
from io import StringIO
from enum import Enum
import traceback

class PlatformType(Enum):
    FLIPKART = 'FLIPKART'
    AMAZON = 'AMAZON'
    MEESHO = 'MEESHO'

def lambda_handler(event, context):
    """
    Fetches data from a CSV URL, cleans and transforms it, 
    and inserts into a PostgreSQL database, handling foreign keys, data integrity, and errors.

    Args:
        event: AWS Lambda event object.
        context: AWS Lambda context object.

    Returns:
        Dictionary containing the success message or error details.
    """

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # if True:
    try:
        # 1. Get CSV URL from event
        csv_url = event['csv_url'] 
        csv_url='https://drive.google.com/uc?id=' + csv_url.split('/')[-2]

        # 2. Fetch data from CSV URL
        csv_data = pd.read_csv(csv_url)

        # 3. Platform Detection and Data Mapping
        platform_type = csv_data['Platform'].iloc[0].upper()  # Get platform type from first row
        platform_to_common_keys = {
            PlatformType.AMAZON.value: {
                'OrderID': 'order_id',
                'ProductID': 'product_id',
                'ProductName': 'product_name',
                'Category': 'category',
                'QuantitySold': 'quantity_sold',
                'SellingPrice': 'selling_price',
                'DateOfSale': 'date_of_sale',
                'CustomerID': 'customer_id',
                'CustomerName': 'customer_name',
                'ContactEmail': 'contact_email',
                'PhoneNumber': 'phone_number',
                'DeliveryAddress': 'delivery_address',
                'DeliveryDate': 'delivery_date',
                'DeliveryStatus': 'delivery_status',
                'Platform': 'platform',  # Keep platform for reference
                'PrimeDelivery': 'prime_delivery',
                'WarehouseLocation': 'warehouse_location',
            },
            PlatformType.FLIPKART.value: {
                'OrderID': 'order_id',
                'ProductID': 'product_id',
                'ProductName': 'product_name',
                'Category': 'category',
                'QuantitySold': 'quantity_sold',
                'SellingPrice': 'selling_price',
                'DateOfSale': 'date_of_sale',
                'CustomerID': 'customer_id',
                'CustomerName': 'customer_name',
                'ContactEmail': 'contact_email',
                'PhoneNumber': 'phone_number',
                'DeliveryAddress': 'delivery_address',
                'DeliveryDate': 'delivery_date',
                'DeliveryStatus': 'delivery_status',
                'Platform': 'platform',  # Keep platform for reference
                'CouponUsed': 'coupon_used',
                'ReturnWindow': 'return_window',
            },
            PlatformType.MEESHO.value: {
                'OrderID': 'order_id',
                'ProductID': 'product_id',
                'ProductName': 'product_name',
                'Category': 'category',
                'QuantitySold': 'quantity_sold',
                'SellingPrice': 'selling_price',
                'DateOfSale': 'date_of_sale',
                'CustomerID': 'customer_id',
                'CustomerName': 'customer_name',
                'ContactEmail': 'contact_email',
                'PhoneNumber': 'phone_number',
                'DeliveryAddress': 'delivery_address',
                'DeliveryDate': 'delivery_date',
                'DeliveryStatus': 'delivery_status',
                'Platform': 'platform',  # Keep platform for reference
                'ResellerName': 'reseller_name',
                'CommissionPercentage': 'commission_percentage',
            },
        }

        # Ensure platform is supported
        if platform_type not in platform_to_common_keys.keys():
            raise ValueError(f"Unsupported platform: {platform_type}")

        # Map platform-specific columns to common keys
        common_keys = platform_to_common_keys[platform_type]
        csv_data = csv_data.rename(columns=common_keys)
        # 4. Data Cleaning and Transformation
        csv_data['date_of_sale'] = pd.to_datetime(csv_data['date_of_sale'], errors='coerce')
        csv_data['delivery_date'] = pd.to_datetime(csv_data['delivery_date'], errors='coerce')

        # Handle potential data type and length issues
        csv_data['quantity_sold'] = csv_data['quantity_sold'].fillna(0).astype(int)
        csv_data['selling_price'] = csv_data['selling_price'].fillna(0).astype(float)
        csv_data['customer_id'] = csv_data['customer_id'].astype(str)  # Ensure CustomerID is string

        # 5. Connect to PostgreSQL database
        # **In production, retrieve credentials from AWS Secrets Manager**
        host = "demo-pgdb-kumarankur2106.d.aivencloud.com" 
        database = "defaultdb"
        user = "avnadmin"
        password = "AVNS_tUouQ3erHSA2RJqqTkE" 
        port= 15662

        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port= port,
        )
        cur = conn.cursor()

        # 6. Insert data into PostgreSQL
        success_count = 0
        failed_count = 0

        for index, row in csv_data.iterrows():
            try:
            # if True:
                # 6.1 Create unique customer_id 
                customer_id = f"{row['platform']}_{row['customer_id']}" 

                # 6.2 Insert into Customer table (if not already exists)
                customer_name = row['customer_name'] 
                contact_email = row['contact_email'] 
                phone_number = row['phone_number'] 
                if phone_number and len(phone_number) > 20:
                    phone_number = phone_number[:20]  # Truncate if exceeding length limit

                cur.execute("""
                    INSERT INTO mains_customer (customer_id, customer_name, contact_email, phone_number)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (customer_id) DO NOTHING; 
                """, (customer_id, customer_name, contact_email, phone_number))

                # 6.3 Insert into Platform table (if not already exists)
                platform_name = row['platform']
                cur.execute("""
                    INSERT INTO mains_platform (platform_name)
                    VALUES (%s)
                    ON CONFLICT (platform_name) DO NOTHING;
                """, (platform_name,))

                # 6.4 Insert into Orders table
                order_id = row['order_id'] 
                product_id = row['product_id'] if 'product_id' in row else None 
                product_name = row['product_name'] if 'product_name' in row else None 
                quantity_sold = row['quantity_sold'] 
                selling_price = row['selling_price'] 
                date_of_sale = row['date_of_sale'] 

                # Retrieve platform_id (assumes platform_name is unique)
                cur.execute("SELECT id FROM mains_platform WHERE platform_name = %s", (platform_name,))
                platform_id = cur.fetchone()[0] 
                coupon_used = row['coupon_used'] if 'coupon_used' in row else False 
                return_window = row['return_window'] if 'return_window' in row else 0 
                cur.execute("""
                    INSERT INTO mains_order (
                        order_id, product_id, product_name, category, quantity_sold, 
                        selling_price, date_of_sale, customer_id, platform_id, 
                        coupon_used, return_window
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (order_id, product_id, product_name, row['category'], quantity_sold, 
                       selling_price, date_of_sale, customer_id, platform_id, 
                       coupon_used, return_window))

                # 6.5 Insert into Deliveries table
                delivery_address = row['delivery_address'] 
                delivery_date = row['delivery_date'] 
                delivery_status = row['delivery_status'] 
                delivery_partner = row['delivery_partner'] if 'delivery_partner' in row else None 
                cur.execute("""
                    INSERT INTO mains_delivery (order_id, delivery_address, delivery_date, delivery_status, delivery_partner)
                    VALUES (%s, %s, %s, %s, %s)
                """, (row['order_id'], delivery_address, delivery_date, delivery_status, delivery_partner))

                success_count += 1
                conn.commit()
            except Exception as e:
                logger.error(f"Error processing row {index+1}: {str(e)} Traceback : {traceback.format_exc()}")
                failed_count += 1
                conn.rollback()

        cur.close()
        conn.close()

        logger.info(f"Processed {len(csv_data)} rows. Success: {success_count}, Failed: {failed_count}")
        return {
            'statusCode': 200,
            'body': f"Processed {len(csv_data)} rows. Success: {success_count}, Failed: {failed_count}"
        }

    except Exception as e:
        logger.error(f"General Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"General Error: {str(e)}"
        }

test_event = {
    "csv_url": "https://drive.google.com/file/d/1z7vO3Lx91Z9XwIey9taSAOXO6z1IwPmH/view?usp=sharing"
    # "csv_url": "https://drive.google.com/file/d/19QUU77xinCo56LQV6A0rd6Y_TTCR8_Br/view?usp=sharing" 
    # "csv_url": "https://drive.google.com/file/d/1sfBGgaVLgXLBW4LLdw3oODZszs2J_-b1/view?usp=sharing" 
    # 'csv_url': 'csv/amazon_data_with_unique_columns.csv'
}

# result = lambda_handler(test_event, None) 

'''
Below are some points that need to be improved in the code in general prod scenario:
1. Error Handling and Logging:

- Improved logging: The current logging captures errors but doesn't provide much detail. 
Consider including specific row data (e.g., order ID, error message) in the log to aid troubleshooting.
- Logging failed rows: Instead of just logging the error, consider storing the entire failed row 
(or relevant columns) in a separate table named failed_data_ingestion or similar. This table can include 
columns for the original data and the error message encountered. This will allow for analysis of failures 
and potential retries.

2. Database Interactions:

- Transactions: Wrap the data insertion logic (for loop) in a transaction using conn.begin() and conn.commit(). 
If any insertion fails, the entire transaction can be rolled back using conn.rollback().
This ensures data consistency.
- Batch inserts: For performance optimization, consider using batch inserts instead of inserting each 
row individually. Libraries like psycopg2-binary can be used for efficient data insertion.

3. Security:

- Secret Management: In production, avoid storing database credentials directly in the code.
 Use AWS Secrets Manager to securely store and retrieve credentials. The code can then use the AWS SDK to 
 access the secrets.
'''