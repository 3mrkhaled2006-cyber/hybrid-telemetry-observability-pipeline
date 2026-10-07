output "namespace" {
  value = kubernetes_namespace.telemetry.metadata[0].name
}

output "service_name" {
  value = kubernetes_service.pipeline_service.metadata[0].name
}

output "metrics_port" {
  value = 9102
}

output "health_port" {
  value = 8080
}
