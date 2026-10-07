output "prometheus_release_name" {
  value = helm_release.prometheus.name
}

output "grafana_release_name" {
  value = helm_release.grafana.name
}
