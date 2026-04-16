ODOO_BIN     := /home/lucadifiori/odoo/odoo-bin
ODOO_ADDONS  := /home/lucadifiori/odoo/addons
MODULE_PATH  := /home/lucadifiori/Desktop/odoo-project-management
VENV         := $(MODULE_PATH)/venv/bin/python
DB           := odoo_dev
PORT         := 8069
LOG_LEVEL    := info
GREEN_BOLD   := \033[1;32m
RED_BOLD     := \033[1;31m
RESET_COLOR  := \033[0m

# Start Odoo with hot-reload enabled (recommended during development)
run:
	@echo "[INFO] Starting Odoo server..."
	@echo "[INFO] Odoo should be reachable at: http://localhost:$(PORT)"
	@echo "[INFO] Press Ctrl+C to stop the server."
	@$(VENV) $(ODOO_BIN) \
		--addons-path=$(ODOO_ADDONS),$(MODULE_PATH) \
		--dev=all \
		-d $(DB) \
		--http-port=$(PORT) \
		--logfile=/dev/stdout \
		--log-level=$(LOG_LEVEL)

# Force reinstall of the module (use after adding new models, views, or security rules)
update:
	@$(VENV) $(ODOO_BIN) \
		--addons-path=$(ODOO_ADDONS),$(MODULE_PATH) \
		--dev=all \
		-d $(DB) \
		--http-port=$(PORT) \
		-u project_advanced \
		--stop-after-init \
		--logfile=/dev/stdout \
		--log-level=$(LOG_LEVEL); \
	status=$$?; \
	if [ $$status -eq 0 ]; then \
		printf '%b\n' "$(GREEN_BOLD)[OK] Update completed successfully.$(RESET_COLOR)"; \
	else \
		printf '%b\n' "$(RED_BOLD)[ERROR] Update failed (exit code: $$status).$(RESET_COLOR)"; \
	fi; \
	exit $$status

# Install the module for the first time on a fresh database
install:
	@$(VENV) $(ODOO_BIN) \
		--addons-path=$(ODOO_ADDONS),$(MODULE_PATH) \
		--dev=all \
		-d $(DB) \
		--http-port=$(PORT) \
		-i project_advanced \
		--stop-after-init \
		--logfile=/dev/stdout \
		--log-level=$(LOG_LEVEL); \
	status=$$?; \
	if [ $$status -eq 0 ]; then \
		printf '%b\n' "$(GREEN_BOLD)[OK] Installation completed successfully.$(RESET_COLOR)"; \
	else \
		printf '%b\n' "$(RED_BOLD)[ERROR] Installation failed (exit code: $$status).$(RESET_COLOR)"; \
	fi; \
	exit $$status

# Open an interactive Odoo shell (useful for debugging and testing)
shell:
	@$(VENV) $(ODOO_BIN) shell \
		--addons-path=$(ODOO_ADDONS),$(MODULE_PATH) \
		-d $(DB) \
		--http-port=$(PORT) \
		--logfile=/dev/null

.PHONY: run update install shell
