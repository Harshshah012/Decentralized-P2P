.PHONY: run clean stop

run:
	python3 deploy_peers.py

clean: stop
	python3 cleanup.py

stop:
	@echo "Stopping all peer processes..."
	-pkill -f "python3.*Test1.py"
	@echo "Cleaned up all peer processes"