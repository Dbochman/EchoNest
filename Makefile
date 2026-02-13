.PHONY: test-nests test-all test-quick deploy

DEPLOY_HOST = deploy@echone.st
DEPLOY_DIR = /opt/echonest

# Run nest contract tests + regression suite
test-nests:
	./scripts/test_nests.sh

# Run full test suite (all tests including nests)
test-all:
	SKIP_SPOTIFY_PREFETCH=1 python3 -m pytest test/ -v

# Quick: just nest tests, no regression
test-quick:
	SKIP_SPOTIFY_PREFETCH=1 python3 -m pytest test/test_nests.py -v -rx

# Deploy to production: rsync, rebuild containers
deploy:
	rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
		--exclude='oauth_creds' --exclude='local_config.yaml' --exclude='.env' \
		--exclude='venv' --exclude='.venv' \
		. $(DEPLOY_HOST):$(DEPLOY_DIR)/
	ssh $(DEPLOY_HOST) 'cd $(DEPLOY_DIR) && docker compose up -d --build echonest player'
	@echo "Deploy complete."
