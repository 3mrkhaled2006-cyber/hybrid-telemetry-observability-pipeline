resource "kubernetes_namespace" "telemetry" {
  metadata {
    name = var.namespace
    labels = {
      "app.kubernetes.io/part-of"              = "hybrid-telemetry-pipeline"
      "pod-security.kubernetes.io/enforce"     = "restricted"
      "pod-security.kubernetes.io/audit"       = "restricted"
      "pod-security.kubernetes.io/warn"        = "restricted"
    }
  }
}

resource "kubernetes_config_map" "pipeline_config" {
  metadata {
    name      = "telemetry-pipeline-config"
    namespace = kubernetes_namespace.telemetry.metadata[0].name
  }

  data = {
    PIPELINE_ENVIRONMENT       = var.environment
    PIPELINE_LOG_LEVEL         = "INFO"
    PIPELINE_SAMPLING_RATE_HZ  = "100.0"
    PIPELINE_WINDOW_SIZE       = "128"
    PIPELINE_NUM_CHANNELS      = "4"
    PIPELINE_INJECT_ANOMALIES  = "true"
    PIPELINE_ANOMALY_PROBABILITY = "0.03"
    PIPELINE_HEALTH_PORT       = "8080"
    PIPELINE_METRICS_PORT      = "9102"
  }
}

resource "kubernetes_deployment" "pipeline" {
  metadata {
    name      = "hybrid-telemetry-pipeline"
    namespace = kubernetes_namespace.telemetry.metadata[0].name
    labels = {
      "app.kubernetes.io/name"    = "hybrid-telemetry-pipeline"
      "app.kubernetes.io/part-of" = "telemetry-observability"
    }
  }

  spec {
    replicas = var.replicas

    selector {
      match_labels = {
        "app.kubernetes.io/name" = "hybrid-telemetry-pipeline"
      }
    }

    template {
      metadata {
        labels = {
          "app.kubernetes.io/name" = "hybrid-telemetry-pipeline"
        }
        annotations = {
          "prometheus.io/scrape" = "true"
          "prometheus.io/port"   = "9102"
          "prometheus.io/path"   = "/metrics"
        }
      }

      spec {
        termination_grace_period_seconds = 30

        security_context {
          run_as_non_root = true
          run_as_user     = 10001
          run_as_group    = 10001
          fs_group        = 10001
          seccomp_profile {
            type = "RuntimeDefault"
          }
        }

        container {
          name  = "telemetry-pipeline"
          image = var.telemetry_image

          env_from {
            config_map_ref {
              name = kubernetes_config_map.pipeline_config.metadata[0].name
            }
          }

          port {
            name           = "health"
            container_port = 8080
          }

          port {
            name           = "metrics"
            container_port = 9102
          }

          security_context {
            allow_privilege_escalation = false
            read_only_root_filesystem  = true
            capabilities {
              drop = ["ALL"]
            }
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }
            limits = {
              cpu    = "500m"
              memory = "384Mi"
            }
          }

          liveness_probe {
            http_get {
              path = "/healthz"
              port = "health"
            }
            period_seconds    = 10
            timeout_seconds   = 2
            failure_threshold = 3
          }

          readiness_probe {
            http_get {
              path = "/readyz"
              port = "health"
            }
            period_seconds    = 5
            timeout_seconds   = 2
            failure_threshold = 2
          }

          volume_mount {
            name       = "tmp-volume"
            mount_path = "/tmp"
          }
        }

        volume {
          name = "tmp-volume"
          empty_dir {
            medium     = "Memory"
            size_limit = "64Mi"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "pipeline_service" {
  metadata {
    name      = "hybrid-telemetry-pipeline"
    namespace = kubernetes_namespace.telemetry.metadata[0].name
    labels = {
      "app.kubernetes.io/name" = "hybrid-telemetry-pipeline"
      "prometheus.io/scrape"  = "true"
    }
  }

  spec {
    type = "ClusterIP"
    selector = {
      "app.kubernetes.io/name" = "hybrid-telemetry-pipeline"
    }

    port {
      name        = "health"
      port        = 8080
      target_port = "health"
    }

    port {
      name        = "metrics"
      port        = 9102
      target_port = "metrics"
    }
  }
}
