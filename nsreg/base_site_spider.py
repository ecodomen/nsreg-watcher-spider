import logging
import re

from .items import NsregItem
from .utils_spider import EMPTY_PRICE

# Функция поиска цен в тексте, используя регулярное выражение
def find_price(re_pattern, price):
    price = str(price).strip()
    if price == "бесплатно":
        price = 0
    else:
        # Применяем регулярное выражение к строке
        if m := re.match(re_pattern, price):
            price = m.group(1)
    price = f'{float(price)}'
    logging.info('price = %s', price)

    return price

# Класс, реализующий основные компоненты паука для веб-скрапинга
class BaseSpiderComponent:

    def __init__(self, start_urls=None, allowed_domains=None, site_names=None, regex=None, path=None):
        # Разделение строк по запятым и преобразуем их в списки
        self.start_urls = start_urls.split(',') if start_urls else []
        self.allowed_domains = allowed_domains.split(',') if allowed_domains else []
        self.site_names = site_names.split(',') if site_names else []
        # Сохранение регулярных выражений и пути xpath для дальнейшего использования
        self.regex = regex
        self.path = path

    # Функция для обработки полученных данных
    def parse(self, response):
        # Поиск цены на регистрацию домена на веб-странице
        price_reg = response.xpath(self.path['price_reg']).get()
        price_reg = find_price(self.regex['price_reg'], price_reg)

        # Поиск цены на продление домена на веб-странице
        price_prolong = response.xpath(self.path['price_prolong']).get()
        price_prolong = find_price(self.regex['price_prolong'], price_prolong)

        # Поиск цены на изменение домена на веб-странице
        price_change = response.xpath(self.path['price_change']).get()
        price_change = find_price(self.regex['price_change'], price_change)

        # Получение имя сайта
        site_name = self.site_names[self.start_urls.index(response.url)]

        # Создание элемента данных и заполнение его информацией
        item = NsregItem()
        item['name'] = site_name
        price = item.get('price', EMPTY_PRICE)
        price['price_reg'] = price_reg
        price['price_prolong'] = price_prolong
        price['price_change'] = price_change
        item['price'] = price

        return item
