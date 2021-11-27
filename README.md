# :fire: CrawlTelegram
<p align='center'>
  Powerful Telegram Members Scraping and Adding Toolkit<br>
  <b>Check out <a href='https://github.com/Cryptonian007/Astra.git'> Astra </a></b><br>
  <a href="https://telegram.me/Techmedies_1"><img src="https://img.shields.io/badge/Telegram-Techmedies-green"></a> <a href="https://twitter.com/cryptonian007?lang=en"><img src="https://img.shields.io/badge/FollowOn-Twitter-green"></a>
  </p>


# :small_red_triangle_down: Folder Structure :small_red_triangle:
```      
crawl_telegram
	|---.git/
	|---build/
	    |---.gitkeep
	    |---CrawlTelegram.exe
	|---database_construction/
	|---db/
	    |---data/
	    |---my.cnf/
	    |---sql/
	|---log/     
            |--- log_2021-06-26.log    
            |--- log_2021-06-26.log.1               
	|---sessions/
	    |---.gitkeep
	    |---+849152683xx.session
	|---src/
	    |---entities/
	        |---Account.py
	        |---<any_other_classess>
	    |---UI/
	        |---telegram_ui.py
	        |---telegram.ui
	    |---function_app.py
	    |---telegram_ui.py
		|---TelegramManager.py
		|---DBWorker.py	
		|---ManagerUI.py
	|---docker-compose.yml (có 1 image dựng DB Mýql)
	|---.gitignore
	|---.env  
	|---README.md
	|---requirements.txt     
```

# :small_red_triangle_down: Features :small_red_triangle:

* ADDS IN BULK[by user id, not by username]
* Scrapes and adds to public groups
* Adds 50-60 members on an average
* Works in Windows systems
* You can run unlimited accounts at the same time in order to add members
* CSV files auto-distributer based on number of accounts to use
* Powerful scraping tool that can scrape active members from any public group
* You can add members both by username and by user ID
* Least chances of account ban
* Script auto-joins public group from all accounts for faster adding
* Filters banned accounts and remove them, making things easy
* Genisys can also store unlimited accounts for adding purposes
* Adding scripts launches automatically based on number of accounts to use

# How to use :question:

<b>Notes: 
1. Please run the following commands step-by-step to setup Database + run app.
2. You have to install Docker on your machine before running
3. All these commands below are run  in the root folder
</b>

:cyclone: Install Requirements

`pip install -r requirements.txt`

:cyclone: Deploy Mysql Engine + Setup database

* Deploy Mysql engine

`docker-compose build && docker-compose up`

* Setup database + create needed tables

`python database_construction\setup_database.py`

* Cover Ui to python 

`pyuic5 -x telegram.ui -o telegram_ui.py`
# Note

Sometimes users may not get added at all, this may be because the account is probably limited. Try with another account

# Other documents:
1. DrawIO: 
https://app.diagrams.net/#G1KMy6msNkYajKFBuPvBlLNevlfdEFgquM
