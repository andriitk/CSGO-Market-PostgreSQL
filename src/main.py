from market.on_sale import main_on_sale
from market.history import main_on_history
from database.services import insert_market_hash_names, compare_data
import multiprocessing as mp
import asyncio
import time

import logging

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', filename='market_hash_names.log',
    filemode='a')

# Start time of start project
START = time.time()

# List of keys for request
with open("keys.txt", "r") as keys_file:
    KEYS = keys_file.read().splitlines()

# Size chunk hashes
CHUNK_SIZE = 50

# List for storing chunk hashes and sublist
HASH_CHUNKS = []

# Index current key in list
KEY_INDEX = 0

# Create global variable dictionary fot iteration and add to DB through one session
DATA_SALES = dict()
DATA_HISTORY = dict()

# Run func for get data=market_hash_names from redis
market_hash_names = asyncio.run(insert_market_hash_names())
market_hash_names = market_hash_names['market_hash_names']

# Iterate and create HASH_CHUNKS with the list into sublists of 50 item
for i in range(0, len(market_hash_names), CHUNK_SIZE):
    key = KEYS[KEY_INDEX]
    hash_chunk = list(market_hash_names.items())[i:i + CHUNK_SIZE]
    HASH_CHUNKS.append((key, hash_chunk))
    KEY_INDEX = (KEY_INDEX + 1) % len(KEYS)

loop_on_sale = asyncio.new_event_loop()
loop_history = asyncio.new_event_loop()


# Define func for process #1 Stage ON_SALE
def run_main_on_sale():
    logging.info('Starting process ON_SALE')
    loop_on_sale.run_until_complete(
        main_on_sale(hash_chunks=HASH_CHUNKS, data_on_sales=DATA_SALES, loop_on_sale=loop_on_sale))
    logging.info('Finished process ON_SALE')


# Define func for process #2 Stage HISTORY
def run_main_on_history():
    logging.info('Starting process HISTORY')
    loop_history.run_until_complete(
        main_on_history(hash_chunks=HASH_CHUNKS, data_history=DATA_HISTORY, loop_history=loop_history))
    logging.info('Finished process HISTORY')


# Entrypoint of program
if __name__ == '__main__':
    logging.info('Starting program...')
    logging.info(f'From API got {len(market_hash_names)} market_hash_names')

    print("\n\n=============================================")
    print("-------------------1 STAGE-----------------------")
    print(f"From API got {len(market_hash_names)} market_hash_names")
    process_one = mp.Process(target=run_main_on_sale)
    process_two = mp.Process(target=run_main_on_history)

    print("--------------------------------------------------")
    print("Start process ON_SALE and HISTORY in different parallel process")
    logging.info('Start process ON_SALE and HISTORY in different parallel process')
    process_one.start()
    process_two.start()

    print("\n\n-------------------2 and 3 STAGE-------------------\n")

    process_one.join()
    process_two.join()

    loop_on_sale.close()
    loop_history.close()

    logging.info('Starting process СOMPARE DATA')
    compare_data()
    logging.info('Finished process СOMPARE DATA')

    elapsed_script_time = time.time() - START
    logging.info('Total time elapsed: %s seconds', elapsed_script_time)
    print("____________________________________________________")
    print("Total time elapsed:", elapsed_script_time, "seconds")
    print("====================================================\n")
