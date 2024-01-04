import sqlite3
from datetime import date, datetime

today = date.today()
formattedDate = today.strftime("%B %d, %Y")

# Stablish connection
conn = sqlite3.connect('pinoybiz-sales/PinoyBiz_Sales.db')

# Create cursor objecy
cursor = conn.cursor()

# Create PinoyBiz_Sales Tables - Customer, Orders, and Transactions
# Customers
cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
               id INTEGER PRIMARY KEY,
               customer_name TEXT NOT NULL
    )
''')

# Products
cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
               id INTEGER PRIMARY KEY,
               product_name TEXT NOT NULL,
               price INTEGER NOT NULL
    )
''')

# Orders
cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
               id INTEGER PRIMARY KEY,
               product_id INTEGER NOT NULL,
               quantity INTEGER NOT NULL,
               order_date DATE NOT NULL
    )
''')

# Transactions
cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
               id INTEGER PRIMARY KEY,
               customer_id INTEGER NOT NULL,
               order_id INTEGER NOT NULL,
               transaction_date DATE NOT NULL
    )
''')

# Load Dummy Data Function
def insertData():
    # Dummy Customers
    cursor.execute('''INSERT INTO customers (customer_name)
                   VALUES
                   ('Arvin Bonggal'),
                   ('Duvall Danganan'),
                   ('Mark Joseph Loma')
                   ''')

    # Dummy Products
    cursor.execute('''INSERT INTO products (product_name, price)
                   VALUES
                   ('Ampalaya', 96.25),
                   ('Sitao', 97.65),
                   ('Pechay', 65.79),
                   ('Squash', 56.42),
                   ('Eggplant', 102.06),
                   ('Tomato', 68.51)
                   ''')
    
    # Dummy Orders
    cursor.execute('''INSERT INTO orders (product_id, quantity, order_date)
                   VALUES
                   (1, 1, 'November 12, 2023'),
                   (2, 1, 'November 12, 2023'),
                   (3, 1, 'November 12, 2023'),
                   (4, 1, 'November 12, 2023'),
                   (5, 1, 'November 12, 2023'),
                   (6, 1, 'November 12, 2023'),
                   (1, 10, 'October 1, 2023'),
                   (2, 20, 'October 1, 2023'),
                   (3, 30, 'October 1, 2023'),
                   (4, 40, 'October 1, 2023'),
                   (5, 50, 'October 1, 2023'),
                   (6, 60, 'October 1, 2023')
                   ''')

    # Dummy Transactions
    cursor.execute('''INSERT INTO transactions (customer_id, order_id, transaction_date)
                   VALUES
                   (1, 1, 'December 12, 2023'),
                   (1, 2, 'December 12, 2023'),
                   (1, 3, 'December 12, 2023'),
                   (1, 4, 'December 12, 2023'),
                   (1, 5, 'December 12, 2023'),
                   (1, 6, 'December 12, 2023'),
                   (2, 7, 'November 1, 2023'),
                   (2, 8, 'November 1, 2023'),
                   (2, 9, 'November 1, 2023'),
                   (2, 10, 'November 1, 2023'),
                   (2, 11, 'November 1, 2023'),
                   (2, 12, 'November 1, 2023')
                   ''')
    
    # Commit Changes
    conn.commit()

# INDEXES
# INDEX order_date
# cursor.execute('CREATE INDEX idx_order_date ON orders(order_date)')

# Call insertData() Function to Load Dummy Data
# insertData()

# Stored Procedure
def calculate_discount(amount, transactionDate):
    d1 = datetime.strptime(transactionDate, "%B %d, %Y")
    d2 = datetime.now()

    if amount > 1000 and (d2 - d1).days <= 30:
        return f'{(amount * 0.9) - ((amount * 0.9)*0.05):.2f}'
    elif amount > 1000:
        return f'{amount*0.9:.2f}'
    else:
        return f'{amount:.2f}'

# Create a SQLite3 function from the Python function
conn.create_function("calculate_discount", 2, calculate_discount)

# Dashboard Query Functions
def customerOrders():
    # LEFT JOIN & SUBQUERY
    cursor.execute('''SELECT customer_name,
                (SELECT SUM(products.price * orders.quantity)
                    FROM
                    transactions
                    LEFT JOIN orders ON transactions.order_id = orders.id
                    LEFT JOIN products ON orders.product_id = products.id
                    WHERE transactions.customer_id = customers.id) AS totalOrderAmount, id
            FROM
            customers
    ''')
    orderDetails = cursor.fetchall()

    # Get Customer with over 5k order amount
    for orders in orderDetails:
        if orders[1] != None and orders[1] > 5000:
            print(f'Customer: {orders[0]}')
            # Get Order Details and apply calculate_discount stored procedure
            cursor.execute('''
                SELECT products.product_name, products.price * orders.quantity, calculate_discount(products.price * orders.quantity, transactions.transaction_date), transactions.transaction_date
                FROM
                transactions
                LEFT JOIN orders ON transactions.order_id = orders.id
                LEFT JOIN products ON orders.product_id = products.id
                WHERE
                transactions.customer_id=?
            ''',(orders[2],))
            customerOrderDetails = cursor.fetchall()
            
            # Order Details Header
            print(f"Order Details:\n{'Product':<20}{'Amount':^20}{'Discounted Amount':^20}{'Transaction Date':>20}")

            # Order Details Content
            for order in customerOrderDetails:
                print(f'{order[0]:<20}{order[1]:^20}{order[2]:^20}{order[3]:>20}')

# Update Order
def updateOrder(order_id, order_quantity):
    # Begin transaction
    conn.execute('BEGIN')

    # Update Quantity
    cursor.execute('UPDATE orders SET quantity=? WHERE id=?',(order_quantity, order_id,))

    # Get Selected Order
    cursor.execute('''SELECT SUM(products.price * ?)
                   FROM
                   transactions
                   LEFT JOIN orders ON transactions.order_id = orders.id
                    LEFT JOIN products ON orders.product_id = products.id
                   WHERE
                   transactions.order_id=?
                   ''',(order_quantity, order_id,))
    orderDetails = cursor.fetchall()

    if list(orderDetails[0])[0] > 10000:
        conn.execute('ROLLBACK')
    else:
        conn.execute('COMMIT')

# Add Order
def addOrder(product_id, quantity, order_date, customer_id):
    cursor.execute('INSERT INTO orders (product_id, quantity, order_date) VALUES (?, ?, ?)''RETURNING id',(product_id, quantity, order_date,))

    # Get New Inserted Order ID
    order = cursor.fetchone()

    cursor.execute('INSERT INTO transactions (customer_id, order_id, transaction_date) VALUES (?, ?, ?)',(customer_id, order[0], order_date,))

    # Create a trigger to update a timestamp on new order insertion
    cursor.execute('''
        CREATE TRIGGER update_timestamp
        AFTER INSERT ON orders
        BEGIN
            UPDATE transactions SET transaction_date = CURRENT_TIMESTAMP WHERE order_id = NEW.order_id;
        END
    ''')

    # Commit Changes
    conn.commit()

# View Customer Orders
customerOrders()

# Update Customer Order
# updateOrder(order_id=1, order_quantity=95)

# Add Customer Order
# addOrder(product_id=3, quantity=2, order_date=formattedDate, customer_id=2)