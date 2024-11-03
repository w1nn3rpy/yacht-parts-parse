import pyexcel
from parse import *

get_all_categories_links()  # Получаем ссылки на все подкатегории
get_all_products()  # Получаем список всех товаров
get_product_info()  # Получаем данные о всех товарах

driver.quit()  # Закрываем драйвер

pyexcel.save_as(records=products_data, dest_file_name='products.xlsx')  # Сохраняем результат в xlsx
print('Результат сохранён в файл products.xlsx')