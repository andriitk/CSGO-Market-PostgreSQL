from database.models import on_sale, history, fourth_stage
from database.db import get_session
from sqlalchemy import select, insert, exists, update
from database.redis import add_data_to_redis, get_market_hash_names
import httpx
import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', filename='market_hash_names.log',
    filemode='a')


# Func for insert of add market hash names ro redis DB
async def insert_market_hash_names():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.steamapis.com/market/items/730?api_key=r39OfExGTYD64Bf8MGntG8oaJgQ&format=comact", timeout=30)
        data = response.json()

    # Check for data in stock if not then insert else extend
    market_hash_names = await get_market_hash_names(table='market_hash_names', db=0)

    if not market_hash_names:
        market_hash_names = {"created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                             'market_hash_names': {}}
        for key, value in data.items():
            market_hash_names['market_hash_names'][key] = str(value)
        await add_data_to_redis(table='market_hash_names', data=market_hash_names, db=0)
    else:
        for key, value in data.items():
            market_hash_names['market_hash_names'][key] = value

    return market_hash_names


# Func for insert data to ON_SALE table according to logic
def insert_on_sales(data: dict):
    with get_session() as session:
        market_ids = {result.market_id for result in session.query(on_sale.c.market_id)}
        if market_ids:
            diff_keys = market_ids - set(data.keys())
            not_founds = 0
            need_checks = 0
            for key in diff_keys:
                query = session.query(on_sale).filter(on_sale.c.market_id == key).first()
                time_db = query.created_at.timestamp()
                time_now = datetime.datetime.now().timestamp()

                if time_now - time_db > 3600:
                    stmt = update(on_sale).where(on_sale.c.market_id == key).values(status="not_found",
                                                                                    created_at=datetime.datetime.now())
                    not_founds += 1
                else:
                    stmt = update(on_sale).where(on_sale.c.market_id == key).values(status="need_check",
                                                                                    created_at=datetime.datetime.now())
                    need_checks += 1
                session.execute(stmt)

            if not_founds:
                logging.info(f"{not_founds} elements got 'not_found' status in ON_SALE DB.")
                print(f"{not_founds} elements got 'not_found' status in ON_SALE DB\n")
            if need_checks:
                logging.info(f"{need_checks} elements got 'need_check' status in ON_SALE DB.")
                print(f"{need_checks} elements got 'need_check' status in ON_SALE DB\n")

        for key, value in data.items():
            exists_query = session.query(on_sale).filter(on_sale.c.market_id == key).first()
            on_sale_status = 0

            if exists_query:
                status = exists_query.status

                if status == "not_found":
                    stmt_1 = update(on_sale).where(on_sale.c.market_id == exists_query.market_id).values(
                        asset=value['asset'],
                        price=value['price'],
                        created_at=datetime.datetime.now(),
                        status="on_sale"
                    )
                    on_sale_status += 1
                else:
                    stmt_1 = update(on_sale).where(on_sale.c.market_id == exists_query.market_id).values(
                        created_at=datetime.datetime.now(),
                        asset=value['asset'],
                        price=value['price'],
                    )
                    logging.info(f"Update existing record in the ON_SALE DB with market_id '{exists_query.market_id}'.")
            else:
                stmt_1 = insert(on_sale).values(market_id=key,
                                                market_hash_name=value['market_hash_name'],
                                                asset=value['asset'],
                                                class_id=value['class_id'],
                                                instance_id=value['instance_id'],
                                                price=value['price'])
                logging.info(f"Insert new record to ON_SALE DB '{value['market_hash_name']} : {key}'.")
            session.execute(stmt_1)

            if on_sale_status:
                logging.info(f"{on_sale_status} elements got 'on_sale' status in ON_SALE DB.")


# Func for insert data to HISTORY
def insert_history(data: dict):
    with get_session() as session:
        market_hash_names = {result.market_hash_name for result in session.query(history.c.market_hash_name)}
        if market_hash_names:
            diff_keys = market_hash_names - set(data.keys())

            not_founds = 0
            for key in diff_keys:
                query = session.query(history).filter(history.c.market_hash_name == key).first()
                time_db = query.created_at.timestamp()
                time_now = datetime.datetime.now().timestamp()

                if time_now - time_db > 3600:
                    stmt = update(history).where(history.c.market_hash_name == key).values(status="not_found",
                                                                                           created_at=datetime.datetime.now())
                    not_founds += 1
                    session.execute(stmt)

            if not_founds:
                logging.info(f"{not_founds} elements got 'not_found' status in HISTORY DB.")
                print(f"{not_founds} elements got 'not_found' status in HISTORY DB\n")

        for key, value in data.items():
            exists_query = session.query(history).filter(history.c.market_hash_name == key).first()

            if not exists_query:
                stmt_1 = insert(history).values(market_hash_name=key,
                                                time=value['time'],
                                                price=value['price'])
                logging.info(f"Insert new record to HISTORY DB '{key}'.")
            else:
                prices = exists_query.price
                times = exists_query.time

                stmt_1 = update(history).where(history.c.market_hash_name == key).values(
                    price=list(set(prices) | set(value['price'])),
                    time=list(set(times) | set(value['time'])),
                    created_at=datetime.datetime.now())
                logging.info(f"Update existing record in the HISTORY DB with name '{key}'.")

            session.execute(stmt_1)


# Get count records in table
def check_all_records(table):
    with get_session() as session:
        results = session.query(table).count()
        return results


# Func for compare tables on 4 Stage
def compare_data():
    print("\n\n-------------------4 STAGE---------------------")

    with get_session() as session:
        count = 0
        data_from_on_sale = session.query(on_sale.c.market_id, on_sale.c.market_hash_name, on_sale.c.status,
                                          on_sale.c.price, on_sale.c.asset, on_sale.c.class_id,
                                          on_sale.c.instance_id).all()
        data_from_history = session.query(history.c.market_hash_name, history.c.status,
                                          history.c.price).all()

        dict_on_sale = {(i[1], i[2], i[3]): (i[0], i[4], i[5], i[6]) for i in data_from_on_sale}

        data_history = {(j[0], j[1], i) for j in data_from_history for i in j[2]}

        list_of_sales = [i for i in data_history if i in dict_on_sale.keys()]

        for i in list_of_sales:
            if not session.query(fourth_stage).filter(fourth_stage.c.market_id == dict_on_sale[i][0]).first():
                stmt_1 = insert(fourth_stage).values(market_hash_name=i[0],
                                                     price=i[2],
                                                     market_id=dict_on_sale[i][0],
                                                     asset=dict_on_sale[i][1],
                                                     class_id=dict_on_sale[i][2],
                                                     instance_id=dict_on_sale[i][3])
                session.execute(stmt_1)
                count += 1
                logging.info(f"[+] Found match element with name: '{i[0]}'; price: {i[2]}.")
                print(f"[+] Found match element with name: '{i[0]}'; price: {i[2]}.")

        if count:
            logging.info(f"Found {count} elements will be on sales. Relevant column added to History table.")
            print(
                f"\n[!] Found {count} elements will be on sales. Relevant column added to History table.\n")
        else:
            logging.info("Not found matching elements. Stage 4 finished without changes.")
            print("[-] Not found matching elements. Stage 4 finished without changes.\n")
