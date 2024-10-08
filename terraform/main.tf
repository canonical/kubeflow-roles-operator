resource "juju_application" "kubeflow_roles" {
  charm {
    name     = "kubeflow-roles"
    channel  = var.channel
    revision = var.revision
  }
  config    = var.config
  model     = var.model_name
  name      = var.app_name
  resources = var.resources
  trust     = true
  units     = 1
}
