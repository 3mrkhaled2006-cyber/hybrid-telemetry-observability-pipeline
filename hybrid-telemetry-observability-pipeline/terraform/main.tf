module "k8s_workload" {
  source = "./modules/k8s-workload"

  namespace       = var.namespace
  environment     = var.environment
  telemetry_image = var.telemetry_image
  replicas        = var.replicas
}

module "observability_stack" {
  count  = var.enable_observability_stack ? 1 : 0
  source = "./modules/observability-stack"

  namespace   = var.namespace
  environment = var.environment
}
