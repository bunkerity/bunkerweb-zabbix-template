# BunkerWeb by HTTP for Zabbix

This repository contains the official Zabbix template for monitoring [BunkerWeb](https://www.bunkerweb.io/) through the Prometheus exporter PRO plugin.

Zabbix performs one HTTP scrape per interval. Dependent items and discovery rules parse that payload, so you don't need a Zabbix agent on the BunkerWeb instance.

## Requirements

- BunkerWeb PRO with the Monitoring and Prometheus exporter plugins
- Zabbix 7.0 LTS or a later 7.x release
- Network access from the Zabbix server or proxy to the BunkerWeb exporter

If you don't have BunkerWeb PRO yet, you can [test it free for 30 days](https://panel.bunkerweb.io/store/bunkerweb-pro).

## Configure BunkerWeb

Enable both plugins and allow the Zabbix server or proxy to reach the exporter:

```env
USE_MONITORING=yes
USE_PROMETHEUS_EXPORTER=yes
PROMETHEUS_EXPORTER_ALLOW_IP=192.0.2.10/32
```

Replace `192.0.2.10/32` with the address or network of your Zabbix server or proxy. The exporter listens on port `9113` and serves `/metrics` by default. If you changed either setting, update the matching Zabbix macros after importing the template.

You can find the full Prometheus exporter configuration in the [BunkerWeb documentation](https://docs.bunkerweb.io/latest/features/).

## Import the template

1. Download [`template_bunkerweb.yaml`](./template_bunkerweb.yaml).
2. In Zabbix, open **Data collection → Templates → Import** and select the file.
3. Create one host for each BunkerWeb instance.
4. Add an interface whose address points to that instance. Zabbix builds the scrape URL from `{HOST.CONN}`.
5. Link the **BunkerWeb by HTTP** template to the host.

Use one Zabbix host per BunkerWeb instance. The exporter exposes per-instance, in-memory counters and does not aggregate a BunkerWeb cluster.

## Macros

| Macro                              | Default    | Purpose                                                                       |
| ---------------------------------- | ---------- | ----------------------------------------------------------------------------- |
| `{$BUNKERWEB.EXPORTER.SCHEME}`     | `http`     | Scheme used to reach the exporter                                             |
| `{$BUNKERWEB.EXPORTER.PORT}`       | `9113`     | Must match `PROMETHEUS_EXPORTER_PORT`                                         |
| `{$BUNKERWEB.EXPORTER.PATH}`       | `/metrics` | Must match `PROMETHEUS_EXPORTER_URL`                                          |
| `{$BUNKERWEB.EXPORTER.INTERVAL}`   | `1m`       | Scrape interval                                                               |
| `{$BUNKERWEB.SERVICE.MATCHES}`     | `.*`       | Services included in discovery                                                |
| `{$BUNKERWEB.SERVICE.NOT_MATCHES}` | `^$`       | Services excluded from discovery                                              |
| `{$BUNKERWEB.DICT.MATCHES}`        | `.*`       | Shared dictionaries included in discovery                                     |
| `{$BUNKERWEB.DICT.NOT_MATCHES}`    | `^$`       | Shared dictionaries excluded from discovery                                   |
| `{$BUNKERWEB.5XX.WARN}`            | `5`        | Percentage of 5xx responses that raises a warning                             |
| `{$BUNKERWEB.ATTACKS.MAX}`         | `10`       | Blocked requests per second that raises a warning                             |
| `{$BUNKERWEB.SHM.TIMELEFT}`        | `7d`       | Warn when projected shared-dictionary exhaustion is closer than this value    |
| `{$BUNKERWEB.NODATA.TIMEOUT}`      | `5m`       | Time without a successful scrape before Zabbix marks the exporter unreachable |

Override macros on the host when one instance needs different connection details, discovery filters, or alert thresholds.

## What the template monitors

Zabbix collects the BunkerWeb version and availability, connections, requests, attacks, response codes, latency, bandwidth, upstream behavior, cache status, TLS protocol use, metric collection errors, and NGINX shared dictionary data.

Zabbix discovers BunkerWeb services and shared dictionaries, then creates the matching items and triggers. It raises problems for exporter reachability, an uninitialized Monitoring plugin, metric collection errors, sustained server errors, elevated attack rates, failing backends, deprecated TLS versions, and projected shared-dictionary exhaustion.

## Troubleshooting

### Prometheus exporter is unreachable

Check that the instance is running, the port and path macros match the BunkerWeb settings, and `PROMETHEUS_EXPORTER_ALLOW_IP` includes the Zabbix server or proxy address.

### Monitoring plugin is not initialized

Set `USE_MONITORING=yes`. The exporter returns HTTP 503 with an explanation when the Monitoring plugin has not initialized. The template accepts that status so it can report this problem instead of calling the exporter unreachable.

### No services or shared dictionaries appear

Check the `MATCHES` and `NOT_MATCHES` macros on the host. Zabbix includes everything by default.

## License

Bunkerity releases the template and its documentation under the [MIT License](./LICENSE).
