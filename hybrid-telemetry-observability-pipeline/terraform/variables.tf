variable "environment" {
  description = "Target deployment environment (e.g. dev, staging, prod)"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be one of: dev, staging, production."
  }
}

variable "kubeconfig_path" {
  description = "Path to the local kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

variable "kubeconfig_context" {
  description = "Context within kubeconfig to apply resources"
  type        = string
  default     = null
}

variable "namespace" {
  description = "Target Kubernetes namespace for telemetry pipeline"
  type        = string
  default     = "telemetry-system"
}

variable "telemetry_image" {
  description = "Container image tag for telemetry pipeline"
  type        = string
  default     = "ghcr.io/org/hybrid-telemetry-pipeline:1.0.0"
}

variable "replicas" {
  description = "Desired replica count for telemetry daemon"
  type        = number
  default     = 3

  validation {
    condition     = var.replicas >= 1 && var.replicas <= 20
    error_message = "Replicas must be between 1 and 20."
  }
}

variable "enable_observability_stack" {
  description = "Whether to provision Prometheus and Grafana Helm releases"
  type        = bool
  default     = true
}
