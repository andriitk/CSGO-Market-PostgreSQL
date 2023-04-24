import logging
import datetime
import urllib.parse
import asyncio
import aiohttp
from database.services import insert_history, check_all_records
from database.models import history

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', filename='market_hash_names.log',
    filemode='a')


async def fetch_data_history(data_history: dict, key, hash_chunk, session):
    tail = ''
    for block in hash_chunk:
        tail += '&list_hash_name[]=' + urllib.parse.quote(block[0])
    url = f"https://market.csgo.com/api/v2/get-list-items-info?key={key}{tail}"

    try:
        async with session.get(url) as response:
            status_code = response.status
            data = await response.json()

            for name, items in data['data'].items():
                prices = set()
                for block in items['history']:
                    if "." not in str(block[1]):
                        prices.add(f"{block[1]}.0")
                    else:
                        prices.add(str(block[1]))

                data_history[name] = {"time": [
                    str(datetime.datetime.fromtimestamp(
                        int(block[0])))
                    for
                    block in
                    items['history']],
                    "price": list(prices)}

    except aiohttp.client_exceptions.ContentTypeError as ex:
        print(f"[!] Exception - HISTORY: ConnectError. Status code: {status_code}")
        logging.error(
            f"[!] Exception - HISTORY - ConnectError. "
            f"Skip {len(hash_chunk)} chunks in HISTORY stage. Status code: {status_code}")

    except Exception as ex:
        print(f"[!] Exception - HISTORY: {ex}. Status code: {status_code}")
        logging.error(
            f"[!] Exception - HISTORY - {ex}. "
            f"Skip {len(hash_chunk)} chunks in HISTORY stage. Status code: {status_code}")


# ASYNCIO
async def main_on_history(hash_chunks: list, data_history: dict, loop_history):
    asyncio.set_event_loop(loop_history)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for index, hash_chunk in enumerate(hash_chunks):
            key = hash_chunk[0]
            hash_chunk = hash_chunk[1]
            tasks.append(
                fetch_data_history(data_history=data_history, key=key, hash_chunk=hash_chunk, session=session))

            # tasks = [asyncio.create_task(
            #     fetch_data_history(data_history=data_history, key=hash_chunk[0], hash_chunk=hash_chunk[1],
            #                        session=session)) for index, hash_chunk in enumerate(hash_chunks)]

            logging.info(
                f"Submitting chunk {index} with key {key} and {len(hash_chunk)} hash names to executor HISTORY")

        await asyncio.gather(*tasks)

    logging.info("Start inserted data to HISTORY DB")
    print("Start inserted data to HISTORY DB")

    insert_history(data_history)

    logging.info(f"Amount elements on all iterations in HISTORY stage: {len(data_history)}")
    logging.info(f"Now HISTORY DB is storing: {check_all_records(history)} records")

    print(f"Amount elements on all iterations in HISTORY stage: {len(data_history)}")
    print(f"Now HISTORY DB is storing: {check_all_records(history)} records")
    print("--------------------------------------------")

# ASYNC
# async def main_on_history(hash_chunks: list, data_history: list):
#     tasks = [asyncio.create_task(
#         fetch_data_history(data_history=data_history, key=hash_chunk[0], hash_chunk=hash_chunk[1])) for
#         index, hash_chunk in enumerate(hash_chunks)]
#     await asyncio.gather(*tasks, return_exceptions=True)
#     # for task in asyncio.as_completed(tasks):
#     #     await task
#     print(f"HISTORY: {len(data_history)}")
