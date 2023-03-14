
# Prerequisites

The ansible playbook that starts up the containers checks if the following tools
can be found:

- Ansible: [guide](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#id13) using `pip`
- clickhouse-client: [guide](https://clickhouse.com/docs/en/install/)
- docker compose v2: [guide](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#id13)

# Installation

To deploy the containers run `ansible-playbook deploy/docker-compose/ansible/pipeline.up.yml`.
Docker compose uses `--force-recreate` when creating the containers. This will cause all the Grafana
dashboards to be lost and they will need to be recreated.

# Uninstallation

To remove the containers run `ansible-playbook deploy/docker-compose/ansible/pipeline.up.yml`.
This will remove additional volumes created.

# Architecture
