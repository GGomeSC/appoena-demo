variable "datadog_api_key" {
  description = "Datadog API key used by the provider"
  type        = string
  sensitive   = true
}

variable "datadog_app_key" {
  description = "Datadog application key used by the provider"
  type        = string
  sensitive   = true
}

variable "datadog_api_url" {
  description = "Datadog API URL for the target site"
  type        = string
}
