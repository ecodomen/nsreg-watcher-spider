# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
import psycopg2

SQL_CREATE_REGISTRATOR_TABLE = '''
CREATE TABLE IF NOT EXISTS registrator(
    id serial PRIMARY KEY,
    name VARCHAR(255) UNIQUE,
    nic_handle1 text,
    nic_handle2 text,
    city VARCHAR(255),
    website text
);

CREATE TABLE IF NOT EXISTS parse_history (
    id serial PRIMARY KEY,
    date DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS domain(
    id serial PRIMARY KEY,
    name VARCHAR(255) UNIQUE
);

CREATE TABLE IF NOT EXISTS parser(
    id serial PRIMARY KEY,
    CONSTRAINT registrator
        FOREIGN KEY (id)
        REFERENCES registrator (id)
        ON DELETE CASCADE,
    contributor_name VARCHAR(255),
    email VARCHAR(255),
    comment text
);

CREATE TABLE IF NOT EXISTS price(
    id serial PRIMARY KEY,
    CONSTRAINT registrator
        FOREIGN KEY (id)
        REFERENCES registrator (id)
        ON DELETE CASCADE,
    CONSTRAINT domain
        FOREIGN KEY (id)
        REFERENCES domain (id)
        ON DELETE SET NULL,
    CONSTRAINT parse
        FOREIGN KEY (id)
        REFERENCES parse_history (id)
        ON DELETE CASCADE,
    price_reg DECIMAL,
    price_prolong DECIMAL,
    price_change DECIMAL
)
'''


SQL_UPDATE_PRICE = '''
DO
$do$

    DECLARE price_reg DECIMAL;
    DECLARE price_prolong DECIMAL;
    DECLARE price_change DECIMAL;

BEGIN

    SELECT DISTINCT ON (id_registrator) price_reg, price_prolong, price_change
    INTO price_reg, price_prolong, price_change
    FROM price
    WHERE id_registrator = %(registrator)s
    ORDER BY id_registrator, id_parse DESC;

    IF NOT FOUND OR
    price_reg != %(price_reg)s OR price_prolong != %(price_prolong)s OR price_change != %(price_change)s
    THEN
        INSERT INTO price (id_registrator, id_domain, id_parse,
        price_reg, price_prolong, price_change)
        VALUES (%(registrator)s, %(domain)s, %(parse)s,
        %(price_reg)s, %(price_prolong)s, %(price_change)s);
    END IF;

END
$do$
'''


class NsregPipeline:
    def __init__(self):
        hostname = os.environ['HOSTNAME_DB']
        username = os.environ['USERNAME_DB']
        password = os.environ['PASSWORD_DB']  # your password
        database = os.environ['DATABASE_NAME']
        port = os.environ['PORT_DB']
        # Create/Connect to database
        self.connection = psycopg2.connect(
            host=hostname, user=username, password=password, dbname=database, port=port)

        # Create cursor, used to execute commands
        self.cur = self.connection.cursor()

        # Create quotes table if none exists
        self.cur.execute(SQL_CREATE_REGISTRATOR_TABLE)
        self.connection.commit()

    def process_item(self, item, spider):
        price = item.get('price', {
            'price_reg': None,
            'price_prolong': None,
            'price_change': None,
        })
        self.cur.execute(SQL_UPDATE_PRICE, (
            item['name'],
            item.get('nic_handle1', None),
            item.get('nic_handle2', None),
            item.get('city', None),
            item.get('website', None),
            price.get('price_reg', None),
            price.get('price_prolong', None),
            price.get('price_change', None),
            item.get('nic_handle1', None),
            item.get('nic_handle2', None),
            item.get('city', None),
            item.get('website', None),
            price.get('price_reg', None),
            price.get('price_prolong', None),
            price.get('price_change', None),
        ))
        spider.logger.info('Saving item SQL: %s', self.cur.query)

        # self.cur.execute("SELECT * FROM registrator WHERE name = %s", (item['name'],))
        # result = self.cur.fetchone()

        # Execute insert of data into database
        self.connection.commit()
        return item

    def close_spider(self, spider):

        # Close cursor & connection to database
        self.cur.close()
        self.connection.close()
