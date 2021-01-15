# sonic-tool installment environment

SONIC_TOOLS := sonic-env sonic-push-dockers sonic-registry-login
INSTALL_DIR := /usr/bin/

all :

install :
	$(foreach tool,$(SONIC_TOOLS),cp $(tool) $(INSTALL_DIR);)

uninstall :
	$(foreach tool,$(SONIC_TOOLS),rm $(INSTALL_DIR)/$(tool);)
