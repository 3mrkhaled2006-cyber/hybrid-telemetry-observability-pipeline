output "namespace" {
  description = "Namespace where telemetry workload is deployed"
  value       = module.k8s_workload.namespace
}

output "service_name" {
  description = "Kubernetes Service name for telemetry exposition"
  value       = module.k8s_workload.service_name
}

output "metrics_port" {
  description = "Port exposing Prometheus metrics"
  value       = module.k8s_workload.metrics_port
}

output "health_port" {
  description = "Port exposing health and readiness probes"
  value       = module.k8s_workload.health_port
}
