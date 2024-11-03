# Formatting commands
format-master:
	cd master-index && poetry run autopep8 --in-place src/main.py 

format-scraper:
	cd scraper && poetry run autopep8 --in-place src/parser.py src/transaction.py

format-enricher:
	cd api-enricher && poetry run autopep8 --in-place src/main.py src/api_handler.py

format-all: format-master format-scraper format-enricher



#Running dev commands
run-dev-master:
	cd master-index && poetry run python src/main.py

run-dev-scraper:
	cd scraper && poetry run python src/main.py


#Building docker containers
build-master:
	docker build -t master-index master-index/.

build-scraper:
	docker build -t scraper scraper/.

build-enricher:
	docker build -t api-enricher api-enricher/.


#Stopping docker containers
# Stop and remove the 'master-index' container if it exists
stop-master:
	@if [ $$(docker ps -a -q -f name=master-index) ]; then \
		docker stop master-index; \
		docker rm master-index; \
	fi

# Stop and remove the 'scraper' container if it exists
stop-scraper:
	@if [ $$(docker ps -a -q -f name=scraper) ]; then \
		docker stop scraper; \
		docker rm scraper; \
	fi

# Stop and remove the 'api-enricher' container if it exists
stop-enricher:
	@if [ $$(docker ps -a -q -f name=api-enricher) ]; then \
		docker stop api-enricher; \
		docker rm api-enricher; \
	fi



#Running docker containers
run-prod-master: stop-master build-master
	docker run \
	-it --network redpanda-network \
	--env-file master-index/.env \
	--name master-index master-index

run-prod-scraper: stop-scraper build-scraper
	docker run \
	-it --network redpanda-network \
	--env-file scraper/.env \
	--name scraper scraper

run-prod-enricher: stop-enricher build-enricher
	docker run \
	-it --network redpanda-network \
	--env-file api-enricher/.env \
	--name api-enricher api-enricher

run-prod-all: run-prod-master run-prod-scraper run-prod-enricher


#Running container intreactively
run-interactive-enricher: stop-enricher build-enricher
	docker run -it api-enricher /bin/bash
