


#Running docker containers for redpanda cluster 
start-redpanda:
	docker-compose -f redpanda.yml up -d
stop-redpanda:
	docker-compose -f redpanda.yml down


inference-sec:
	docker-compose -f docker-compose/system-inference/services-inference.yml \
	--profile sec up
inference-prices:
	docker-compose -f docker-compose/system-inference/services-inference.yml \
	--profile prices up

training-sec:
	docker-compose -f docker-compose/system-training/services-training.yml \
	--profile sec up
training-prices:
	docker-compose -f docker-compose/system-training/services-training.yml \
	--profile prices up
