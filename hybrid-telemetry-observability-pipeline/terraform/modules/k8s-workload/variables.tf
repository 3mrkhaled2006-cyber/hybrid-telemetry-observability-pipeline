variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
}

variable "environment" {
  description = "Target environment"
  type        = string
}

variable "telemetry_image" {
  description = "Docker image for telemetry pipeline"
  type        = string
}

variable "replicas" {
  description = "Number of replicas"
  type        = number
}
