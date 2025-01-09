


build-training:
	docker build -t training .


stop-training:
	@if [ $$(docker ps -a -q -f name=training) ]; then \
		docker stop training; \
		docker rm training; \
	fi

#Running docker containers for sec-4 pipeline

run-prod-training: stop-training build-training
	docker run -it --network redpanda-network \
	--env-file .env \
	--env-file .credentials.env \
	--name training \
	-v /Users/calcatscubedos.l./Desktop/prod_inside_out/training/src:/app/src \
	training

