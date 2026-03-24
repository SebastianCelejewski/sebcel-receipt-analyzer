variable "environment" {
  description = "Deployment environment"
  type = string
  default = "dev"
}

variable "notification_emails" {
  type = list(string)
  default = [
    "Sebastian.Celejewski@wp.pl"
  ]
}

variable "smtp_user" {
  type = string
  sensitive = false
  default = "Sebastian.Celejewski@wp.pl"
}

variable "smtp_password" {
  type      = string
  sensitive = true
  default = "ChangeMe"
}