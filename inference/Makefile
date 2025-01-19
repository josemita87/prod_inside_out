# Build the master Docker image
build-master:
	docker build -t master-index ../sec-feature-pipeline/master-index

# Build the scraper Docker image
build-scraper:
	docker build -t scraper ../sec-feature-pipeline/scraper

# Build the enricher Docker image
build-enricher:
	docker build -t api-enricher ../sec-feature-pipeline/api-enricher

# Stop and remove any existing master container
stop-master:
	-docker rm -f master || true

# Stop and remove any existing scraper container
stop-scraper:
	-docker rm -f scraper || true

# Stop and remove any existing enricher container
stop-enricher:
	-docker rm -f api-enricher || true

# Run the master Docker container
run-infer-master: stop-master build-master
	docker run \
		-it --network redpanda-network \
		--env-file .env-inference-master.env \
		--name master master-index

# Run the scraper Docker container
run-infer-scraper: stop-scraper build-scraper
	docker run \
		-it --network redpanda-network \
		--env-file .env-inference-scraper.env \
		--name scraper scraper

run-infer-enricher: stop-enricher build-enricher
	docker run \
		-it --network redpanda-network \
		--env-file .env-inference-enricher.env \
		--name api-enricher api-enricher


 
#configure the enricher microservice
#Call the prices microservice to update all prices
#Call the target microservice to upate last features
#Prepare inference pipeline using the trained model 