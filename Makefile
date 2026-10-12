# Shortcuts for the Dulces Delicias Odoo demo.  Run `make` to list them.
DB      ?= dulces_delicias
MODULE  ?= dulces_delicias
COMPOSE ?= docker compose

.DEFAULT_GOAL := help
.PHONY: help setup start stop install demo update reset logs shell clean

help:
	@grep -E '^[a-z]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  make %-8s %s\n", $$1, $$2}'

setup: ## Download the OCA helpdesk modules (git submodule)
	git submodule update --init

start: setup ## Start Odoo, PostgreSQL and Mailpit in the background
	$(COMPOSE) up -d

stop: ## Stop all containers (your data is kept)
	$(COMPOSE) stop

install: setup ## Create the database and install the case-study configuration
	$(COMPOSE) up -d db mailpit
	$(COMPOSE) stop odoo
	$(COMPOSE) run --rm odoo odoo -d $(DB) -i $(MODULE) --stop-after-init
	$(COMPOSE) run --rm -T odoo odoo shell -d $(DB) --no-http --log-level=warn < scripts/install_spanish.py
	$(COMPOSE) up -d odoo
	@echo ""
	@echo "  Odoo is ready:   http://localhost:8069   (user: admin  password: admin)"
	@echo "  Sent emails:     http://localhost:8025"

demo: ## Simulate the business operations (purchases, production, sales, ...)
	$(COMPOSE) exec -T odoo odoo shell -d $(DB) --no-http --log-level=warn < scripts/demo_flow.py

update: ## Reload the module after editing its files
	$(COMPOSE) stop odoo
	$(COMPOSE) run --rm odoo odoo -d $(DB) -u $(MODULE) --stop-after-init
	$(COMPOSE) up -d odoo

reset: ## DELETE the database and install everything again from scratch
	$(COMPOSE) up -d db
	$(COMPOSE) stop odoo
	$(COMPOSE) exec db dropdb -U odoo --if-exists --force $(DB)
	$(COMPOSE) run --rm --entrypoint "" odoo rm -rf /var/lib/odoo/filestore/$(DB)
	$(MAKE) install

logs: ## Follow the Odoo server log (Ctrl+C to quit)
	$(COMPOSE) logs -f odoo

shell: ## Open an interactive Odoo Python shell to play with the ORM
	$(COMPOSE) exec odoo odoo shell -d $(DB) --no-http

clean: ## Remove the containers AND all the data volumes
	$(COMPOSE) down -v
