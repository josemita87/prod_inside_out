format-master:
	poetry run autopep8 --in-place master-index/src/main.py 
	
format-scraper:
	poetry run autopep8 --in-place scraper/src/parser.py scraper/src/transaction.py


run-dev-master:
	cd master-index && poetry run python src/main.py

run-dev-scraper:
	cd scraper && poetry run python src/main.py



build-master:
	docker build -t master-index master-index/.

build-scraper:
	docker build -t scraper scraper/.

run-prod-master: build-master
	docker run \
	-it --network redpanda-network \
	--env-file master-index/.env \
	--name master-index master-index