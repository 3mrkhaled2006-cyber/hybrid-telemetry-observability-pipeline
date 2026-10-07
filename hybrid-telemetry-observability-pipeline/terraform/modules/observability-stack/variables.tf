variable "namespace" {
  description = "Target namespace"
  type        = string
}

variable "environment" {
  description = "Target environment"
  type        = string
}

variable "prometheus_chart_version" {
  description = "Helm chart version for Prometheus"
  type        = string
  default     = "25.8.0"
}

variable "grafana_chart_version" {
  description = "Helm chart version for Grafana"
  type        = string
  default     = "7.0.19"
}
