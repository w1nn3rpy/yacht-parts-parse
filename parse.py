import re

from bs4 import BeautifulSoup
import requests
from selenium import webdriver

site = 'https://yacht-parts.ru/'
catalog_url = site + 'catalog/'
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
}

products_data = []

### Можно было бы добавить time.sleep() в каждую функцию, но сайт вроде не блокирует, поэтому я не стал
def get_all_categories_links():
    """
    Функция выполняет GET запрос к каталогу товаров сайта yacht-parts.ru
    Если запрос успешен - создаётся объект BeautifulSoup
    для обработки html текста страницы
    Функция ищет все подкаталоги: проходится циклом по всем найденным строкам с тегом <а> и наличием ссылок
    Если ссылка начинается с /catalog/ и имеет - добавляется в заранее созданное множество, для исключения
    дублирования
    По заверешнию цикла ссылки из множества сохраняются в файл category_links.txt
    """
    category_regex = re.compile(r'^/catalog/[^/]+/[^/]+/$')

    response = requests.get(url=catalog_url, headers=headers)

    if response.status_code == 200:

        soup = BeautifulSoup(response.text, 'html.parser')

        last_level_categories = set(
            site.rstrip('/') + link['href']
            for link in soup.find_all('a', href=True)
            if category_regex.match(link['href'])
        )
        print('Поиск категорий завершён')
        with open('category_links.txt', 'w') as result:
            for links in last_level_categories:
                result.write(links + '\n')
            print('Результат сохранён в файл "category_links.txt"')

    else:
        print(f'Ошибка {response.status_code}')


def get_all_products():
    """
    Функция проходит по каждой ссылке в файле category_links.txt и делает к ней GET запрос.
    Если запрос успешен - создаётся объект BeautifulSoup для обработки html текста страницы
    и производится поиск ссылок с тегом <а>.
    При совпадении формата ссылки с regex паттерном - она добавляется в множество.
    По окончанию цикла все ссылки на товары сохраняются в файл prod_res.txt
    """
    with open('category_links.txt', 'r') as category_link_list:

        products_regexp = re.compile(r'^/catalog/[^/]+/[^/]+/[^/]+/$')
        products_links = set()
        for category in category_link_list:
            print(f'Обработка {category}')
            response = requests.get(url=category.strip(), headers=headers)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                for link in soup.find_all('a', href=True):
                    if re.match(products_regexp, link['href']):
                        full_link = site.rstrip('/') + link['href']
                        products_links.add(full_link)

        with open('prod_res.txt', 'w') as prod_res:
            for links in products_links:
                prod_res.write(links + '\n')
            print('Обработка завершена! Результат сохранён в файл "prod_res.txt"')


driver = webdriver.Chrome()
# У меня chromedriver установлен через brew,
# поэтому у меня работает без явного указания пути

def get_product_info():
    """
    Здесь уже задействуется chromedriver с selenium для получения изображений товара
    Функция проходит по каждой ссылке файла prod_res.txt и делает GET запрос.
    Создаётся объект BeautifulSoup для обработки html текста страницы.
    Для каждого элемента производится поиск по нужным тегам и аргументам.
    Результат сохраняется в список словарей products_data,
    который затем сохраняется в формате xlsx методом pyexcel.save_as
    """
    with open('prod_res.txt', 'r') as products:

        for product in products:
            print(f'Обработка\n{product}')
            driver.get(product)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            title = soup.find('h1', id='pagetitle').text.strip()

            meta_tag = soup.find('meta', itemprop='position', content='3')
            category = meta_tag.find_previous('span', itemprop='name').text

            article = soup.find('span', class_='value').text.strip()

            brand = 'Неизвестно'
            brand_block = soup.find('div', class_='brand iblock')
            if brand_block:
                brand = brand_block.find('img', title=True)['title']

            price = soup.find('div', class_='price').text.strip()

            description = 'Нет описания'
            description_string = soup.find('div', class_='preview_text')
            if description_string:
                description = description_string.text.strip()

            photos = [site.rstrip('/') + li['data-big'] for li in soup.find_all('li', {'data-big': True})]

            ### Код для товаров с одной фотографией
            one_photo_block = soup.find('li', id='mphoto-0')
            if one_photo_block:
                one_photo = one_photo_block.find('a', href=True)
                if one_photo:
                    photos.append(site.rstrip('/') + one_photo['href'])

            result = {
                '1. Category': category,
                '2. Article': article,
                '3. Brand': brand,
                '4. Title': title,
                '5. Price': price if price else 'Под заказ',
                '6. Description': description,
                '7. Photos': ", ".join(photos if True else one_photo)
            }
            products_data.append(result)


if __name__ == '__main__':
    get_all_categories_links() # Получаем ссылки на все подкатегории
    get_all_products() # Получаем список всех товаров

    get_product_info() # Получаем данные о всех товарах
    driver.quit() # Закрываем драйвер

