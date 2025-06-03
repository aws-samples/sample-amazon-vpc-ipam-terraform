#==============================================================================
# Sample Terraform Implementation for Hierarchical IPAM on AWS
#
# This code demonstrates how to implement hierarchical IP Address Management
# across multiple AWS regions, business units, and environments.
#
# IMPORTANT: This code is provided as a sample for educational purposes.
# Before using in production, review security configurations and customize
# to meet your organizational requirements.
#==============================================================================

variable "product_name" {
  description = "Product name for the resource being deployed"
  type        = string
}

variable "feature_name" {
  description = "Feature name for the resource being deployed"
  type        = string
}

variable "business_unit" {
  description = "Business Unit for the resource being deployed"
  type        = string
}

variable "environment" {
  description = "Environment for the resource being deployed"
  type        = string
}

variable "optional_tags" {
  description = "Map of any non-required tags to include in the default tags. Will be appended to this module's tag_map output."
  type        = map(string)
  default     = {}
}
