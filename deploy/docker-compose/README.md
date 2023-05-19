
# Deploy via docker-compose

## Prerequisites

The ansible playbook that starts up the containers checks if the following tools
can be found:

- [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#id13) using `pip`
- [clickhouse-client](https://clickhouse.com/docs/en/install/)
- [docker-compose v2](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#id13)
- [poetry](https://python-poetry.org/), in case you manually want to run each
a scrapy spider individually

## Deploy

To deploy the containers run `ansible-playbook deploy/docker-compose/ansible/pipeline.up.yml`.
Docker compose uses `--force-recreate` when creating the containers. 
This will cause all the Grafana dashboards to be lost, and
they will need to be recreated.

The ansible playbook will create the following containers:

| Container Name |                               Role                                |                                                                                                                                                                                                                                          Accessibility |
|----------------|:-----------------------------------------------------------------:|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|
| zookeeper      |           Tracks Kafka's state since I don't use Kraft            |                                                                                                                                                                                                                      I chose to not expose port `2181` |
| kafka          |        Stores the scraped json data in the `flights` topic        |                                                                                                                                                                                                                        Exposes ports `9092` and `9093` |
| scraper        | Runs all the scrapy spiders. The triggering happens using crontab |                                                                                                                                                                                                                                Doesn't expose anything |
| clickhouse     |                          Stores the data                          | <table>  <thead>  <tr>  <th></th>  <th>Native clickhouse-client</th>  <th>HTTP interface</th>  </tr>  </thead>  <tbody>  <tr>  <td> localhost_port:container_port </td>  <td>`19000`:`9000`</td>  <td>`18123`:`8123`</td>  </tr>    </tbody>  </table> |
| grafana        |                    Visualise the scraped data                     |                                                                                                                                                                                                                      Exposes localhost's `3000`:`3000` |

Containers are isolated in separate networks to leave only containers that need to communicate to each other
in the same network. For example, since the `scrapers` container needs to communicate only to `kafka` container and
nothing more, both `scrapers` and `kafka` containers are part of the `scraper-kafka` network.

## Cleanup

To remove the containers run `ansible-playbook deploy/docker-compose/ansible/pipeline.up.yml`.
This will also remove additional volumes created.
