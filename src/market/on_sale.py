import logging
import urllib.parse
from database.services import insert_on_sales, check_all_records
from database.models import on_sale
import asyncio
import aiohttp

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', filename='market_hash_names.log',
    filemode='a')


async def fetch_data_on_sale(data_on_sales: dict, key, hash_chunk, session):
    tail = ''
    for block in hash_chunk:
        tail += '&list_hash_name[]=' + urllib.parse.quote(block[0])
    url = f"https://market.csgo.com/api/v2/search-list-items-by-hash-name-all/?key={key}{tail}"

    try:
        async with session.get(url) as response:
            status_code = response.status
            data = await response.json()

            for name, items in data['data'].items():
                for item in items:
                    data_on_sales[str(item['id'])] = {"market_hash_name": name,
                                                      "asset": str(item['extra'][
                                                                       'asset']) if 'extra' in item and 'asset' in
                                                                                    item[
                                                                                        'extra'] else None,
                                                      "class_id": str(item['class']),
                                                      "instance_id": str(item['instance']),
                                                      "price": str(int(item['price']) / 100)}

    except aiohttp.client_exceptions.ContentTypeError as ex:
        print(f"[!] Exception - ON_SALE: ConnectError. Status code: {status_code}")
        logging.error(
            f"[!] Exception - ON_SALE - ConnectError. "
            f"Skip {len(hash_chunk)} chunks in ON_SALE stage. Status code: {status_code}")

    except Exception as ex:
        print(f"[!] Exception - ON_SALE: {ex}. Status code: {status_code}")
        logging.error(
            f"[!] Exception - ON_SALE - {ex}. "
            f"Skip {len(hash_chunk)} chunks in ON_SALE stage. Status code: {status_code}")


# ASYNCIO
async def main_on_sale(hash_chunks: list, data_on_sales: dict, loop_on_sale):
    asyncio.set_event_loop(loop_on_sale)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for index, hash_chunk in enumerate(hash_chunks):
            key = hash_chunk[0]
            hash_chunk = hash_chunk[1]
            tasks.append(
                fetch_data_on_sale(data_on_sales=data_on_sales, key=key, hash_chunk=hash_chunk, session=session))
            logging.info(
                f"Submitting chunk {index} with key {key} and {len(hash_chunk)} hash names to executor ON_SALE")

        await asyncio.gather(*tasks)

    logging.info("Start inserted data to ON_SALE DB")
    print("Start inserted data to ON_SALE DB")

    insert_on_sales(data_on_sales)

    logging.info(f"Amount elements on all iterations in ON_SALE stage: {len(data_on_sales)}")
    logging.info(f"Now ON_SALE DB is storing: {check_all_records(on_sale)} records")

    print(f"Amount elements on all iterations in ON_SALE stage: {len(data_on_sales)}")
    print(f"Now ON_SALE DB is storing: {check_all_records(on_sale)} records")

# ASYNC
# async def main_on_sale(hash_chunks: list, data_on_sale: list):
#     tasks = [asyncio.create_task(
#         fetch_data_on_sale(data_on_sale=data_on_sale, key=hash_chunk[0], hash_chunk=hash_chunk[1])) for
#         index, hash_chunk in enumerate(hash_chunks)]
#     await asyncio.gather(*tasks, return_exceptions=True)
#     # for task in asyncio.as_completed(tasks):
#     #     await task
#     print(f"ON_SALE: {len(data_on_sale)}")
