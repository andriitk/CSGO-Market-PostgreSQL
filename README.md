# CSGO-Market-v.2 PostgreSQL
1. Clone project in your directory - <code>git clone https://github.com/andriitk/CSGO-Market-v.2.git</code> <br>
2. Install Docker - <code>apt install docker.io</code> <br>
3. Change directory on CSGO-Market-v.2 - <code>cd CSGO-Market-v.2</code> <br>
3. Create file <code>.env</code> in the current directory with such variables:<br>
<code>POSTGRES_HOST=postgres_db</code><br>
<code>POSTGRES_PORT=1224</code><br>
<code>POSTGRES_DB=market_csgo</code><br>
<code>POSTGRES_USER=csgo</code><br>
<code>POSTGRES_PASSWORD=<your_pass></code><br>
<code>REDIS_HOST=csgo_redis_db</code><br>
<code>REDIS_PORT=6398</code> <br>
4. Run the command to build docker image and start program- <code>docker-compose up --build</code> <br>
<br>
All logs you can see in the terminal.
