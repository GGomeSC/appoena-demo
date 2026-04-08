locals {
  software_catalog_services = toset([
    "appoena-demo-frontend",
    "appoena-demo-api",
    "appoena-demo-loadgen",
    "appoena-demo-worker",
  ])

  service_dependencies = {
    "appoena-demo-frontend" = []
    "appoena-demo-api" = [
      "queue:items-events",
    ]
    "appoena-demo-loadgen" = []
    "appoena-demo-worker" = [
      "queue:items-events",
    ]
  }
}
